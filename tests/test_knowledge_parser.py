# tests/test_knowledge_parser.py
# -*- coding: utf-8 -*-
"""
知识解析模块单元测试
"""
import sys
import os
import unittest
import json
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from novel_generator.knowledge_parser import KnowledgeParser, parse_knowledge_from_file
from novel_generator.knowledge_structures import (
    WorldView, Character, PlotOutline, StructuredKnowledge,
    create_worldview_element, create_character, create_plot_point
)


class TestKnowledgeParser(unittest.TestCase):
    """知识解析器测试类"""

    def setUp(self):
        """测试前置设置"""
        self.mock_llm_adapter = Mock()
        self.mock_embedding_adapter = Mock()
        
        # 创建测试用的知识解析器
        self.parser = KnowledgeParser(
            llm_interface_format="OpenAI",
            llm_api_key="test_api_key",
            llm_base_url="http://localhost:8080",
            llm_model="test_model",
            embedding_adapter=self.mock_embedding_adapter,
            filepath="/test/path"
        )
        
        # 替换为mock对象
        self.parser.llm_adapter = self.mock_llm_adapter
        
    def test_init_parser(self):
        """测试解析器初始化"""
        self.assertIsNotNone(self.parser)
        self.assertEqual(self.parser.filepath, "/test/path")
        self.assertEqual(self.parser.embedding_adapter, self.mock_embedding_adapter)
        
    def test_preprocess_text(self):
        """测试文本预处理"""
        # 测试正常文本
        text = "这是一个   测试文本\n\n    带有多余空格"
        result = self.parser.preprocess_text(text)
        expected = "这是一个 测试文本 带有多余空格"
        self.assertEqual(result, expected)
        
        # 测试空文本
        self.assertEqual(self.parser.preprocess_text(""), "")
        self.assertEqual(self.parser.preprocess_text("   "), "")
        
        # 测试超长文本
        long_text = "测试" * 30000
        result = self.parser.preprocess_text(long_text)
        self.assertTrue(len(result) <= 50003)  # 50000 + "..."
        
    @patch('novel_generator.knowledge_parser.invoke_with_cleaning')
    def test_extract_worldview_success(self, mock_invoke):
        """测试世界观提取成功"""
        # 模拟返回的JSON数据
        mock_worldview_data = {
            "name": "测试世界",
            "overview": "这是一个测试世界",
            "geography": [
                {
                    "category": "地理",
                    "name": "测试大陆",
                    "description": "一个虚构的大陆",
                    "importance": "high",
                    "tags": ["大陆", "主要"]
                }
            ],
            "history": [],
            "technology": [],
            "society": [],
            "culture": [],
            "magic_system": [],
            "politics": [],
            "economy": [],
            "other_elements": []
        }
        
        mock_invoke.return_value = json.dumps(mock_worldview_data, ensure_ascii=False)
        
        content = "这里是测试世界的描述文本..."
        result = self.parser.extract_worldview(content)
        
        self.assertEqual(result["name"], "测试世界")
        self.assertEqual(len(result["geography"]), 1)
        self.assertEqual(result["geography"][0]["name"], "测试大陆")
        
    @patch('novel_generator.knowledge_parser.invoke_with_cleaning')
    def test_extract_worldview_empty_response(self, mock_invoke):
        """测试世界观提取返回空结果"""
        mock_invoke.return_value = ""
        
        content = "测试内容"
        result = self.parser.extract_worldview(content)
        
        self.assertEqual(result, {})
        
    @patch('novel_generator.knowledge_parser.invoke_with_cleaning')  
    def test_extract_characters_success(self, mock_invoke):
        """测试角色提取成功"""
        mock_characters_data = [
            {
                "name": "测试角色",
                "role": "主角",
                "gender": "男",
                "age": "25",
                "appearance": "高大威猛",
                "personality": ["勇敢", "善良"],
                "abilities": [
                    {
                        "name": "剑术",
                        "description": "精通剑术",
                        "level": "advanced",
                        "category": "武力"
                    }
                ],
                "background": "来自小村庄的青年",
                "motivation": "拯救世界",
                "arc_development": "从普通人成长为英雄",
                "relationships": [
                    {
                        "target_character": "测试伙伴",
                        "relationship_type": "朋友",
                        "relationship_strength": "strong",
                        "description": "生死之交",
                        "history": "一起长大的朋友"
                    }
                ],
                "important_items": ["传说之剑"],
                "catchphrases": ["正义必胜"],
                "weaknesses": ["过于冲动"],
                "secrets": ["拥有神秘血统"],
                "notes": "主角设定"
            }
        ]
        
        mock_invoke.return_value = json.dumps(mock_characters_data, ensure_ascii=False)
        
        content = "这里是角色描述文本..."
        result = self.parser.extract_characters(content)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "测试角色")
        self.assertEqual(result[0]["role"], "主角")
        self.assertEqual(len(result[0]["abilities"]), 1)
        
    @patch('novel_generator.knowledge_parser.invoke_with_cleaning')
    def test_extract_plot_outline_success(self, mock_invoke):
        """测试剧情大纲提取成功"""
        mock_plot_data = {
            "title": "测试小说",
            "genre": "奇幻",
            "theme": "成长与友谊",
            "premise": "一个普通青年的冒险故事",
            "main_storyline": "主角踏上拯救世界的旅程",
            "plot_structure": "三幕式",
            "main_plot_lines": [
                {
                    "name": "主线剧情",
                    "description": "拯救世界的主要故事线",
                    "main_characters": ["测试角色"],
                    "plot_points": [
                        {
                            "name": "启程",
                            "description": "离开家乡开始冒险",
                            "chapter_range": "第1-2章",
                            "characters_involved": ["测试角色"],
                            "importance": "high",
                            "plot_type": "开始",
                            "consequences": "踏上冒险之路"
                        }
                    ],
                    "status": "planned"
                }
            ],
            "sub_plot_lines": [],
            "major_conflicts": [
                {
                    "name": "善恶对立",
                    "type": "道德",
                    "description": "正义与邪恶的冲突",
                    "parties_involved": ["主角", "反派"],
                    "stakes": "世界的命运",
                    "resolution_method": "最终决战",
                    "status": "unresolved"
                }
            ],
            "key_plot_points": [],
            "inciting_incident": "家乡被毁",
            "plot_point_1": "获得力量",
            "midpoint": "发现真相",
            "plot_point_2": "面临选择",
            "climax": "最终决战",
            "resolution": "恢复和平",
            "themes": ["成长", "友谊", "勇气"],
            "symbols": ["剑", "光明"],
            "motifs": ["旅程", "成长"]
        }
        
        mock_invoke.return_value = json.dumps(mock_plot_data, ensure_ascii=False)
        
        content = "这里是剧情大纲文本..."
        result = self.parser.extract_plot_outline(content)
        
        self.assertEqual(result["title"], "测试小说")
        self.assertEqual(result["genre"], "奇幻")
        self.assertEqual(len(result["main_plot_lines"]), 1)
        self.assertEqual(len(result["major_conflicts"]), 1)
        
    def test_analyze_relationships_empty_characters(self):
        """测试空角色列表的关系分析"""
        result = self.parser.analyze_relationships([])
        self.assertEqual(result, {})
        
    def test_generate_structure(self):
        """测试结构化数据生成"""
        worldview = {"name": "测试世界"}
        characters = [{"name": "测试角色"}]
        plot_outline = {"title": "测试小说"}
        relationships = {"relationships": []}
        
        result = self.parser.generate_structure(
            worldview, characters, plot_outline, relationships
        )
        
        self.assertIn("metadata", result)
        self.assertIn("worldview", result)
        self.assertIn("characters", result)
        self.assertIn("plot_outline", result)
        self.assertIn("relationships", result)
        self.assertIn("statistics", result)
        
        self.assertEqual(result["statistics"]["character_count"], 1)
        
    @patch('builtins.open', create=True)
    @patch('json.dump')
    def test_save_extracted_knowledge(self, mock_json_dump, mock_open):
        """测试保存提取的知识"""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        test_data = {"test": "data"}
        result = self.parser.save_extracted_knowledge(test_data, "test.json")
        
        self.assertTrue(result)
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once_with(
            test_data, mock_file, ensure_ascii=False, indent=2
        )
        
    def test_save_extracted_knowledge_no_filepath(self):
        """测试没有文件路径时保存失败"""
        parser = KnowledgeParser(
            llm_interface_format="OpenAI",
            llm_api_key="test_key",
            llm_base_url="http://test",
            llm_model="test",
            filepath=""
        )
        
        result = parser.save_extracted_knowledge({"test": "data"})
        self.assertFalse(result)
        

