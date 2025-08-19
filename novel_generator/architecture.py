#novel_generator/architecture.py
# -*- coding: utf-8 -*-
"""
小说总体架构生成（Novel_architecture_generate 及相关辅助函数）
"""
import os
import json
import logging
import traceback
from novel_generator.common import invoke_with_cleaning
from llm_adapters import create_llm_adapter
from prompt_definitions import (
    core_seed_prompt,
    character_dynamics_prompt,
    world_building_prompt,
    plot_architecture_prompt,
    create_character_state_prompt
)
from utils import clear_file_content, save_string_to_txt


def load_structured_knowledge(filepath: str) -> dict:
    """
    从 filepath 下加载已提取的结构化知识库数据
    """
    knowledge_file = os.path.join(filepath, "extracted_knowledge.json")
    if not os.path.exists(knowledge_file):
        return {}
    
    try:
        with open(knowledge_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        logging.info(f"已加载结构化知识库数据: {knowledge_file}")
        return data
    except Exception as e:
        logging.warning(f"无法加载结构化知识库: {e}")
        return {}


def format_knowledge_for_prompt(structured_knowledge: dict) -> str:
    """
    将结构化知识库数据格式化为提示词可用的文本
    """
    if not structured_knowledge:
        return ""
    
    formatted_sections = []
    
    # 格式化世界观信息
    if "worldview" in structured_knowledge:
        worldview = structured_knowledge["worldview"]
        if worldview:
            formatted_sections.append("=== 知识库-世界观设定 ===")
            
            if worldview.get("overview"):
                formatted_sections.append(f"总概述: {worldview['overview']}")
            
            # 处理各类世界观要素
            categories = ["geography", "history", "technology", "society", "culture", 
                         "magic_system", "politics", "economy", "other_elements"]
            category_names = ["地理", "历史", "科技", "社会", "文化", "魔法体系", "政治", "经济", "其他"]
            
            for category, name in zip(categories, category_names):
                if category in worldview and worldview[category]:
                    formatted_sections.append(f"\n{name}设定:")
                    for element in worldview[category][:3]:  # 限制数量避免过长
                        formatted_sections.append(f"- {element.get('name', '')}: {element.get('description', '')}")
    
    # 格式化角色信息
    if "characters" in structured_knowledge and structured_knowledge["characters"]:
        formatted_sections.append("\n=== 知识库-角色信息 ===")
        
        for char in structured_knowledge["characters"][:5]:  # 限制主要角色数量
            name = char.get("name", "")
            role = char.get("role", "")
            if name:
                formatted_sections.append(f"\n{name} ({role}):")
                if char.get("background"):
                    formatted_sections.append(f"  背景: {char['background']}")
                if char.get("personality"):
                    personalities = ", ".join(char["personality"][:3])  # 限制特征数量
                    formatted_sections.append(f"  性格: {personalities}")
                if char.get("motivation"):
                    formatted_sections.append(f"  目标: {char['motivation']}")
    
    # 格式化剧情信息
    if "plot_outline" in structured_knowledge:
        plot = structured_knowledge["plot_outline"]
        if plot:
            formatted_sections.append("\n=== 知识库-剧情要素 ===")
            
            if plot.get("theme"):
                formatted_sections.append(f"主题: {plot['theme']}")
            if plot.get("main_storyline"):
                formatted_sections.append(f"主线: {plot['main_storyline']}")
            
            # 添加主要冲突
            if plot.get("major_conflicts"):
                formatted_sections.append("\n主要冲突:")
                for conflict in plot["major_conflicts"][:3]:
                    name = conflict.get("name", "")
                    desc = conflict.get("description", "")
                    if name and desc:
                        formatted_sections.append(f"- {name}: {desc}")
    
    return "\n".join(formatted_sections)


def load_partial_architecture_data(filepath: str) -> dict:
    """
    从 filepath 下的 partial_architecture.json 读取已有的阶段性数据。
    如果文件不存在或无法解析，返回空 dict。
    """
    partial_file = os.path.join(filepath, "partial_architecture.json")
    if not os.path.exists(partial_file):
        return {}
    try:
        with open(partial_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logging.warning(f"Failed to load partial_architecture.json: {e}")
        return {}

def save_partial_architecture_data(filepath: str, data: dict):
    """
    将阶段性数据写入 partial_architecture.json。
    """
    partial_file = os.path.join(filepath, "partial_architecture.json")
    try:
        with open(partial_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Failed to save partial_architecture.json: {e}")

def Novel_architecture_generate(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    topic: str,
    genre: str,
    number_of_chapters: int,
    word_number: int,
    filepath: str,
    user_guidance: str = "",  # 新增参数
    use_knowledge_base: bool = False,  # 是否使用知识库
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600
) -> None:
    """
    依次调用:
      1. core_seed_prompt
      2. character_dynamics_prompt  
      3. world_building_prompt
      4. plot_architecture_prompt
    若在中间任何一步报错且重试多次失败，则将已经生成的内容写入 partial_architecture.json 并退出；
    下次调用时可从该步骤继续。
    最终输出 Novel_architecture.txt

    新增：
    - 在完成角色动力学设定后，依据该角色体系，使用 create_character_state_prompt 生成初始角色状态表，
      并存储到 character_state.txt，后续维护更新。
    - 支持知识库集成：如果use_knowledge_base=True，会加载已提取的知识库数据辅助生成
    """
    os.makedirs(filepath, exist_ok=True)
    partial_data = load_partial_architecture_data(filepath)
    
    # 加载知识库数据（如果启用）
    knowledge_context = ""
    if use_knowledge_base:
        logging.info("尝试加载结构化知识库数据...")
        structured_knowledge = load_structured_knowledge(filepath)
        if structured_knowledge:
            knowledge_context = format_knowledge_for_prompt(structured_knowledge)
            logging.info(f"已加载知识库数据，上下文长度: {len(knowledge_context)} 字符")
        else:
            logging.info("未找到知识库数据或数据为空")
    
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )
    
    # 构建增强的用户指导（包含知识库信息）
    enhanced_guidance = user_guidance
    if knowledge_context:
        enhanced_guidance = f"{user_guidance}\n\n{knowledge_context}" if user_guidance else knowledge_context
    
    # Step1: 核心种子
    if "core_seed_result" not in partial_data:
        logging.info("Step1: Generating core_seed_prompt (核心种子) ...")
        prompt_core = core_seed_prompt.format(
            topic=topic,
            genre=genre,
            number_of_chapters=number_of_chapters,
            word_number=word_number,
            user_guidance=enhanced_guidance
        )
        core_seed_result = invoke_with_cleaning(llm_adapter, prompt_core)
        if not core_seed_result.strip():
            logging.warning("core_seed_prompt generation failed and returned empty.")
            save_partial_architecture_data(filepath, partial_data)
            return
        partial_data["core_seed_result"] = core_seed_result
        save_partial_architecture_data(filepath, partial_data)
    else:
        logging.info("Step1 already done. Skipping...")
    
    # Step2: 角色动力学
    if "character_dynamics_result" not in partial_data:
        logging.info("Step2: Generating character_dynamics_prompt ...")
        prompt_character = character_dynamics_prompt.format(
            core_seed=partial_data["core_seed_result"].strip(),
            user_guidance=enhanced_guidance
        )
        character_dynamics_result = invoke_with_cleaning(llm_adapter, prompt_character)
        if not character_dynamics_result.strip():
            logging.warning("character_dynamics_prompt generation failed.")
            save_partial_architecture_data(filepath, partial_data)
            return
        partial_data["character_dynamics_result"] = character_dynamics_result
        save_partial_architecture_data(filepath, partial_data)
    else:
        logging.info("Step2 already done. Skipping...")
        
    # 生成初始角色状态
    if "character_dynamics_result" in partial_data and "character_state_result" not in partial_data:
        logging.info("Generating initial character state from character dynamics ...")
        prompt_char_state_init = create_character_state_prompt.format(
            character_dynamics=partial_data["character_dynamics_result"].strip()
        )
        character_state_init = invoke_with_cleaning(llm_adapter, prompt_char_state_init)
        if not character_state_init.strip():
            logging.warning("create_character_state_prompt generation failed.")
            save_partial_architecture_data(filepath, partial_data)
            return
        partial_data["character_state_result"] = character_state_init
        character_state_file = os.path.join(filepath, "character_state.txt")
        clear_file_content(character_state_file)
        save_string_to_txt(character_state_init, character_state_file)
        save_partial_architecture_data(filepath, partial_data)
        logging.info("Initial character state created and saved.")
        
    # Step3: 世界观
    if "world_building_result" not in partial_data:
        logging.info("Step3: Generating world_building_prompt ...")
        prompt_world = world_building_prompt.format(
            core_seed=partial_data["core_seed_result"].strip(),
            user_guidance=enhanced_guidance
        )
        world_building_result = invoke_with_cleaning(llm_adapter, prompt_world)
        if not world_building_result.strip():
            logging.warning("world_building_prompt generation failed.")
            save_partial_architecture_data(filepath, partial_data)
            return
        partial_data["world_building_result"] = world_building_result
        save_partial_architecture_data(filepath, partial_data)
    else:
        logging.info("Step3 already done. Skipping...")
        
    # Step4: 三幕式情节
    if "plot_arch_result" not in partial_data:
        logging.info("Step4: Generating plot_architecture_prompt ...")
        prompt_plot = plot_architecture_prompt.format(
            core_seed=partial_data["core_seed_result"].strip(),
            character_dynamics=partial_data["character_dynamics_result"].strip(),
            world_building=partial_data["world_building_result"].strip(),
            user_guidance=enhanced_guidance
        )
        plot_arch_result = invoke_with_cleaning(llm_adapter, prompt_plot)
        if not plot_arch_result.strip():
            logging.warning("plot_architecture_prompt generation failed.")
            save_partial_architecture_data(filepath, partial_data)
            return
        partial_data["plot_arch_result"] = plot_arch_result
        save_partial_architecture_data(filepath, partial_data)
    else:
        logging.info("Step4 already done. Skipping...")

    core_seed_result = partial_data["core_seed_result"]
    character_dynamics_result = partial_data["character_dynamics_result"]
    world_building_result = partial_data["world_building_result"]
    plot_arch_result = partial_data["plot_arch_result"]

    # 构建最终内容，如果使用了知识库则添加相关说明
    knowledge_note = ""
    if use_knowledge_base and knowledge_context:
        knowledge_note = "\n\n#=== 知识库集成说明 ===\n本架构已集成导入的知识库数据，在世界观、角色和剧情设定中融入了知识库要素。\n"

    final_content = (
        "#=== 0) 小说设定 ===\n"
        f"主题：{topic},类型：{genre},篇幅：约{number_of_chapters}章（每章{word_number}字）\n"
        f"知识库集成：{'是' if use_knowledge_base else '否'}\n"
        f"{knowledge_note}"
        "#=== 1) 核心种子 ===\n"
        f"{core_seed_result}\n\n"
        "#=== 2) 角色动力学 ===\n"
        f"{character_dynamics_result}\n\n"
        "#=== 3) 世界观 ===\n"
        f"{world_building_result}\n\n"
        "#=== 4) 三幕式情节架构 ===\n"
        f"{plot_arch_result}\n"
    )

    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    clear_file_content(arch_file)
    save_string_to_txt(final_content, arch_file)
    logging.info("Novel_architecture.txt has been generated successfully.")

    partial_arch_file = os.path.join(filepath, "partial_architecture.json")
    if os.path.exists(partial_arch_file):
        os.remove(partial_arch_file)
        logging.info("partial_architecture.json removed (all steps completed).")
