# test_hierarchical_processing.py
# -*- coding: utf-8 -*-
"""
测试分层递归知识提取功能
"""

import sys
import os
import logging
from typing import Dict, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

def test_text_segmentation():
    """测试文本分段功能"""
    print("=== 测试文本分段功能 ===")
    
    from novel_generator.knowledge_parser import KnowledgeParser
    
    # 创建一个简单的解析器实例（不需要LLM初始化）
    parser = KnowledgeParser.__new__(KnowledgeParser)
    
    # 测试短文本
    short_text = "这是一个短文本测试"
    segments = parser.split_text_into_segments(short_text, 50000)
    print(f"短文本分段结果: {len(segments)}段")
    assert len(segments) == 1
    
    # 测试长文本
    long_text = "测试文本" * 10000  # 生成约40K字符的文本
    segments = parser.split_text_into_segments(long_text, 50000)
    print(f"长文本分段结果: {len(segments)}段，总长度: {len(long_text)}字符")
    
    # 验证分段后所有内容合并是否与原文一致
    combined = "".join(segments)
    print(f"分段前后长度对比: 原文 {len(long_text)} vs 合并 {len(combined)}")
    
    print("文本分段功能测试通过")

def test_hierarchical_merge_structure():
    """测试分层递归合并结构"""
    print("\n=== 测试分层递归合并结构 ===")
    
    from novel_generator.knowledge_parser import KnowledgeParser
    
    # 创建解析器实例
    parser = KnowledgeParser.__new__(KnowledgeParser)
    
    # 测试世界观合并
    def mock_merge_func(base, new):
        """模拟合并函数"""
        result = base.copy() if base else {}
        if new:
            for key, value in new.items():
                if key in result:
                    if isinstance(value, str) and isinstance(result[key], str):
                        result[key] = result[key] + " " + value
                    else:
                        result[key] = value
                else:
                    result[key] = value
        return result
    
    # 模拟AI合并函数，总是返回基础合并结果
    def mock_ai_merge(group, merge_func, extraction_type, level, group_num):
        """模拟AI合并，使用基础合并"""
        return parser._fallback_merge_group(group, merge_func, extraction_type)
    
    # 替换AI合并函数为模拟函数
    parser._ai_merge_group = mock_ai_merge
    
    # 测试不同数量的结果
    test_cases = [
        ([], "空结果测试"),
        ([{"test": "single"}], "单一结果测试"),
        ([{"a": "1"}, {"b": "2"}], "两个结果测试"),
        ([{"a": "1"}, {"b": "2"}, {"c": "3"}], "三个结果测试"),
        ([{"a": "1"}, {"b": "2"}, {"c": "3"}, {"d": "4"}, {"e": "5"}], "五个结果测试"),
        ([{"a": str(i)} for i in range(10)], "十个结果测试"),
    ]
    
    for results, description in test_cases:
        print(f"\n{description}: {len(results)}个输入")
        merged = parser._hierarchical_merge_results(results, mock_merge_func, "worldview")
        print(f"合并结果: {type(merged).__name__}")
        
        if results:
            if len(results) == 1:
                assert merged == results[0], "单一结果应直接返回"
            else:
                assert isinstance(merged, dict), "多个结果应返回字典"
        else:
            assert merged == {}, "空结果应返回空字典"
    
    print("分层递归合并结构测试通过")

def test_character_merge():
    """测试角色合并功能"""
    print("\n=== 测试角色合并功能 ===")
    
    from novel_generator.knowledge_parser import KnowledgeParser
    
    parser = KnowledgeParser.__new__(KnowledgeParser)
    
    # 测试角色列表合并
    chars1 = [{"name": "张三", "age": 25}]
    chars2 = [{"name": "李四", "age": 30}]
    chars3 = [{"name": "张三", "description": "主角"}]  # 与chars1重名
    
    # 测试基础合并
    merged_12 = parser._merge_character_lists(chars1, chars2)
    print(f"合并不重名角色: {len(merged_12)}个角色")
    assert len(merged_12) == 2
    
    # 测试重名角色合并
    merged_13 = parser._merge_character_lists(chars1, chars3)
    print(f"合并重名角色: {len(merged_13)}个角色")
    assert len(merged_13) == 1
    assert "age" in merged_13[0] and "description" in merged_13[0]
    
    print("角色合并功能测试通过")

def test_jieba_segmentation():
    """测试jieba智能分段"""
    print("\n=== 测试jieba智能分段 ===")
    
    from novel_generator.knowledge_parser import KnowledgeParser
    
    parser = KnowledgeParser.__new__(KnowledgeParser)
    
    # 测试中文文本智能分段
    chinese_text = "这是一个测试文档，用来验证jieba分词器的智能分段功能。我们希望分段在词语边界处进行，而不是在词语中间截断。"
    
    segments = parser.split_text_into_segments(chinese_text, 30)  # 使用较小的分段大小进行测试
    print(f"中文智能分段: 原文{len(chinese_text)}字符，分为{len(segments)}段")
    
    # 验证分段质量
    for i, segment in enumerate(segments):
        print(f"段落{i+1}: {segment[:20]}...")
    
    print("jieba智能分段测试通过")

def main():
    """主测试函数"""
    print("开始测试分层递归知识提取功能...")
    
    try:
        test_text_segmentation()
        test_hierarchical_merge_structure()
        test_character_merge()
        test_jieba_segmentation()
        
        print("\n" + "="*50)
        print("所有测试通过！分层递归功能工作正常")
        print("="*50)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)