class TestKnowledgeStructures(unittest.TestCase):
    """知识结构测试类"""

    def test_create_worldview_element(self):
        """测试世界观要素创建"""
        element = create_worldview_element(
            category="地理",
            name="测试山脉",
            description="一座高耸的山脉",
            importance="high",
            tags=["山脉", "地标"]
        )
        
        self.assertEqual(element.category, "地理")
        self.assertEqual(element.name, "测试山脉")
        self.assertEqual(element.importance, "high")
        self.assertEqual(len(element.tags), 2)
        
    def test_create_character(self):
        """测试角色创建"""
        character = create_character(
            name="测试角色",
            role="主角",
            gender="男",
            age=25
        )
        
        self.assertEqual(character.name, "测试角色")
        self.assertEqual(character.role, "主角")
        self.assertEqual(character.gender, "男")
        self.assertEqual(character.age, 25)
        
    def test_character_relationships(self):
        """测试角色关系功能"""
        from novel_generator.knowledge_structures import CharacterRelationship
        
        character = create_character("角色A")
        relationship = CharacterRelationship(
            target_character="角色B",
            relationship_type="朋友",
            relationship_strength="strong",
            description="好友关系"
        )
        
        character.add_relationship(relationship)
        
        found_rel = character.get_relationship_with("角色B")
        self.assertIsNotNone(found_rel)
        self.assertEqual(found_rel.relationship_type, "朋友")
        
        # 测试不存在的关系
        not_found = character.get_relationship_with("角色C")
        self.assertIsNone(not_found)
        
    def test_structured_knowledge(self):
        """测试结构化知识类"""
        knowledge = StructuredKnowledge()
        
        # 测试添加角色
        character = create_character("测试角色", "主角")
        knowledge.add_character(character)
        
        self.assertEqual(len(knowledge.characters), 1)
        self.assertEqual(knowledge.metadata.total_characters, 1)
        
        # 测试获取角色
        found_char = knowledge.get_character_by_name("测试角色")
        self.assertIsNotNone(found_char)
        self.assertEqual(found_char.name, "测试角色")
        
        # 测试转换为字典
        data_dict = knowledge.to_dict()
        self.assertIn("metadata", data_dict)
        self.assertIn("characters", data_dict)
        
    def test_structured_knowledge_serialization(self):
        """测试结构化知识序列化"""
        knowledge = StructuredKnowledge()
        character = create_character("测试角色")
        knowledge.add_character(character)
        
        # 测试JSON序列化
        json_str = knowledge.to_json()
        self.assertIsInstance(json_str, str)
        
        # 验证JSON可以被解析
        parsed_data = json.loads(json_str)
        self.assertIn("characters", parsed_data)
        self.assertEqual(len(parsed_data["characters"]), 1)


