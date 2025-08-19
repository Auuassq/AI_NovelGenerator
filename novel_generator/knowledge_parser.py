# novel_generator/knowledge_parser.py
# -*- coding: utf-8 -*-
"""
知识库智能解析模块
从导入的知识库文档中提取世界观、角色、大纲等小说核心要素
"""
import os
import json
import logging
import traceback
import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Any, Callable
from dataclasses import asdict
import jieba

from novel_generator.common import invoke_with_cleaning
from novel_generator.vectorstore_utils import load_vector_store
from llm_adapters import create_llm_adapter
from utils import read_file, save_string_to_txt

# 关闭jieba的DEBUG模式，避免输出详细日志
jieba.setLogLevel(20)


class KnowledgeParser:
    """
    知识库解析器核心类
    负责从知识库文档中智能提取结构化的小说要素
    """
    
    def __init__(self, 
                 llm_interface_format: str,
                 llm_api_key: str,
                 llm_base_url: str,
                 llm_model: str,
                 embedding_adapter=None,
                 filepath: str = "",
                 temperature: float = 0.7,
                 max_tokens: int = 4096,
                 timeout: int = 600,
                 max_concurrent_requests: int = 200):
        """
        初始化知识解析器
        
        Args:
            llm_interface_format: LLM接口格式
            llm_api_key: LLM API密钥  
            llm_base_url: LLM基础URL
            llm_model: LLM模型名称
            embedding_adapter: 嵌入模型适配器
            filepath: 项目文件路径
            temperature: 生成温度
            max_tokens: 最大令牌数
            timeout: 超时时间
            max_concurrent_requests: 最大并发请求数（默认5）
        """
        self.llm_adapter = create_llm_adapter(
            interface_format=llm_interface_format,
            base_url=llm_base_url,
            model_name=llm_model,
            api_key=llm_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        self.embedding_adapter = embedding_adapter
        self.filepath = filepath
        self.vector_store = None
        self.max_concurrent_requests = max_concurrent_requests
        
        # 如果提供了embedding适配器，尝试加载向量存储
        if self.embedding_adapter and self.filepath:
            self.vector_store = load_vector_store(self.embedding_adapter, self.filepath)
    
    def preprocess_text(self, content: str) -> str:
        """
        预处理输入文本，清理和标准化格式
        
        Args:
            content: 原始文本内容
            
        Returns:
            str: 预处理后的文本（仅清理格式，不分段）
        """
        if not content or not content.strip():
            return ""
        
        # 移除多余的空白字符
        content = ' '.join(content.split())
        
        return content
    
    def split_text_into_segments(self, content: str, segment_size: int = 50000) -> List[Dict[str, Any]]:
        """
        将长文本分割成多个段落，以便分批处理，并为每个段落添加顺序标记
        
        Args:
            content: 原始文本内容
            segment_size: 每段的字符数量（默认50000）
            
        Returns:
            List[Dict]: 分段后的文本列表，每个元素包含{text, order, start_pos, end_pos}
        """
        if not content or not content.strip():
            return []
        
        if len(content) <= segment_size:
            return [{
                "text": content,
                "order": 1,
                "start_pos": 0,
                "end_pos": len(content),
                "segment_id": "seg_001"
            }]
        
        try:
            segments = []
            segment_count = 0
            
            # 将文本分成指定大小的片段
            for i in range(0, len(content), segment_size):
                segment = content[i:i + segment_size]
                actual_start = i
                actual_end = i + len(segment)
                
                # 使用jieba进行智能分段，避免在词语中间截断
                if i + segment_size < len(content):  # 不是最后一段
                    words = list(jieba.cut(segment))
                    if len(words) > 1:  # 如果有多个词，尝试在词边界处分割
                        # 从后往前找到合适的分割点
                        total_length = 0
                        split_point = 0
                        for j, word in enumerate(words):
                            if total_length + len(word) > segment_size * 0.9:  # 保持在90%左右
                                split_point = total_length
                                break
                            total_length += len(word)
                        
                        if split_point > 0:
                            segment = content[i:i + split_point]
                            actual_end = i + split_point
                
                if segment.strip():
                    segment_count += 1
                    segments.append({
                        "text": segment.strip(),
                        "order": segment_count,
                        "start_pos": actual_start,
                        "end_pos": actual_end,
                        "segment_id": f"seg_{segment_count:03d}"
                    })
            
            logging.info(f"文本分段完成，原文本{len(content)}字符，分为{len(segments)}段，已添加顺序标记")
            return segments
            
        except Exception as e:
            logging.warning(f"智能分段失败，使用简单分段: {e}")
            # 回退到简单分段，也带有顺序标记
            segments = []
            segment_count = 0
            for i in range(0, len(content), segment_size):
                segment = content[i:i + segment_size]
                if segment.strip():
                    segment_count += 1
                    segments.append({
                        "text": segment.strip(),
                        "order": segment_count,
                        "start_pos": i,
                        "end_pos": min(i + segment_size, len(content)),
                        "segment_id": f"seg_{segment_count:03d}"
                    })
            return segments
    
    def _hierarchical_merge_results(self, results: List[Any], merge_func: callable, 
                                   extraction_type: str, group_size: int = 4) -> Any:
        """
        分层递归合并结果，每4个一组直到最终只剩一个结果
        
        Args:
            results: 待合并的结果列表
            merge_func: 合并函数
            extraction_type: 提取类型（用于日志）
            group_size: 每组的数量（默认4）
            
        Returns:
            Any: 最终合并结果
        """
        if not results:
            return {} if extraction_type != "characters" else []
        
        if len(results) == 1:
            return results[0]
        
        level = 1
        current_results = results.copy()
        
        while len(current_results) > 1:
            logging.info(f"{extraction_type}分层合并 - 第{level}层: {len(current_results)}个结果 -> 每{group_size}个一组")
            
            next_level_results = []
            
            # 将结果分组，每组4个
            for i in range(0, len(current_results), group_size):
                group = current_results[i:i + group_size]
                
                # 使用AI合并当前组的结果
                merged_result = self._ai_merge_group(group, merge_func, extraction_type, level, i // group_size + 1)
                if merged_result is not None:
                    next_level_results.append(merged_result)
            
            current_results = next_level_results
            level += 1
            
            logging.info(f"{extraction_type}第{level-1}层合并完成，得到{len(current_results)}个结果")
        
        logging.info(f"{extraction_type}分层递归合并完成，总共{level-1}层")
        return current_results[0] if current_results else ({} if extraction_type != "characters" else [])
    
    def _ai_merge_group(self, group: List[Any], merge_func: callable, 
                       extraction_type: str, level: int, group_num: int) -> Any:
        """
        使用AI智能合并一组结果
        
        Args:
            group: 待合并的结果组
            merge_func: 合并函数
            extraction_type: 提取类型
            level: 当前层级
            group_num: 组号
            
        Returns:
            Any: 合并后的结果
        """
        if not group:
            return {} if extraction_type != "characters" else []
        
        if len(group) == 1:
            return group[0]
        
        logging.info(f"AI合并第{level}层第{group_num}组，共{len(group)}个{extraction_type}结果")
        
        try:
            # 将组内结果转换为JSON字符串，发送给AI进行智能合并
            group_json = json.dumps(group, ensure_ascii=False, indent=2)
            
            # 构建合并提示词
            merge_prompt = self._build_merge_prompt(group_json, extraction_type)
            
            # 调用LLM进行智能合并
            result = invoke_with_cleaning(self.llm_adapter, merge_prompt)
            
            if not result.strip():
                logging.warning(f"第{level}层第{group_num}组AI合并返回空结果，使用基础合并")
                return self._fallback_merge_group(group, merge_func, extraction_type)
            
            # 尝试解析JSON结果
            try:
                merged_data = json.loads(result)
                logging.info(f"第{level}层第{group_num}组AI合并成功")
                return merged_data
            except json.JSONDecodeError:
                logging.warning(f"第{level}层第{group_num}组AI合并结果非JSON格式，使用基础合并")
                return self._fallback_merge_group(group, merge_func, extraction_type)
                
        except Exception as e:
            logging.error(f"第{level}层第{group_num}组AI合并失败: {e}，使用基础合并")
            return self._fallback_merge_group(group, merge_func, extraction_type)
    
    def _build_merge_prompt(self, group_json: str, extraction_type: str) -> str:
        """
        构建合并提示词
        
        Args:
            group_json: 组结果的JSON字符串
            extraction_type: 提取类型
            
        Returns:
            str: 合并提示词
        """
        if extraction_type == "worldview":
            return f"""请将以下多个世界观设定数据智能合并为一个完整统一的世界观：

{group_json}

要求：
1. 合并相同或相似的设定，去除重复信息
2. 保持信息的完整性和一致性
3. 整合不同片段中的补充信息
4. 返回标准JSON格式的世界观数据
5. 保持原有的数据结构

请返回合并后的完整世界观JSON数据："""

        elif extraction_type == "characters":
            return f"""请将以下多个角色列表智能合并为一个完整的角色列表：

{group_json}

要求：
1. 合并同名角色的信息，去除重复角色
2. 整合不同片段中对同一角色的补充描述
3. 保持所有独特角色的信息
4. 返回标准JSON格式的角色列表
5. 保持原有的数据结构

请返回合并后的完整角色列表JSON数据："""

        elif extraction_type == "plot":
            return f"""请将以下多个剧情大纲数据智能合并为一个完整统一的剧情大纲：

{group_json}

要求：
1. 整合不同片段的剧情信息
2. 保持剧情的逻辑连贯性
3. 合并相似的剧情点，去除重复信息
4. 返回标准JSON格式的剧情大纲数据
5. 保持原有的数据结构

请返回合并后的完整剧情大纲JSON数据："""
        
        else:
            return f"""请将以下多个{extraction_type}数据智能合并为一个完整的结果：

{group_json}

要求：
1. 合并相同或相似的信息，去除重复
2. 保持信息的完整性和一致性
3. 返回标准JSON格式数据
4. 保持原有的数据结构

请返回合并后的完整JSON数据："""
    
    def _fallback_merge_group(self, group: List[Any], merge_func: callable, extraction_type: str) -> Any:
        """
        当AI合并失败时的备用合并方法
        
        Args:
            group: 待合并的结果组
            merge_func: 合并函数
            extraction_type: 提取类型
            
        Returns:
            Any: 合并后的结果
        """
        if extraction_type == "characters":
            # 角色使用特殊的合并逻辑
            result = []
            for item in group:
                if isinstance(item, list):
                    result = self._merge_character_lists(result, item)
            return result
        else:
            # 世界观和剧情使用通用合并逻辑
            result = {}
            for item in group:
                if isinstance(item, dict):
                    result = merge_func(result, item)
            return result
    
    def _smart_truncate_with_jieba(self, content: str, max_length: int) -> str:
        """
        使用jieba进行智能分词截取，以500字符为单位进行分词
        
        Args:
            content: 原始文本内容
            max_length: 最大字符长度
            
        Returns:
            str: 智能截取后的文本
        """
        try:
            # 分词处理，以500字符为单位
            segment_size = 500
            segments = []
            current_length = 0
            
            # 将文本分成500字符的片段
            for i in range(0, len(content), segment_size):
                segment = content[i:i + segment_size]
                if current_length + len(segment) > max_length:
                    # 如果加上这个片段会超长，对当前片段进行jieba分词
                    words = list(jieba.cut(segment))
                    for word in words:
                        if current_length + len(word) <= max_length:
                            segments.append(word)
                            current_length += len(word)
                        else:
                            break
                    break
                else:
                    # 对当前片段进行分词并添加
                    words = list(jieba.cut(segment))
                    segments.extend(words)
                    current_length += len(segment)
            
            result = ''.join(segments)
            logging.info(f"jieba智能截取完成，从{len(content)}字符截取到{len(result)}字符")
            return result
            
        except Exception as e:
            logging.warning(f"jieba分词失败，使用简单截取: {e}")
            return content[:max_length] + "..."
    
    def extract_with_vector_context(self, content: str, query: str, top_k: int = 5) -> str:
        """
        使用向量检索增强的上下文提取
        
        Args:
            content: 原始内容
            query: 检索查询
            top_k: 返回的相关片段数量
            
        Returns:
            str: 相关上下文片段
        """
        if not self.vector_store:
            return content[:2000]  # 如果没有向量存储，返回前2000字符
        
        try:
            # 使用向量检索获取相关片段
            results = self.vector_store.similarity_search(query, k=top_k)
            context_pieces = []
            
            for result in results:
                context_pieces.append(result.page_content)
            
            return "\n\n".join(context_pieces)
            
        except Exception as e:
            logging.warning(f"向量检索失败: {e}")
            return content[:2000]
    
    def _process_segment_concurrently(self, segments: List[Dict[str, Any]], 
                                     extraction_type: str, 
                                     prompt_template_name: str,
                                     context_query: str) -> List[Any]:
        """
        并发处理文本段落提取
        
        Args:
            segments: 分段数据列表
            extraction_type: 提取类型（worldview/characters/plot）
            prompt_template_name: 提示词模板名称
            context_query: 向量检索查询字符串
            
        Returns:
            List[Any]: 提取结果列表
        """
        def process_single_segment(segment_data: Dict[str, Any]) -> Optional[Any]:
            """处理单个段落的函数"""
            segment_order = segment_data.get("order", 0)
            segment_text = segment_data.get("text", "")
            segment_id = segment_data.get("segment_id", "")
            
            logging.info(f"并发处理 - 开始处理{extraction_type}段落 {segment_order} (ID: {segment_id})")
            
            try:
                # 使用向量检索获取相关内容
                context = self.extract_with_vector_context(
                    segment_text,
                    context_query,
                    top_k=8
                )
                
                # 导入并获取提示词模板
                from prompt_definitions import knowledge_worldview_extraction_prompt, knowledge_character_extraction_prompt, knowledge_plot_extraction_prompt
                
                if prompt_template_name == "worldview":
                    prompt_template = knowledge_worldview_extraction_prompt
                elif prompt_template_name == "character":
                    prompt_template = knowledge_character_extraction_prompt
                elif prompt_template_name == "plot":
                    prompt_template = knowledge_plot_extraction_prompt
                else:
                    logging.error(f"未知的提示词模板: {prompt_template_name}")
                    return None
                
                # 构建提示词，包含段落顺序信息
                prompt = prompt_template.format(
                    content=f"[段落{segment_order}] {context}"
                )
                
                # 调用LLM进行提取
                result = invoke_with_cleaning(self.llm_adapter, prompt)
                
                if not result.strip():
                    logging.warning(f"{extraction_type}段落{segment_order}提取返回空结果")
                    return None
                
                # 尝试解析JSON结果
                try:
                    segment_data_result = json.loads(result)
                    
                    # 为结果添加元数据
                    if extraction_type == "characters":
                        if isinstance(segment_data_result, list):
                            for char in segment_data_result:
                                if isinstance(char, dict):
                                    char["_segment_metadata"] = {
                                        "order": segment_order,
                                        "segment_id": segment_id,
                                        "start_pos": segment_data.get("start_pos", 0),
                                        "end_pos": segment_data.get("end_pos", 0)
                                    }
                        else:
                            logging.warning(f"角色段落{segment_order}数据格式错误，应为列表")
                            return None
                    else:
                        if isinstance(segment_data_result, dict):
                            segment_data_result["_segment_metadata"] = {
                                "order": segment_order,
                                "segment_id": segment_id,
                                "start_pos": segment_data.get("start_pos", 0),
                                "end_pos": segment_data.get("end_pos", 0)
                            }
                    
                    logging.info(f"{extraction_type}段落{segment_order}并发处理成功")
                    return segment_data_result
                    
                except json.JSONDecodeError:
                    logging.warning(f"段落{segment_order}返回结果非JSON格式，尝试文本解析")
                    if extraction_type == "worldview":
                        segment_data_result = self._parse_worldview_text(result)
                    elif extraction_type == "characters":
                        segment_data_result = self._parse_characters_text(result)
                    elif extraction_type == "plot":
                        segment_data_result = self._parse_plot_text(result)
                    else:
                        return None
                    
                    if segment_data_result:
                        # 为非JSON结果添加元数据
                        if extraction_type == "characters":
                            for char in segment_data_result:
                                if isinstance(char, dict):
                                    char["_segment_metadata"] = {
                                        "order": segment_order,
                                        "segment_id": segment_id
                                    }
                        else:
                            segment_data_result["_segment_metadata"] = {
                                "order": segment_order,
                                "segment_id": segment_id
                            }
                        return segment_data_result
                    return None
                    
            except ImportError:
                logging.error(f"找不到{prompt_template_name}提取提示词")
                return None
            except Exception as e:
                logging.error(f"{extraction_type}段落{segment_order}并发处理失败: {e}")
                return None
        
        # 使用ThreadPoolExecutor进行并发处理
        segment_results = []
        
        logging.info(f"开始并发处理{len(segments)}个{extraction_type}段落，最大并发数: {self.max_concurrent_requests}")
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent_requests) as executor:
            # 提交所有任务
            future_to_segment = {
                executor.submit(process_single_segment, segment): segment 
                for segment in segments
            }
            
            # 收集结果，保持原始顺序
            results_dict = {}
            for future in as_completed(future_to_segment):
                segment = future_to_segment[future]
                segment_order = segment.get("order", 0)
                try:
                    result = future.result()
                    if result is not None:
                        results_dict[segment_order] = result
                except Exception as e:
                    logging.error(f"段落{segment_order}并发处理异常: {e}")
        
        # 按顺序重新排列结果
        for segment in segments:
            segment_order = segment.get("order", 0)
            if segment_order in results_dict:
                segment_results.append(results_dict[segment_order])
        
        logging.info(f"{extraction_type}并发处理完成，成功处理{len(segment_results)}/{len(segments)}个段落")
        return segment_results
    
    def extract_worldview(self, content: str) -> Dict[str, Any]:
        """
        从知识库内容中提取世界观设定，使用分层递归处理
        
        Args:
            content: 知识库文本内容
            
        Returns:
            Dict: 包含世界观各要素的字典
        """
        logging.info("开始提取世界观设定...")
        
        # 预处理文本
        processed_content = self.preprocess_text(content)
        if not processed_content:
            logging.warning("预处理后内容为空")
            return {}
        
        # 分段处理
        segments = self.split_text_into_segments(processed_content)
        
        # 第一层：使用并发处理提取所有段落
        segment_results = self._process_segment_concurrently(
            segments,
            "worldview",
            "worldview",
            "世界观 地理 历史 背景 科技 魔法 社会 文化 政治"
        )
        
        # 第二层及后续：使用分层递归合并所有结果
        if not segment_results:
            logging.warning("没有成功提取到任何世界观数据")
            return {}
        
        logging.info(f"第一层提取完成，共得到{len(segment_results)}个世界观片段")
        
        # 使用分层递归合并
        final_worldview = self._hierarchical_merge_results(
            segment_results, 
            self._merge_worldview_data,
            "worldview"
        )
        
        logging.info("世界观分层递归提取完成")
        return final_worldview
    
    def extract_characters(self, content: str) -> List[Dict[str, Any]]:
        """
        从知识库内容中提取角色信息，使用分层递归处理
        
        Args:
            content: 知识库文本内容
            
        Returns:
            List[Dict]: 角色信息列表
        """
        logging.info("开始提取角色信息...")
        
        processed_content = self.preprocess_text(content)
        if not processed_content:
            return []
        
        # 分段处理
        segments = self.split_text_into_segments(processed_content)
        
        # 第一层：使用并发处理提取所有段落
        segment_results = self._process_segment_concurrently(
            segments,
            "characters",
            "character",
            "角色 人物 主角 配角 性格 能力 关系 背景"
        )
        
        # 第二层及后续：使用分层递归合并所有结果
        if not segment_results:
            logging.warning("没有成功提取到任何角色数据")
            return []
        
        logging.info(f"第一层提取完成，共得到{len(segment_results)}个角色片段")
        
        # 使用分层递归合并
        final_characters = self._hierarchical_merge_results(
            segment_results,
            self._merge_character_lists,
            "characters"
        )
        
        logging.info(f"角色分层递归提取完成，最终提取到{len(final_characters) if isinstance(final_characters, list) else 0}个角色")
        return final_characters if isinstance(final_characters, list) else []
    
    def extract_plot_outline(self, content: str) -> Dict[str, Any]:
        """
        从知识库内容中提取剧情大纲，使用分层递归处理
        
        Args:
            content: 知识库文本内容
            
        Returns:
            Dict: 剧情大纲信息
        """
        logging.info("开始提取剧情大纲...")
        
        # 预处理文本
        processed_content = self.preprocess_text(content)
        if not processed_content:
            logging.warning("预处理后内容为空")
            return {}
        
        # 分段处理
        segments = self.split_text_into_segments(processed_content)
        
        # 第一层：使用并发处理提取所有段落
        segment_results = self._process_segment_concurrently(
            segments,
            "plot",
            "plot",
            "剧情 故事线 情节 冲突 高潮 结局 发展 转折"
        )
        
        # 第二层及后续：使用分层递归合并所有结果
        if not segment_results:
            logging.warning("没有成功提取到任何剧情数据")
            return {}
        
        logging.info(f"第一层提取完成，共得到{len(segment_results)}个剧情片段")
        
        # 使用分层递归合并
        final_plot = self._hierarchical_merge_results(
            segment_results,
            self._merge_worldview_data,
            "plot"
        )
        
        logging.info("剧情分层递归提取完成")
        return final_plot
    
    def analyze_relationships(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析角色关系网络
        
        Args:
            characters: 角色信息列表
            
        Returns:
            Dict: 关系网络数据
        """
        logging.info("开始分析角色关系...")
        
        if not characters:
            return {}
        
        try:
            from prompt_definitions import knowledge_relationship_analysis_prompt
            
            # 构建角色信息文本
            characters_text = json.dumps(characters, ensure_ascii=False, indent=2)
            
            prompt = knowledge_relationship_analysis_prompt.format(
                characters=characters_text
            )
            
            result = invoke_with_cleaning(self.llm_adapter, prompt)
            
            if result.strip():
                try:
                    relationships = json.loads(result)
                    logging.info("关系分析成功")
                    return relationships
                except json.JSONDecodeError:
                    logging.warning("关系分析结果非JSON格式")
                    return {}
            
        except ImportError:
            logging.warning("找不到relationship分析提示词，跳过关系分析")
        except Exception as e:
            logging.error(f"关系分析失败: {e}")
        
        return {}
    
    def generate_structure(self, worldview: Dict, characters: List[Dict], 
                          plot_outline: Dict, relationships: Dict = None) -> Dict[str, Any]:
        """
        生成完整的结构化知识库数据
        
        Args:
            worldview: 世界观数据
            characters: 角色数据
            plot_outline: 剧情大纲数据  
            relationships: 关系数据
            
        Returns:
            Dict: 完整的结构化数据
        """
        structure = {
            "metadata": {
                "extracted_time": "",
                "source_files": [],
                "extraction_version": "1.0"
            },
            "worldview": worldview,
            "characters": characters,
            "plot_outline": plot_outline,
            "relationships": relationships or {},
            "statistics": {
                "worldview_elements": len(worldview.get("elements", [])),
                "character_count": len(characters),
                "plot_points": len(plot_outline.get("plot_points", [])),
                "relationship_count": len(relationships.get("relationships", [])) if relationships else 0
            }
        }
        
        return structure
    
    def save_extracted_knowledge(self, structured_data: Dict[str, Any], 
                                filename: str = "extracted_knowledge.json") -> bool:
        """
        保存提取的结构化知识到文件
        
        Args:
            structured_data: 结构化数据
            filename: 保存的文件名
            
        Returns:
            bool: 是否保存成功
        """
        if not self.filepath:
            logging.error("未指定文件路径")
            return False
        
        try:
            output_path = os.path.join(self.filepath, filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"结构化知识已保存至: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"保存失败: {e}")
            return False
    
    # 辅助文本解析方法（备用）
    def _parse_worldview_text(self, text: str) -> Dict[str, Any]:
        """解析世界观文本为结构化数据"""
        # 简单的文本解析逻辑
        return {"raw_content": text, "parsed": False}
    
    def _parse_characters_text(self, text: str) -> List[Dict[str, Any]]:
        """解析角色文本为结构化数据"""
        return [{"raw_content": text, "parsed": False}]
    
    def _parse_plot_text(self, text: str) -> Dict[str, Any]:
        """解析剧情文本为结构化数据"""
        return {"raw_content": text, "parsed": False}
    
    def _merge_worldview_data(self, base_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并多个段落的世界观数据
        
        Args:
            base_data: 基础数据
            new_data: 新数据
            
        Returns:
            Dict: 合并后的数据
        """
        if not base_data:
            return new_data
        if not new_data:
            return base_data
        
        merged = base_data.copy()
        
        # 合并不同类型的字段
        for key, value in new_data.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, list) and isinstance(merged[key], list):
                # 合并列表，去重
                existing_items = {str(item) for item in merged[key]}
                for item in value:
                    if str(item) not in existing_items:
                        merged[key].append(item)
                        existing_items.add(str(item))
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                # 递归合并字典
                merged[key] = self._merge_dict_data(merged[key], value)
            elif isinstance(value, str) and isinstance(merged[key], str):
                # 合并字符串，避免重复
                if value not in merged[key]:
                    merged[key] += "\n" + value
        
        return merged
    
    def _merge_dict_data(self, base_dict: Dict, new_dict: Dict) -> Dict:
        """递归合并字典数据"""
        merged = base_dict.copy()
        for key, value in new_dict.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                merged[key] = self._merge_dict_data(merged[key], value)
            elif isinstance(value, list) and isinstance(merged[key], list):
                existing_items = {str(item) for item in merged[key]}
                for item in value:
                    if str(item) not in existing_items:
                        merged[key].append(item)
        return merged
    
    def _merge_character_lists(self, base_list: List[Dict], new_list: List[Dict]) -> List[Dict]:
        """
        合并角色列表，避免重复角色
        
        Args:
            base_list: 基础角色列表
            new_list: 新角色列表
            
        Returns:
            List: 合并后的角色列表
        """
        if not base_list:
            return new_list
        if not new_list:
            return base_list
        
        merged = base_list.copy()
        existing_names = {char.get("name", "") for char in base_list}
        
        for new_char in new_list:
            char_name = new_char.get("name", "")
            if char_name and char_name not in existing_names:
                merged.append(new_char)
                existing_names.add(char_name)
            elif char_name in existing_names:
                # 如果角色已存在，合并其信息
                for i, existing_char in enumerate(merged):
                    if existing_char.get("name") == char_name:
                        merged[i] = self._merge_dict_data(existing_char, new_char)
                        break
        
        return merged


def parse_knowledge_from_file(
    file_path: str,
    llm_interface_format: str,
    llm_api_key: str, 
    llm_base_url: str,
    llm_model: str,
    filepath: str,
    embedding_adapter=None
) -> Optional[Dict[str, Any]]:
    """
    从文件中解析知识库的便捷函数
    
    Args:
        file_path: 知识库文件路径
        其他参数同KnowledgeParser初始化参数
        
    Returns:
        Optional[Dict]: 结构化知识数据，失败返回None
    """
    try:
        # 读取文件内容
        content = read_file(file_path)
        if not content.strip():
            logging.warning("文件内容为空")
            return None
        
        # 创建解析器
        parser = KnowledgeParser(
            llm_interface_format=llm_interface_format,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            llm_model=llm_model,
            embedding_adapter=embedding_adapter,
            filepath=filepath
        )
        
        # 提取各要素 - 使用并发处理
        logging.info(f"开始并发解析知识库文件: {file_path}")
        
        worldview = None
        characters = None
        plot_outline = None
        relationships = None
        
        # 定义三个主要要素提取任务，关系分析依赖角色数据需要单独处理
        def extract_worldview_task():
            return parser.extract_worldview(content)
        
        def extract_characters_task():
            return parser.extract_characters(content)
        
        def extract_plot_task():
            return parser.extract_plot_outline(content)
        
        try:
            # 并发执行三个主要要素提取任务
            with ThreadPoolExecutor(max_workers=3) as executor:
                # 提交任务
                worldview_future = executor.submit(extract_worldview_task)
                characters_future = executor.submit(extract_characters_task)  
                plot_future = executor.submit(extract_plot_task)
                
                # 获取结果
                worldview = worldview_future.result()
                characters = characters_future.result()
                plot_outline = plot_future.result()
                
                logging.info("并发要素提取完成")
        
        except Exception as e:
            logging.error(f"并发要素提取失败，回退到串行处理: {e}")
            # 如果并发失败，回退到原来的串行处理
            worldview = parser.extract_worldview(content)
            characters = parser.extract_characters(content)
            plot_outline = parser.extract_plot_outline(content)
        
        # 关系分析依赖角色数据，单独处理
        relationships = parser.analyze_relationships(characters)
        
        # 生成结构化数据
        structured_data = parser.generate_structure(
            worldview, characters, plot_outline, relationships
        )
        
        # 确保metadata字段存在
        if "metadata" not in structured_data:
            structured_data["metadata"] = {}
        
        # 添加源文件信息
        structured_data["metadata"]["source_files"] = [file_path]
        structured_data["metadata"]["extracted_time"] = ""  # 可以添加时间戳
        
        # 保存结果
        parser.save_extracted_knowledge(structured_data)
        
        logging.info("知识库解析完成")
        
        # 生成AI书评（如果解析成功）
        try:
            from novel_generator.review_generator import generate_book_review
            logging.info("开始生成AI书评...")
            
            review_text = generate_book_review(
                structured_knowledge=structured_data,
                api_key=llm_api_key,
                base_url=llm_base_url,
                llm_model=llm_model,
                interface_format=llm_interface_format,
                filepath=filepath,
                temperature=0.7,
                max_tokens=2048,
                timeout=600
            )
            
            if review_text:
                logging.info("✅ AI书评生成完成")
            else:
                logging.warning("⚠️ AI书评生成失败")
                
        except Exception as e:
            logging.error(f"生成AI书评时出错: {e}")
        
        return structured_data
        
    except Exception as e:
        logging.error(f"知识库解析失败: {e}")
        traceback.print_exc()
        return None