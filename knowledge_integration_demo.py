# -*- coding: utf-8 -*-
"""
知识库集成功能演示脚本
展示知识库如何与架构生成集成
"""
import os
import json
from novel_generator.knowledge_structures import StructuredKnowledge
from novel_generator.architecture import load_structured_knowledge, format_knowledge_for_prompt

def create_demo_knowledge():
    """创建演示用的知识库数据"""
    demo_knowledge = {
        "worldview": {
            "name": "仙侠世界",
            "overview": "一个修仙者与凡人共存的奇幻世界，有着完整的修炼体系和门派势力。",
            "geography": [
                {
                    "name": "青云山脉",
                    "description": "连绵千里的灵气充沛山脉，是各大仙门的聚集地。",
                    "importance": "high"
                },
                {
                    "name": "流云城",
                    "description": "修仙者与凡人交易的繁华城池，位于青云山脉脚下。",
                    "importance": "medium"
                }
            ],
            "magic_system": [
                {
                    "name": "五行修炼法",
                    "description": "通过吸收天地间的五行灵气进行修炼的方法。",
                    "importance": "high"
                }
            ]
        },
        "characters": [
            {
                "name": "林轩",
                "role": "主角",
                "background": "出身平凡的少年，意外获得古老传承，踏上修仙之路。",
                "personality": ["坚毅", "善良", "有责任感"],
                "abilities": ["五行灵根", "古老传承"],
                "relationships": [],
                "motivation": "保护家人，追求更高境界的修炼。"
            },
            {
                "name": "雪莲仙子",
                "role": "导师",
                "background": "青云门的长老，修为高深，性格清冷。",
                "personality": ["清冷", "严厉", "护短"],
                "abilities": ["冰系法术", "剑术"],
                "relationships": [{"target": "林轩", "type": "师徒"}],
                "motivation": "培养优秀弟子，重振青云门声望。"
            }
        ],
        "plot_outline": {
            "title": "修仙传说",
            "theme": "成长与责任",
            "main_storyline": "平凡少年获得传承，在修仙路上不断成长，最终承担起保护世界的责任。",
            "major_conflicts": [
                {
                    "name": "门派危机",
                    "description": "青云门遭受邪修势力威胁，需要新生力量来守护。",
                    "type": "external"
                },
                {
                    "name": "内心挣扎",
                    "description": "主角在力量与责任之间的内心冲突和成长。",
                    "type": "internal"
                }
            ]
        },
        "statistics": {
            "worldview_elements": 3,
            "character_count": 2,
            "plot_points": 2,
            "relationship_count": 1
        }
    }
    return demo_knowledge

def demo_knowledge_integration():
    """演示知识库集成功能"""
    print("=== 知识库集成功能演示 ===")
    
    # 创建演示数据
    print("1. 创建演示用知识库数据...")
    demo_knowledge = create_demo_knowledge()
    
    # 保存到文件
    demo_dir = "demo_project"
    os.makedirs(demo_dir, exist_ok=True)
    knowledge_file = os.path.join(demo_dir, "extracted_knowledge.json")
    
    with open(knowledge_file, 'w', encoding='utf-8') as f:
        json.dump(demo_knowledge, f, ensure_ascii=False, indent=2)
    print(f"   知识库数据已保存到: {knowledge_file}")
    
    # 演示加载功能
    print("\n2. 演示知识库加载功能...")
    loaded_knowledge = load_structured_knowledge(demo_dir)
    if loaded_knowledge:
        print("   [OK] 成功加载知识库数据")
        print(f"   - 世界观要素: {loaded_knowledge.get('statistics', {}).get('worldview_elements', 0)}")
        print(f"   - 角色数量: {loaded_knowledge.get('statistics', {}).get('character_count', 0)}")
        print(f"   - 情节点: {loaded_knowledge.get('statistics', {}).get('plot_points', 0)}")
    else:
        print("   [ERROR] 加载知识库失败")
        return
    
    # 演示格式化功能
    print("\n3. 演示知识库格式化功能...")
    formatted_prompt = format_knowledge_for_prompt(loaded_knowledge)
    print(f"   格式化后的提示词长度: {len(formatted_prompt)} 字符")
    print("   格式化内容预览:")
    print("   " + "="*50)
    preview = formatted_prompt[:300] + "..." if len(formatted_prompt) > 300 else formatted_prompt
    print(f"   {preview}")
    print("   " + "="*50)
    
    # 清理演示文件
    print("\n4. 清理演示文件...")
    try:
        os.remove(knowledge_file)
        os.rmdir(demo_dir)
        print("   [OK] 演示文件已清理")
    except:
        print("   [WARNING] 清理演示文件时出现问题")
    
    print("\n=== 演示完成 ===")
    print("\n使用说明:")
    print("1. 在 '📚 知识库' 标签页导入并解析文档")
    print("2. 点击 '🎯 用于架构生成' 准备知识库")
    print("3. 在 '小说设定' 标签页勾选 '使用已有知识库辅助生成架构'")
    print("4. 生成架构时会自动融入知识库内容")

if __name__ == "__main__":
    demo_knowledge_integration()