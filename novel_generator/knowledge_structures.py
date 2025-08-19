# novel_generator/knowledge_structures.py  
# -*- coding: utf-8 -*-
"""
知识库数据结构定义
定义世界观、角色、剧情大纲等结构化数据类
"""
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Union
from datetime import datetime


@dataclass
class WorldViewElement:
    """世界观单个要素"""
    category: str           # 要素类别 (地理/历史/科技/社会/文化等)
    name: str              # 要素名称
    description: str       # 详细描述  
    importance: str        # 重要程度 (high/medium/low)
    tags: List[str] = field(default_factory=list)  # 标签
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass  
class WorldView:
    """世界观数据结构"""
    name: str = ""                                    # 世界观名称
    overview: str = ""                               # 总体概述
    geography: List[WorldViewElement] = field(default_factory=list)    # 地理设定
    history: List[WorldViewElement] = field(default_factory=list)      # 历史背景  
    technology: List[WorldViewElement] = field(default_factory=list)   # 科技水平
    society: List[WorldViewElement] = field(default_factory=list)      # 社会结构
    culture: List[WorldViewElement] = field(default_factory=list)      # 文化设定
    magic_system: List[WorldViewElement] = field(default_factory=list) # 魔法/超能力体系
    politics: List[WorldViewElement] = field(default_factory=list)     # 政治结构
    economy: List[WorldViewElement] = field(default_factory=list)      # 经济体系
    other_elements: List[WorldViewElement] = field(default_factory=list) # 其他要素
    
    def get_all_elements(self) -> List[WorldViewElement]:
        """获取所有世界观要素"""
        all_elements = []
        all_elements.extend(self.geography)
        all_elements.extend(self.history)  
        all_elements.extend(self.technology)
        all_elements.extend(self.society)
        all_elements.extend(self.culture)
        all_elements.extend(self.magic_system)
        all_elements.extend(self.politics)
        all_elements.extend(self.economy)
        all_elements.extend(self.other_elements)
        return all_elements
    
    def get_elements_by_category(self, category: str) -> List[WorldViewElement]:
        """根据类别获取要素"""
        category_map = {
            "地理": self.geography,
            "历史": self.history,
            "科技": self.technology,
            "社会": self.society,
            "文化": self.culture,
            "魔法": self.magic_system,
            "政治": self.politics,
            "经济": self.economy,
            "其他": self.other_elements
        }
        return category_map.get(category, [])
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class CharacterAbility:
    """角色能力"""
    name: str              # 能力名称
    description: str       # 能力描述
    level: str            # 能力等级 (beginner/intermediate/advanced/master)
    category: str = ""     # 能力分类 (武力/智力/魔法/社交等)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CharacterRelationship:
    """角色关系"""
    target_character: str   # 关系对象
    relationship_type: str  # 关系类型 (朋友/敌人/家人/恋人/师生等)  
    relationship_strength: str # 关系强度 (weak/moderate/strong/very_strong)
    description: str       # 关系描述
    history: str = ""      # 关系历史
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Character:
    """角色数据结构"""
    name: str                                         # 角色姓名
    role: str = ""                                   # 角色定位 (主角/配角/反派等)
    gender: str = ""                                 # 性别
    age: Union[int, str] = ""                        # 年龄
    appearance: str = ""                             # 外貌描述
    personality: List[str] = field(default_factory=list)      # 性格特征列表
    abilities: List[CharacterAbility] = field(default_factory=list) # 能力列表
    background: str = ""                             # 背景故事
    motivation: str = ""                             # 动机/目标
    arc_development: str = ""                        # 角色弧光发展
    relationships: List[CharacterRelationship] = field(default_factory=list) # 人物关系
    important_items: List[str] = field(default_factory=list)   # 重要物品
    catchphrases: List[str] = field(default_factory=list)     # 口头禅/名言
    weaknesses: List[str] = field(default_factory=list)       # 弱点
    secrets: List[str] = field(default_factory=list)          # 秘密
    notes: str = ""                                  # 备注
    
    def get_relationship_with(self, character_name: str) -> Optional[CharacterRelationship]:
        """获取与指定角色的关系"""
        for rel in self.relationships:
            if rel.target_character == character_name:
                return rel
        return None
    
    def add_relationship(self, relationship: CharacterRelationship):
        """添加关系"""
        # 检查是否已存在该关系，如果存在则更新
        existing_rel = self.get_relationship_with(relationship.target_character)
        if existing_rel:
            self.relationships.remove(existing_rel)
        self.relationships.append(relationship)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class PlotPoint:
    """情节点"""
    name: str              # 情节点名称
    description: str       # 详细描述
    chapter_range: str = ""    # 涉及章节范围
    characters_involved: List[str] = field(default_factory=list) # 涉及角色
    importance: str = "medium"   # 重要程度 (low/medium/high/critical)
    plot_type: str = ""     # 情节类型 (冲突/转折/高潮/解决等)
    consequences: str = ""  # 后果/影响
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlotLine:
    """故事线"""
    name: str              # 故事线名称  
    description: str       # 描述
    main_characters: List[str] = field(default_factory=list) # 主要角色
    plot_points: List[PlotPoint] = field(default_factory=list) # 情节点
    status: str = "planned" # 状态 (planned/in_progress/completed)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Conflict:
    """冲突设置"""
    name: str              # 冲突名称
    type: str              # 冲突类型 (内在/人际/社会/自然/超自然)
    description: str       # 冲突描述
    parties_involved: List[str] = field(default_factory=list) # 冲突各方
    stakes: str = ""       # 冲突的赌注/后果
    resolution_method: str = "" # 解决方式
    status: str = "unresolved" # 状态 (unresolved/resolving/resolved)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlotOutline:
    """剧情大纲数据结构"""
    title: str = ""                                  # 作品标题
    genre: str = ""                                  # 类型
    theme: str = ""                                  # 主题
    premise: str = ""                                # 故事前提
    main_storyline: str = ""                         # 主故事线概述
    plot_structure: str = ""                         # 情节结构 (三幕式/英雄之旅等)
    
    # 核心要素
    main_plot_lines: List[PlotLine] = field(default_factory=list)    # 主要故事线
    sub_plot_lines: List[PlotLine] = field(default_factory=list)     # 副线故事
    major_conflicts: List[Conflict] = field(default_factory=list)    # 主要冲突
    key_plot_points: List[PlotPoint] = field(default_factory=list)   # 关键情节点
    
    # 结构化情节点
    inciting_incident: str = ""      # 激励事件
    plot_point_1: str = ""           # 情节点1
    midpoint: str = ""               # 中点
    plot_point_2: str = ""           # 情节点2  
    climax: str = ""                 # 高潮
    resolution: str = ""             # 结局
    
    # 主题要素
    themes: List[str] = field(default_factory=list)          # 主题列表
    symbols: List[str] = field(default_factory=list)         # 象征元素
    motifs: List[str] = field(default_factory=list)          # 主题母题
    
    def get_all_plot_points(self) -> List[PlotPoint]:
        """获取所有情节点"""
        all_points = list(self.key_plot_points)
        for storyline in self.main_plot_lines + self.sub_plot_lines:
            all_points.extend(storyline.plot_points)
        return all_points
    
    def get_characters_involved(self) -> List[str]:
        """获取所有涉及的角色"""
        characters = set()
        for conflict in self.major_conflicts:
            characters.update(conflict.parties_involved)
        for point in self.get_all_plot_points():
            characters.update(point.characters_involved)
        return list(characters)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class RelationshipNetwork:
    """关系网络"""
    characters: List[str] = field(default_factory=list)      # 角色列表
    relationships: List[Dict[str, Any]] = field(default_factory=list) # 关系列表
    relationship_groups: List[Dict[str, Any]] = field(default_factory=list) # 关系组
    
    def add_relationship(self, char1: str, char2: str, 
                        relationship_type: str, description: str = ""):
        """添加关系"""
        relationship = {
            "character1": char1,
            "character2": char2,  
            "relationship_type": relationship_type,
            "description": description,
            "bidirectional": True  # 是否双向关系
        }
        self.relationships.append(relationship)
        
        # 确保角色在列表中
        if char1 not in self.characters:
            self.characters.append(char1)
        if char2 not in self.characters:
            self.characters.append(char2)
    
    def get_character_relationships(self, character_name: str) -> List[Dict[str, Any]]:
        """获取指定角色的所有关系"""
        char_rels = []
        for rel in self.relationships:
            if rel["character1"] == character_name or rel["character2"] == character_name:
                char_rels.append(rel)
        return char_rels
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class KnowledgeMetadata:
    """知识库元数据"""
    extraction_time: str = ""         # 提取时间
    source_files: List[str] = field(default_factory=list)   # 源文件列表
    extraction_version: str = "1.0"   # 提取版本
    total_characters: int = 0          # 角色总数
    total_worldview_elements: int = 0  # 世界观要素总数
    total_plot_points: int = 0         # 情节点总数
    extraction_method: str = "auto"    # 提取方法 (auto/manual/hybrid)
    confidence_score: float = 0.0      # 置信度分数
    notes: str = ""                   # 备注
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StructuredKnowledge:
    """完整的结构化知识库"""
    metadata: KnowledgeMetadata = field(default_factory=KnowledgeMetadata)
    worldview: WorldView = field(default_factory=WorldView)
    characters: List[Character] = field(default_factory=list)
    plot_outline: PlotOutline = field(default_factory=PlotOutline)  
    relationship_network: RelationshipNetwork = field(default_factory=RelationshipNetwork)
    
    def update_metadata(self):
        """更新元数据统计信息"""
        self.metadata.total_characters = len(self.characters)
        self.metadata.total_worldview_elements = len(self.worldview.get_all_elements())
        self.metadata.total_plot_points = len(self.plot_outline.get_all_plot_points())
        self.metadata.extraction_time = datetime.now().isoformat()
    
    def get_character_by_name(self, name: str) -> Optional[Character]:
        """根据名称获取角色"""
        for char in self.characters:
            if char.name == name:
                return char
        return None
    
    def add_character(self, character: Character):
        """添加角色"""
        existing = self.get_character_by_name(character.name)
        if existing:
            # 更新现有角色
            self.characters.remove(existing)
        self.characters.append(character)
        self.update_metadata()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    def save_to_file(self, filepath: str) -> bool:
        """保存到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Optional['StructuredKnowledge']:
        """从文件加载"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重建对象
            knowledge = cls()
            
            # 加载元数据
            if 'metadata' in data:
                knowledge.metadata = KnowledgeMetadata(**data['metadata'])
            
            # 加载世界观
            if 'worldview' in data:
                worldview_data = data['worldview']
                knowledge.worldview = WorldView(**worldview_data)
            
            # 加载角色
            if 'characters' in data:
                for char_data in data['characters']:
                    character = Character(**char_data)
                    knowledge.characters.append(character)
            
            # 加载剧情大纲
            if 'plot_outline' in data:
                knowledge.plot_outline = PlotOutline(**data['plot_outline'])
            
            # 加载关系网络
            if 'relationship_network' in data:
                knowledge.relationship_network = RelationshipNetwork(**data['relationship_network'])
            
            return knowledge
            
        except Exception as e:
            print(f"加载失败: {e}")
            return None


# 工具函数
def create_worldview_element(category: str, name: str, description: str, 
                           importance: str = "medium", tags: List[str] = None) -> WorldViewElement:
    """创建世界观要素的便捷函数"""
    return WorldViewElement(
        category=category,
        name=name,
        description=description,
        importance=importance,
        tags=tags or []
    )

def create_character(name: str, role: str = "", **kwargs) -> Character:
    """创建角色的便捷函数"""
    return Character(name=name, role=role, **kwargs)

def create_plot_point(name: str, description: str, **kwargs) -> PlotPoint:
    """创建情节点的便捷函数"""
    return PlotPoint(name=name, description=description, **kwargs)

def create_conflict(name: str, conflict_type: str, description: str, **kwargs) -> Conflict:
    """创建冲突的便捷函数"""
    return Conflict(name=name, type=conflict_type, description=description, **kwargs)