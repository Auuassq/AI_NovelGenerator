# examples/knowledge_parser_demo.py
# -*- coding: utf-8 -*-
"""
知识解析功能演示脚本
演示如何使用新的知识库智能解析功能
"""
import os
import sys
import json

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from novel_generator.knowledge_parser import KnowledgeParser
from novel_generator.knowledge_structures import StructuredKnowledge


def demo_knowledge_parsing():
    """演示知识解析功能"""
    print("=== AI小说生成器 - 知识库智能解析演示 ===\n")
    
    # 示例知识库内容
    demo_content = """
    《星际迷航：新纪元》设定文档
    
    == 世界观设定 ==
    
    地理环境：
    - 星系联邦：由数百个星球组成的政治联盟，总部位于地球
    - 克林贡帝国：军事化的外星种族，以荣誉和战斗为核心价值
    - 新星城：联邦最重要的太空站，位于银河系中心附近
    
    历史背景：
    - 2387年：传送门技术发明，开启星际旅行新纪元
    - 2401年：第一次星际战争爆发，联邦与克林贡帝国对立
    - 2420年：和平协议签署，建立星际贸易网络
    
    科技水平：
    - 量子传送技术：可实现瞬间星际传输
    - 思维链接设备：允许不同种族间的直接意识交流
    - 反重力引擎：使星舰能够进行超光速航行
    
    == 角色设定 ==
    
    詹姆斯·柯克：
    - 身份：星舰企业号船长
    - 年龄：35岁，人类男性
    - 性格：勇敢、冲动、富有领导魅力，但有时过于鲁莽
    - 能力：卓越的战术思维和指挥能力，精通多种格斗技巧
    - 背景：来自爱荷华农场，年轻时父亲死于星际战争
    - 目标：维护银河系和平，探索未知星域
    - 装备：联邦标准相位器，船长徽章
    
    斯波克：
    - 身份：企业号大副，瓦肯族与人类混血
    - 年龄：127岁（按瓦肯族标准为青年）
    - 性格：逻辑至上，冷静理性，但内心深藏情感冲突
    - 能力：瓦肯族心灵感应，超人的计算和分析能力
    - 背景：父亲是瓦肯族大使，母亲是人类科学家
    - 与柯克关系：最信任的副手和朋友，经常在理性和情感间为柯克提供平衡
    
    莱昂纳德·麦考伊：
    - 身份：企业号首席医官
    - 性格：急躁、直言不讳，但心地善良，医者仁心
    - 能力：顶尖的医疗技术，对外星生物学有深入研究
    - 与柯克和斯波克关系：三人形成铁三角，经常调和柯克和斯波克的分歧
    
    == 剧情大纲 ==
    
    故事类型：科幻冒险
    主题：友谊、探索、不同文明间的理解与冲突
    
    主线剧情：
    企业号在探索新星域时发现了一个古老文明的遗迹，其中隐藏着能够改变银河系格局的强大技术。然而，这项技术的激活引来了沉睡千年的古老敌人——"虚无吞噬者"。柯克船长必须团结各种族，包括昔日的敌人克林贡族，共同对抗这个威胁全宇宙的存在。
    
    关键冲突：
    1. 联邦与克林贡的历史仇恨 vs 面对共同威胁的必要合作
    2. 柯克的冲动决策 vs 斯波克的逻辑分析
    3. 保存古老文明遗产 vs 为了银河系安全而摧毁危险技术
    
    重要情节点：
    - 发现古老遗迹（第1-3章）
    - 激活古老技术，唤醒虚无吞噬者（第4-5章）
    - 寻求克林贡族帮助，组建联合舰队（第6-8章）
    - 最终决战，牺牲与胜利（第9-10章）
    
    结局：虽然击败了虚无吞噬者，但柯克船长为了拯救银河系付出了巨大牺牲，这改变了所有人对英雄主义的理解。
    """
    
    print("演示内容：《星际迷航：新纪元》设定文档")
    print("-" * 50)
    
    # 注意：这里使用演示配置，实际使用时需要配置真实的API
    parser = KnowledgeParser(
        llm_interface_format="OpenAI",  # 演示配置
        llm_api_key="demo_api_key",
        llm_base_url="http://demo.example.com",
        llm_model="demo_model",
        filepath="./demo_output"
    )
    
    print("1. 文本预处理...")
    processed_content = parser.preprocess_text(demo_content)
    print(f"   原始长度: {len(demo_content)} 字符")
    print(f"   处理后长度: {len(processed_content)} 字符")
    
    print("\n2. 演示数据结构创建...")
    
    # 创建演示的结构化知识
    from novel_generator.knowledge_structures import (
        StructuredKnowledge, WorldView, Character, PlotOutline,
        create_worldview_element, create_character, create_plot_point, create_conflict
    )
    
    # 创建世界观
    worldview = WorldView(
        name="星际迷航：新纪元世界观",
        overview="一个多种族共存的星际文明时代"
    )
    
    # 添加地理要素
    worldview.geography.append(
        create_worldview_element("地理", "星系联邦", "由数百个星球组成的政治联盟", "high", ["政治", "联盟"])
    )
    worldview.geography.append(
        create_worldview_element("地理", "克林贡帝国", "军事化的外星种族领域", "high", ["军事", "外星种族"])
    )
    
    # 添加科技要素
    worldview.technology.append(
        create_worldview_element("科技", "量子传送技术", "瞬间星际传输技术", "high", ["传输", "量子"])
    )
    
    # 创建角色
    kirk = create_character(
        name="詹姆斯·柯克",
        role="主角",
        gender="男",
        age=35,
        appearance="身材高大，金发蓝眼，具有领导者气质",
        background="来自爱荷华农场，年轻时父亲死于星际战争"
    )
    kirk.personality = ["勇敢", "冲动", "富有魅力", "鲁莽"]
    kirk.motivation = "维护银河系和平，探索未知星域"
    kirk.important_items = ["联邦标准相位器", "船长徽章"]
    
    spock = create_character(
        name="斯波克",
        role="配角",
        gender="男", 
        age="127",
        background="瓦肯族与人类混血，父亲是瓦肯族大使"
    )
    spock.personality = ["逻辑", "冷静", "理性", "情感冲突"]
    
    # 创建剧情大纲
    plot_outline = PlotOutline(
        title="星际迷航：新纪元",
        genre="科幻冒险",
        theme="友谊、探索、不同文明间的理解与冲突",
        main_storyline="企业号发现古老文明遗迹，激活技术唤醒古老敌人，团结各族对抗威胁"
    )
    
    # 添加情节点
    plot_outline.key_plot_points.append(
        create_plot_point("发现遗迹", "在新星域发现古老文明遗迹", chapter_range="第1-3章", importance="high")
    )
    plot_outline.key_plot_points.append(
        create_plot_point("唤醒敌人", "激活古老技术唤醒虚无吞噬者", chapter_range="第4-5章", importance="critical")
    )
    
    # 添加冲突
    plot_outline.major_conflicts.append(
        create_conflict("种族仇恨", "人际", "联邦与克林贡的历史仇恨", 
                       parties_involved=["联邦", "克林贡帝国"], stakes="银河系和平")
    )
    
    # 创建结构化知识对象
    structured_knowledge = StructuredKnowledge(
        worldview=worldview,
        characters=[kirk, spock],
        plot_outline=plot_outline
    )
    structured_knowledge.update_metadata()
    
    print("   ✅ 结构化知识对象创建完成")
    print(f"   - 世界观要素数量: {structured_knowledge.metadata.total_worldview_elements}")
    print(f"   - 角色数量: {structured_knowledge.metadata.total_characters}")  
    print(f"   - 情节点数量: {structured_knowledge.metadata.total_plot_points}")
    
    print("\n3. 数据序列化演示...")
    
    # 转换为JSON
    json_data = structured_knowledge.to_json()
    print(f"   JSON数据长度: {len(json_data)} 字符")
    
    # 保存到文件（演示）
    demo_file = "demo_structured_knowledge.json"
    if structured_knowledge.save_to_file(demo_file):
        print(f"   ✅ 已保存到文件: {demo_file}")
        
        # 加载验证
        loaded_knowledge = StructuredKnowledge.load_from_file(demo_file)
        if loaded_knowledge:
            print(f"   ✅ 文件加载验证成功，角色数量: {len(loaded_knowledge.characters)}")
        
        # 清理演示文件
        try:
            os.remove(demo_file)
            print("   ✅ 演示文件已清理")
        except:
            pass
    
    print("\n4. 数据结构功能演示...")
    
    # 演示角色关系功能
    from novel_generator.knowledge_structures import CharacterRelationship
    
    relationship = CharacterRelationship(
        target_character="斯波克",
        relationship_type="朋友",
        relationship_strength="very_strong",
        description="最信任的副手和朋友",
        history="多年共事建立的深厚友谊"
    )
    kirk.add_relationship(relationship)
    
    found_rel = kirk.get_relationship_with("斯波克")
    if found_rel:
        print(f"   ✅ 角色关系功能正常: {kirk.name} 与 {found_rel.target_character} 的关系是 {found_rel.relationship_type}")
    
    # 演示世界观要素查询
    geography_elements = structured_knowledge.worldview.get_elements_by_category("地理")
    print(f"   ✅ 世界观查询功能正常: 找到 {len(geography_elements)} 个地理要素")
    
    print(f"\n=== 演示完成 ===")
    print("✅ Phase 1 基础架构搭建成功！")
    print("\n下一步: Phase 2 - 核心解析功能开发")
    print("- 实现与真实LLM的集成")
    print("- 优化提示词和解析逻辑") 
    print("- 添加错误处理和重试机制")


if __name__ == "__main__":
    demo_knowledge_parsing()