class TestIntegrationCases(unittest.TestCase):
    """集成测试用例"""

    @patch('novel_generator.knowledge_parser.read_file')
    @patch('novel_generator.knowledge_parser.KnowledgeParser')
    def test_parse_knowledge_from_file_success(self, mock_parser_class, mock_read_file):
        """测试从文件解析知识成功"""
        # 设置模拟数据
        mock_read_file.return_value = "测试文件内容"
        
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        
        mock_parser.extract_worldview.return_value = {"name": "测试世界"}
        mock_parser.extract_characters.return_value = [{"name": "测试角色"}]
        mock_parser.extract_plot_outline.return_value = {"title": "测试小说"}
        mock_parser.analyze_relationships.return_value = {"relationships": []}
        mock_parser.generate_structure.return_value = {"test": "structure"}
        mock_parser.save_extracted_knowledge.return_value = True
        
        # 执行测试
        result = parse_knowledge_from_file(
            file_path="/test/file.txt",
            llm_interface_format="OpenAI",
            llm_api_key="test_key",
            llm_base_url="http://test",
            llm_model="test_model",
            filepath="/test/output"
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        mock_read_file.assert_called_once_with("/test/file.txt")
        mock_parser.extract_worldview.assert_called_once()
        mock_parser.extract_characters.assert_called_once()
        mock_parser.extract_plot_outline.assert_called_once()
        
    @patch('novel_generator.knowledge_parser.read_file')
    def test_parse_knowledge_from_file_empty_content(self, mock_read_file):
        """测试文件内容为空的情况"""
        mock_read_file.return_value = ""
        
        result = parse_knowledge_from_file(
            file_path="/test/empty_file.txt",
            llm_interface_format="OpenAI", 
            llm_api_key="test_key",
            llm_base_url="http://test",
            llm_model="test_model",
            filepath="/test/output"
        )
        
        self.assertIsNone(result)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestKnowledgeParser))
    suite.addTests(loader.loadTestsFromTestCase(TestKnowledgeStructures))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationCases))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    if not success:
        sys.exit(1)
    print("\n所有测试通过！ ✅")