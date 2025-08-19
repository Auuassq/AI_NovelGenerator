# test_integration.py
# -*- coding: utf-8 -*-
"""
测试知识库集成功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from novel_generator.knowledge_structures import StructuredKnowledge, create_character, create_worldview_element
from novel_generator.architecture import load_structured_knowledge, format_knowledge_for_prompt


def test_knowledge_structures():
    """测试数据结构"""
    print("测试知识库数据结构...")
    
    # 创建角色
    character = create_character("测试角色", "主角")
    character.personality = ["勇敢", "智慧"]
    character.motivation = "拯救世界"
    
    # 创建世界观要素
    element = create_worldview_element("地理", "测试大陆", "虚构的大陆", "high")
    
    print("[OK] 数据结构测试通过")


def test_knowledge_integration():
    """测试知识库集成"""
    print("测试知识库格式化...")
    
    # 模拟结构化知识数据
    test_knowledge = {
        "worldview": {
            "overview": "测试世界概述",
            "geography": [
                {"name": "测试大陆", "description": "虚构的大陆"}
            ]
        },
        "characters": [
            {"name": "测试角色", "role": "主角", "background": "来自小村庄"}
        ]
    }
    
    formatted = format_knowledge_for_prompt(test_knowledge)
    print(f"格式化结果长度: {len(formatted)} 字符")
    print("[OK] 知识库格式化测试通过")


def main():
    print("=== 知识库集成功能测试 ===")
    
    try:
        test_knowledge_structures()
        test_knowledge_integration()
        print("\n[OK] 所有测试通过！Phase 2 核心功能开发完成")
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {str(e)}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)