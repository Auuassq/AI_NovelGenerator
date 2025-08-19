# -*- coding: utf-8 -*-
"""
AI书评生成模块
在小说要素解析完成后，生成专业的书评分析
"""
import os
import json
import logging
import traceback
from typing import Dict, Any, Optional
from novel_generator.common import invoke_with_cleaning
from llm_adapters import create_llm_adapter


def generate_book_review(
    structured_knowledge: Dict[str, Any],
    api_key: str,
    base_url: str,
    llm_model: str,
    interface_format: str,
    filepath: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600
) -> Optional[str]:
    """
    基于解析出的小说要素生成AI书评
    
    Args:
        structured_knowledge: 结构化知识数据
        api_key: API密钥
        base_url: API基础URL
        llm_model: 使用的模型名
        interface_format: 接口格式
        filepath: 文件保存路径
        temperature: 温度参数
        max_tokens: 最大token数
        timeout: 超时时间
    
    Returns:
        生成的书评内容，失败时返回None
    """
    try:
        if not structured_knowledge:
            logging.warning("无结构化知识数据，无法生成书评")
            return None
            
        # 创建LLM适配器
        llm_adapter = create_llm_adapter(
            interface_format=interface_format,
            base_url=base_url,
            model_name=llm_model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        
        # 构建书评分析提示词
        review_prompt = build_review_prompt(structured_knowledge)
        
        logging.info("开始生成AI书评...")
        review_text = invoke_with_cleaning(llm_adapter, review_prompt)
        
        if not review_text or not review_text.strip():
            logging.warning("书评生成失败，返回空内容")
            return None
            
        # 保存书评到文件
        review_file = os.path.join(filepath, "ai_book_review.txt")
        try:
            with open(review_file, "w", encoding="utf-8") as f:
                f.write(review_text)
            logging.info(f"AI书评已保存到: {review_file}")
        except Exception as e:
            logging.warning(f"保存书评文件失败: {e}")
            
        return review_text
        
    except Exception as e:
        logging.error(f"生成AI书评时出错: {e}")
        traceback.print_exc()
        return None


def build_review_prompt(structured_knowledge: Dict[str, Any]) -> str:
    """
    根据结构化知识构建书评生成提示词
    
    Args:
        structured_knowledge: 结构化知识数据
    
    Returns:
        构建好的提示词
    """
    
    # 提取基本信息
    metadata = structured_knowledge.get("metadata", {})
    title = metadata.get("title", "未知作品")
    
    # 格式化世界观信息
    worldview_summary = format_worldview_for_review(structured_knowledge.get("worldview", {}))
    
    # 格式化角色信息
    characters_summary = format_characters_for_review(structured_knowledge.get("characters", []))
    
    # 格式化剧情信息
    plot_summary = format_plot_for_review(structured_knowledge.get("plot_outline", {}))
    
    # 构建完整的书评提示词
    prompt = f"""你是一位资深的文学评论家和书评专家，请基于以下提取的小说要素，撰写一篇专业、深入的书评分析。

=== 作品信息 ===
作品标题：{title}

=== 世界观设定 ===
{worldview_summary}

=== 角色分析 ===
{characters_summary}

=== 剧情要素 ===
{plot_summary}

请从以下几个维度进行专业书评：

1. **世界观构建**
   - 分析世界观的完整性、独创性和逻辑性
   - 评价世界设定对故事的支撑作用
   - 指出世界观的亮点和不足

2. **人物塑造**
   - 分析主要角色的性格深度和复杂性
   - 评价角色间的关系动态和冲突张力
   - 讨论角色发展弧线的合理性

3. **剧情结构**
   - 分析故事主线的逻辑性和吸引力
   - 评价冲突设置的合理性和戏剧张力
   - 讨论主题表达的深度和意义

4. **文学价值**
   - 评估作品的思想深度和艺术价值
   - 分析作品的创新性和独特之处
   - 讨论作品可能的读者群体和影响力

5. **总体评价**
   - 给出综合评分建议（1-10分）
   - 总结作品的核心优势和主要不足
   - 提供阅读建议和改进建议

要求：
- 保持客观专业的评论态度
- 用词准确，分析深入
- 既要肯定优点，也要指出问题
- 篇幅控制在1000-1500字
- 语言流畅，逻辑清晰

请开始撰写书评："""
    
    return prompt


def format_worldview_for_review(worldview: Dict[str, Any]) -> str:
    """
    格式化世界观信息用于书评分析
    """
    if not worldview:
        return "世界观信息不够完整，难以进行深入分析。"
    
    sections = []
    
    # 总概述
    if worldview.get("overview"):
        sections.append(f"总体设定：{worldview['overview']}")
    
    # 主要设定类别
    categories = {
        "geography": "地理环境",
        "history": "历史背景", 
        "technology": "科技水平",
        "society": "社会结构",
        "culture": "文化特色",
        "magic_system": "魔法/超自然体系",
        "politics": "政治制度",
        "economy": "经济体系"
    }
    
    for key, name in categories.items():
        if key in worldview and worldview[key]:
            elements = worldview[key]
            if elements:
                element_names = [elem.get("name", "") for elem in elements[:3] if elem.get("name")]
                if element_names:
                    sections.append(f"{name}：{'、'.join(element_names)}")
    
    return "\n".join(sections) if sections else "世界观要素较少，设定相对简单。"


def format_characters_for_review(characters: list) -> str:
    """
    格式化角色信息用于书评分析
    """
    if not characters:
        return "角色信息不够详细，难以进行深度分析。"
    
    sections = []
    
    # 统计角色类型
    main_chars = [char for char in characters if char.get("role") in ["主角", "男主角", "女主角", "主要角色"]]
    supporting_chars = [char for char in characters if char.get("role") in ["配角", "次要角色", "重要配角"]]
    
    sections.append(f"角色规模：主要角色{len(main_chars)}个，配角{len(supporting_chars)}个")
    
    # 主要角色分析
    if main_chars:
        sections.append("\n主要角色：")
        for char in main_chars[:3]:  # 最多展示3个主要角色
            name = char.get("name", "未命名")
            role = char.get("role", "")
            personality = char.get("personality", [])
            motivation = char.get("motivation", "")
            
            char_desc = f"- {name}（{role}）"
            if personality:
                char_desc += f"：性格{'、'.join(personality[:2])}"
            if motivation:
                char_desc += f"，目标：{motivation[:50]}{'...' if len(motivation) > 50 else ''}"
            sections.append(char_desc)
    
    return "\n".join(sections)


def format_plot_for_review(plot_outline: Dict[str, Any]) -> str:
    """
    格式化剧情信息用于书评分析
    """
    if not plot_outline:
        return "剧情要素信息不足，难以进行结构分析。"
    
    sections = []
    
    # 主题和主线
    if plot_outline.get("theme"):
        sections.append(f"核心主题：{plot_outline['theme']}")
        
    if plot_outline.get("main_storyline"):
        storyline = plot_outline["main_storyline"]
        sections.append(f"主线剧情：{storyline[:100]}{'...' if len(storyline) > 100 else ''}")
    
    # 主要冲突
    conflicts = plot_outline.get("major_conflicts", [])
    if conflicts:
        sections.append(f"\n主要冲突：")
        for i, conflict in enumerate(conflicts[:3], 1):
            name = conflict.get("name", f"冲突{i}")
            desc = conflict.get("description", "")
            if desc:
                sections.append(f"- {name}：{desc[:80]}{'...' if len(desc) > 80 else ''}")
            else:
                sections.append(f"- {name}")
    
    return "\n".join(sections) if sections else "剧情结构信息较少，需要更多细节才能深入分析。"