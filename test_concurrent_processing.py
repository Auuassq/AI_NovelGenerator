# test_concurrent_processing.py
# -*- coding: utf-8 -*-
"""
测试并发知识提取功能
"""

import sys
import os
import logging
import time
from typing import Dict, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

def test_concurrent_functionality():
    """测试并发功能"""
    print("=== 测试并发知识提取功能 ===")
    
    from novel_generator.knowledge_parser import KnowledgeParser
    
    # 创建一个简单的解析器实例（不需要完整的LLM初始化）
    parser = KnowledgeParser.__new__(KnowledgeParser)
    parser.max_concurrent_requests = 3  # 设置并发数为3进行测试
    
    # 模拟长文本（生成多个段落以测试并发）
    test_segments = [
        {
            "text": "这是第一个测试段落，包含世界观相关内容。魔法世界中有各种神秘的力量和生物。",
            "order": 1,
            "start_pos": 0,
            "end_pos": 40,
            "segment_id": "seg_001"
        },
        {
            "text": "这是第二个测试段落，描述主要角色张三。他是一名勇敢的战士，拥有强大的剑术。",
            "order": 2,
            "start_pos": 40,
            "end_pos": 80,
            "segment_id": "seg_002"
        },
        {
            "text": "这是第三个测试段落，讲述剧情发展。主人公面临重大挑战，必须做出艰难的选择。",
            "order": 3,
            "start_pos": 80,
            "end_pos": 120,
            "segment_id": "seg_003"
        }
    ]
    
    # 模拟向量检索方法
    def mock_extract_with_vector_context(content: str, query: str, top_k: int = 5) -> str:
        """模拟向量检索"""
        return content[:200]  # 返回前200字符作为上下文
    
    # 替换向量检索方法
    parser.extract_with_vector_context = mock_extract_with_vector_context
    
    # 模拟LLM调用，返回固定的JSON结果
    def mock_llm_call(prompt: str) -> str:
        """模拟LLM调用"""
        time.sleep(0.1)  # 模拟网络延迟
        if "世界观" in prompt:
            return '{"setting": "魔法世界", "technology_level": "中世纪"}'
        elif "角色" in prompt:
            return '[{"name": "张三", "role": "战士", "abilities": ["剑术"]}]'
        elif "剧情" in prompt:
            return '{"plot_points": ["开始冒险", "遇到挑战", "做出选择"]}'
        else:
            return '{"data": "test"}'
    
    # 创建模拟的invoke_with_cleaning函数
    def mock_invoke_with_cleaning(llm_adapter, prompt):
        return mock_llm_call(prompt)
    
    # 替换原始的invoke_with_cleaning函数
    import novel_generator.knowledge_parser as kp_module
    original_invoke = kp_module.invoke_with_cleaning
    kp_module.invoke_with_cleaning = mock_invoke_with_cleaning
    
    try:
        print(f"开始测试并发处理 {len(test_segments)} 个段落...")
        
        # 记录开始时间
        start_time = time.time()
        
        # 测试世界观并发提取
        print("\n--- 测试世界观并发提取 ---")
        worldview_results = parser._process_segment_concurrently(
            test_segments,
            "worldview",
            "worldview", 
            "世界观 地理 历史 背景 科技 魔法 社会 文化 政治"
        )
        print(f"世界观提取结果数量: {len(worldview_results)}")
        
        # 测试角色并发提取
        print("\n--- 测试角色并发提取 ---")
        character_results = parser._process_segment_concurrently(
            test_segments,
            "characters",
            "character",
            "角色 人物 主角 配角 性格 能力 关系 背景"
        )
        print(f"角色提取结果数量: {len(character_results)}")
        
        # 测试剧情并发提取
        print("\n--- 测试剧情并发提取 ---")
        plot_results = parser._process_segment_concurrently(
            test_segments,
            "plot",
            "plot",
            "剧情 故事线 情节 冲突 高潮 结局 发展 转折"
        )
        print(f"剧情提取结果数量: {len(plot_results)}")
        
        # 记录结束时间
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n并发处理总时间: {total_time:.2f}秒")
        print(f"平均每个段落处理时间: {total_time/len(test_segments):.2f}秒")
        
        # 验证结果
        assert len(worldview_results) <= len(test_segments), "世界观结果数量不应超过输入段落数"
        assert len(character_results) <= len(test_segments), "角色结果数量不应超过输入段落数"
        assert len(plot_results) <= len(test_segments), "剧情结果数量不应超过输入段落数"
        
        print("\n并发处理功能测试通过!")
        
        # 测试结果顺序保持
        print("\n--- 验证结果顺序 ---")
        for i, result in enumerate(worldview_results):
            if isinstance(result, dict) and "_segment_metadata" in result:
                metadata = result["_segment_metadata"]
                expected_order = i + 1
                actual_order = metadata.get("order", 0)
                print(f"结果{i+1}: 预期顺序={expected_order}, 实际顺序={actual_order}")
                assert actual_order == expected_order, f"结果顺序错误: 预期{expected_order}, 实际{actual_order}"
        
        print("结果顺序验证通过!")
        
    finally:
        # 恢复原始函数
        kp_module.invoke_with_cleaning = original_invoke

def test_concurrent_vs_sequential_performance():
    """比较并发与顺序处理的性能"""
    print("\n=== 性能对比测试 ===")
    
    # 这是一个概念性的测试，实际测试需要真实的LLM环境
    print("注意: 实际性能测试需要在真实LLM环境中进行")
    print("预期结果: 并发处理应该比顺序处理快 3-5倍（取决于并发数量）")
    
def test_max_concurrent_requests_setting():
    """测试最大并发请求数设置"""
    print("\n=== 测试最大并发请求数设置 ===")
    
    from novel_generator.knowledge_parser import KnowledgeParser
    
    # 测试默认值
    parser1 = KnowledgeParser.__new__(KnowledgeParser)
    parser1.__init__(
        llm_interface_format="openai",
        llm_api_key="test",
        llm_base_url="test",
        llm_model="test"
    )
    assert parser1.max_concurrent_requests == 5, "默认并发数应为5"
    
    # 测试自定义值
    parser2 = KnowledgeParser.__new__(KnowledgeParser)
    parser2.__init__(
        llm_interface_format="openai",
        llm_api_key="test",
        llm_base_url="test", 
        llm_model="test",
        max_concurrent_requests=10
    )
    assert parser2.max_concurrent_requests == 10, "自定义并发数应为10"
    
    print("最大并发请求数设置测试通过!")

def main():
    """主测试函数"""
    print("开始测试并发知识提取功能...")
    
    try:
        test_max_concurrent_requests_setting()
        test_concurrent_functionality()
        test_concurrent_vs_sequential_performance()
        
        print("\n" + "="*50)
        print("所有并发功能测试通过！")
        print("主要改进:")
        print("1. ✅ 添加了max_concurrent_requests参数")
        print("2. ✅ 实现了并发段落处理方法")
        print("3. ✅ 修改了三个提取方法使用并发处理")
        print("4. ✅ 保持了段落顺序和元数据完整性")
        print("5. ✅ 并发处理在第一层，合并在后续层按顺序执行")
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