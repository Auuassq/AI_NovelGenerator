#novel_generator/knowledge.py
# -*- coding: utf-8 -*-
"""
知识文件导入至向量库（advanced_split_content、import_knowledge_file）
"""
import os
import logging
import re
import traceback
import jieba
import jieba.posseg as pseg

# 关闭jieba的DEBUG模式，避免输出详细日志
jieba.setLogLevel(20)  # 设置为INFO级别，避免DEBUG信息
import warnings
from utils import read_file
from novel_generator.vectorstore_utils import load_vector_store, init_vector_store
from langchain.docstore.document import Document

# 禁用特定的Torch警告
warnings.filterwarnings('ignore', message='.*Torch was not compiled with flash attention.*')
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def advanced_split_content(content: str, similarity_threshold: float = 0.7, max_length: int = 500) -> list:
    """
    使用jieba分词的分段策略将文本切分为适合向量存储的段落片段。
    
    该方法的核心思路是：
    1. 使用jieba进行中文分词处理，保持语义完整性
    2. 基于分词结果和语义边界进行文本分割
    3. 采用贪心算法将词语组合成段落，确保每段不超过最大长度限制
    
    这种方法的优势：
    - 利用jieba的中文分词能力，更好地理解中文语义
    - 基于词语边界分割，保持语义完整性
    - 有效利用段落空间，避免过多短段落造成的向量检索效率问题
    
    Args:
        content (str): 需要分割的原始文本内容
        similarity_threshold (float, optional): 相似度阈值，当前未使用，保留用于未来扩展. Defaults to 0.7.
        max_length (int, optional): 每个段落的最大字符长度. Defaults to 500.
        
    Returns:
        list: 包含分割后文本段落的列表，每个段落都是完整词语的组合
    """
    if not content.strip():
        return []
    
    # 使用jieba进行分词
    words = list(jieba.cut(content))
    
    if not words:
        return []

    # 存储最终分割结果的列表
    final_segments = []
    
    # 当前正在构建的段落
    current_segment = []
    current_length = 0
    
    # 遍历所有词语，使用贪心算法进行分组

    for word in words:
        word_length = len(word)
        
        # 如果加入当前词语会使段落超过最大长度限制
        if current_length + word_length > max_length:
            # 保存当前段落（如果非空）
            if current_segment:
                final_segments.append(''.join(current_segment))
            
            # 开始新的段落，包含当前词语
            current_segment = [word]
            current_length = word_length
        else:
            # 将词语添加到当前段落
            current_segment.append(word)
            current_length += word_length
    
    # 处理最后一个段落
    if current_segment:
        final_segments.append(''.join(current_segment))
    
    return final_segments

def import_knowledge_file(
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    file_path: str,
    filepath: str
):
    """
    将用户指定的知识库文件导入到向量数据库中，以便在生成章节时进行语义检索。
    
    该函数的主要工作流程如下：
    1. 检查并读取指定的知识库文件
    2. 对文件内容进行分段处理
    3. 创建指定类型的嵌入模型适配器
    4. 初始化或加载向量存储
    5. 将文本段落转换为向量并存储到向量数据库中
    
    Args:
        embedding_api_key (str): 嵌入模型服务的API密钥
        embedding_url (str): 嵌入模型服务的基础URL地址
        embedding_interface_format (str): 嵌入模型接口格式（如OpenAI、Ollama等）
        embedding_model_name (str): 嵌入模型名称
        file_path (str): 待导入的知识库文件路径
        filepath (str): 项目保存路径，用于确定向量数据库存储位置
        
    Returns:
        None: 无返回值，结果通过日志输出和文件存储体现
    """
    # 记录开始导入日志，包含文件路径和嵌入模型信息
    logging.info(f"开始导入知识库文件: {file_path}, 接口格式: {embedding_interface_format}, 模型: {embedding_model_name}")
    
    # 检查文件是否存在，如果不存在则记录警告日志并返回
    if not os.path.exists(file_path):
        logging.warning(f"知识库文件不存在: {file_path}")
        return
    
    # 读取文件内容
    content = read_file(file_path)
    
    # 检查文件内容是否为空，如果为空则记录警告日志并返回
    if not content.strip():
        logging.warning("知识库文件内容为空。")
        return
    
    # 对文件内容进行分段处理，将大段文本切分为适合向量化的较小段落
    paragraphs = advanced_split_content(content)
    
    # 导入嵌入适配器模块并创建指定类型的嵌入适配器实例
    from embedding_adapters import create_embedding_adapter
    embedding_adapter = create_embedding_adapter(
        embedding_interface_format,      # 嵌入模型接口格式
        embedding_api_key,               # API密钥
        embedding_url if embedding_url else "http://localhost:11434/api",  # 服务地址，如果未提供则使用默认地址
        embedding_model_name             # 嵌入模型名称
    )
    
    # 尝试加载已存在的向量存储，如果不存在或加载失败则返回None
    store = load_vector_store(embedding_adapter, filepath)
    
    # 如果向量存储不存在或加载失败，则初始化一个新的向量存储
    if not store:
        logging.info("Vector store does not exist or load failed. Initializing a new one for knowledge import...")
        # 初始化向量存储，将分段后的文本转换为向量并存储
        store = init_vector_store(embedding_adapter, paragraphs, filepath)
        if store:
            # 初始化成功，记录成功日志
            logging.info("知识库文件已成功导入至向量库(新初始化)。")
        else:
            # 初始化失败，记录警告日志
            logging.warning("知识库导入失败，跳过。")
    else:
        # 如果向量存储已存在，则采用追加模式将新内容添加到现有存储中
        try:
            # 将文本段落转换为文档对象列表
            docs = [Document(page_content=str(p)) for p in paragraphs]
            # 将文档添加到现有的向量存储中
            store.add_documents(docs)
            # 记录成功日志
            logging.info("知识库文件已成功导入至向量库(追加模式)。")
        except Exception as e:
            # 如果添加文档过程中出现异常，记录警告日志和异常信息
            logging.warning(f"知识库导入失败: {e}")
            traceback.print_exc()
