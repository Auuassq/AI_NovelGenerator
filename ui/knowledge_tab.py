# ui/knowledge_tab.py
# -*- coding: utf-8 -*-
"""
知识库管理标签页
提供知识库导入、解析、管理的完整UI界面
"""
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from threading import Thread

from novel_generator.knowledge_parser import KnowledgeParser, parse_knowledge_from_file
from novel_generator.knowledge_structures import StructuredKnowledge
from utils import read_file


class KnowledgeTab:
    """知识库管理标签页类"""
    
    def __init__(self, parent_frame, main_window):
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.current_structured_knowledge = None
        
        self.build_knowledge_tab()
    
    def build_knowledge_tab(self):
        """构建知识库标签页界面"""
        # 主容器
        self.main_container = ctk.CTkScrollableFrame(self.parent_frame)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ctk.CTkLabel(
            self.main_container, 
            text="📚 知识库智能管理", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 创建三栏布局
        self.create_layout()
        
        # 左栏：文件操作
        self.build_file_operations_section()
        
        # 中栏：解析配置与控制
        self.build_parsing_controls_section()
        
        # 右栏：结果展示
        self.build_results_section()
    
    def create_layout(self):
        """创建三栏布局"""
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.pack(fill="both", expand=True)
        
        # 左栏：文件操作 (30%)
        self.left_frame = ctk.CTkFrame(self.content_frame)
        self.left_frame.pack(side="left", fill="both", expand=False, padx=(0, 5))
        self.left_frame.configure(width=300)
        
        # 中栏：解析控制 (40%)
        self.middle_frame = ctk.CTkFrame(self.content_frame)
        self.middle_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        # 右栏：结果展示 (30%)
        self.right_frame = ctk.CTkFrame(self.content_frame)
        self.right_frame.pack(side="right", fill="both", expand=False, padx=(5, 0))
        self.right_frame.configure(width=300)
    
    def build_file_operations_section(self):
        """构建文件操作区域"""
        # 标题
        section_title = ctk.CTkLabel(
            self.left_frame, 
            text="📁 文件操作", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        section_title.pack(pady=(10, 15))
        
        # 文件选择区域
        file_frame = ctk.CTkFrame(self.left_frame)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        # 当前文件显示
        ctk.CTkLabel(file_frame, text="当前文件:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.current_file_var = tk.StringVar(value="未选择文件")
        self.current_file_label = ctk.CTkLabel(
            file_frame, 
            textvariable=self.current_file_var,
            wraplength=250,
            font=ctk.CTkFont(size=12)
        )
        self.current_file_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # 文件操作按钮
        self.select_file_btn = ctk.CTkButton(
            self.left_frame,
            text="📂 选择知识库文件",
            command=self.select_knowledge_file,
            width=200
        )
        self.select_file_btn.pack(pady=5)
        
        self.import_file_btn = ctk.CTkButton(
            self.left_frame,
            text="📥 导入到向量库",
            command=self.import_to_vectorstore,
            width=200,
            state="disabled"
        )
        self.import_file_btn.pack(pady=5)
        
        self.parse_file_btn = ctk.CTkButton(
            self.left_frame,
            text="🧠 智能解析文档",
            command=self.parse_knowledge_file,
            width=200,
            state="disabled"
        )
        self.parse_file_btn.pack(pady=5)
        
        # 分隔线
        separator1 = ctk.CTkFrame(self.left_frame, height=2)
        separator1.pack(fill="x", padx=20, pady=15)
        
        # 文件信息显示
        info_frame = ctk.CTkFrame(self.left_frame)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(info_frame, text="文件信息:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.file_info_text = ctk.CTkTextbox(info_frame, height=120, font=ctk.CTkFont(size=11))
        self.file_info_text.pack(fill="x", padx=10, pady=(0, 10))
        self.file_info_text.insert("0.0", "请选择知识库文件...")
        self.file_info_text.configure(state="disabled")
        
        # 已有知识库管理
        knowledge_mgmt_frame = ctk.CTkFrame(self.left_frame)
        knowledge_mgmt_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(knowledge_mgmt_frame, text="知识库管理:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.load_existing_btn = ctk.CTkButton(
            knowledge_mgmt_frame,
            text="🔄 加载已有知识库",
            command=self.load_existing_knowledge,
            width=180
        )
        self.load_existing_btn.pack(pady=5)
        
        self.clear_knowledge_btn = ctk.CTkButton(
            knowledge_mgmt_frame,
            text="🗑️ 清空知识库",
            command=self.clear_knowledge_base,
            width=180,
            fg_color="red",
            hover_color="darkred"
        )
        self.clear_knowledge_btn.pack(pady=(5, 10))
    
    def build_parsing_controls_section(self):
        """构建解析控制区域"""
        # 标题
        section_title = ctk.CTkLabel(
            self.middle_frame, 
            text="⚙️ 智能解析配置", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        section_title.pack(pady=(10, 15))
        
        # 解析选项
        options_frame = ctk.CTkFrame(self.middle_frame)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(options_frame, text="解析选项:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 复选框组
        self.extract_worldview_var = tk.BooleanVar(value=True)
        self.extract_characters_var = tk.BooleanVar(value=True)
        self.extract_plot_var = tk.BooleanVar(value=True)
        self.analyze_relationships_var = tk.BooleanVar(value=True)
        
        checkbox_frame = ctk.CTkFrame(options_frame)
        checkbox_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkCheckBox(checkbox_frame, text="📍 提取世界观设定", variable=self.extract_worldview_var).pack(anchor="w", padx=10, pady=2)
        ctk.CTkCheckBox(checkbox_frame, text="👥 提取角色信息", variable=self.extract_characters_var).pack(anchor="w", padx=10, pady=2)
        ctk.CTkCheckBox(checkbox_frame, text="📖 提取剧情大纲", variable=self.extract_plot_var).pack(anchor="w", padx=10, pady=2)
        ctk.CTkCheckBox(checkbox_frame, text="🔗 分析角色关系", variable=self.analyze_relationships_var).pack(anchor="w", padx=10, pady=(2, 10))
        
        # 进度显示区域
        progress_frame = ctk.CTkFrame(self.middle_frame)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(progress_frame, text="解析进度:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(progress_frame, text="就绪", font=ctk.CTkFont(size=12))
        self.progress_label.pack(padx=10, pady=(0, 10))
        
        # 日志显示区域
        log_frame = ctk.CTkFrame(self.middle_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(log_frame, text="解析日志:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(log_frame, height=200, font=ctk.CTkFont(size=11))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # 操作按钮区域
        button_frame = ctk.CTkFrame(self.middle_frame)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        button_container = ctk.CTkFrame(button_frame)
        button_container.pack(pady=10)
        
        self.start_parse_btn = ctk.CTkButton(
            button_container,
            text="🚀 开始智能解析",
            command=self.start_parsing,
            width=150,
            font=ctk.CTkFont(weight="bold")
        )
        self.start_parse_btn.pack(side="left", padx=5)
        
        self.stop_parse_btn = ctk.CTkButton(
            button_container,
            text="⏹️ 停止解析",
            command=self.stop_parsing,
            width=120,
            state="disabled",
            fg_color="orange",
            hover_color="darkorange"
        )
        self.stop_parse_btn.pack(side="left", padx=5)
        
        self.clear_log_btn = ctk.CTkButton(
            button_container,
            text="🧹 清空日志",
            command=self.clear_log,
            width=100
        )
        self.clear_log_btn.pack(side="left", padx=5)
    
    def build_results_section(self):
        """构建结果展示区域"""
        # 标题
        section_title = ctk.CTkLabel(
            self.right_frame, 
            text="📊 解析结果", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        section_title.pack(pady=(10, 15))
        
        # 统计信息
        stats_frame = ctk.CTkFrame(self.right_frame)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(stats_frame, text="提取统计:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.stats_text = ctk.CTkTextbox(stats_frame, height=100, font=ctk.CTkFont(size=11))
        self.stats_text.pack(fill="x", padx=10, pady=(0, 10))
        self.update_stats_display()
        
        # 结果预览选项卡
        preview_frame = ctk.CTkFrame(self.right_frame)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(preview_frame, text="内容预览:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 选项卡
        self.preview_tabview = ctk.CTkTabview(preview_frame, width=280, height=300)
        self.preview_tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.preview_tabview.add("世界观")
        self.preview_tabview.add("角色")
        self.preview_tabview.add("剧情")
        self.preview_tabview.add("关系")
        self.preview_tabview.add("AI书评")  # 新增AI书评选项卡
        
        # 各选项卡内容
        self.worldview_preview = ctk.CTkTextbox(self.preview_tabview.tab("世界观"), height=200)
        self.worldview_preview.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.characters_preview = ctk.CTkTextbox(self.preview_tabview.tab("角色"), height=200)
        self.characters_preview.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.plot_preview = ctk.CTkTextbox(self.preview_tabview.tab("剧情"), height=200)
        self.plot_preview.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.relationships_preview = ctk.CTkTextbox(self.preview_tabview.tab("关系"), height=200)
        self.relationships_preview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # AI书评预览
        self.review_preview = ctk.CTkTextbox(self.preview_tabview.tab("AI书评"), height=200)
        self.review_preview.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.clear_previews()
        
        # 底部操作按钮
        action_frame = ctk.CTkFrame(self.right_frame)
        action_frame.pack(fill="x", padx=10, pady=5)
        
        action_container = ctk.CTkFrame(action_frame)
        action_container.pack(pady=10)
        
        self.save_results_btn = ctk.CTkButton(
            action_container,
            text="💾 保存结果",
            command=self.save_parsing_results,
            width=120,
            state="disabled"
        )
        self.save_results_btn.pack(side="top", pady=2)
        
        self.use_for_generation_btn = ctk.CTkButton(
            action_container,
            text="🎯 用于架构生成",
            command=self.use_for_architecture_generation,
            width=120,
            state="disabled",
            fg_color="green",
            hover_color="darkgreen"
        )
        self.use_for_generation_btn.pack(side="top", pady=2)
    
    def select_knowledge_file(self):
        """选择知识库文件"""
        filetypes = [
            ("文本文件", "*.txt"),
            ("Markdown文件", "*.md"),
            ("Word文档", "*.docx"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择知识库文档",
            filetypes=filetypes
        )
        
        if filename:
            self.current_file_var.set(os.path.basename(filename))
            self.selected_file_path = filename
            self.update_file_info(filename)
            
            # 启用相关按钮
            self.import_file_btn.configure(state="normal")
            self.parse_file_btn.configure(state="normal")
            
            self.log_message(f"✅ 已选择文件: {os.path.basename(filename)}")
    
    def update_file_info(self, filepath):
        """更新文件信息显示"""
        try:
            # 获取文件统计信息
            file_size = os.path.getsize(filepath)
            content = read_file(filepath)
            
            char_count = len(content)
            line_count = content.count('\n') + 1
            word_count = len(content.split())
            
            # 格式化显示
            size_str = f"{file_size / 1024:.1f} KB" if file_size > 1024 else f"{file_size} B"
            
            info_text = (
                f"文件名: {os.path.basename(filepath)}\n"
                f"大小: {size_str}\n"
                f"字符数: {char_count:,}\n"
                f"单词数: {word_count:,}\n"
                f"行数: {line_count:,}\n\n"
                f"内容预览:\n{content[:200]}{'...' if len(content) > 200 else ''}"
            )
            
            self.file_info_text.configure(state="normal")
            self.file_info_text.delete("0.0", "end")
            self.file_info_text.insert("0.0", info_text)
            self.file_info_text.configure(state="disabled")
            
        except Exception as e:
            self.log_message(f"❌ 读取文件信息失败: {str(e)}", is_error=True)
    
    def import_to_vectorstore(self):
        """导入文件到向量库"""
        if not hasattr(self, 'selected_file_path'):
            messagebox.showwarning("警告", "请先选择文件")
            return
        
        # 获取配置
        try:
            embedding_config = {
                'api_key': self.main_window.embedding_api_key_var.get().strip(),
                'url': self.main_window.embedding_url_var.get().strip(),
                'interface_format': self.main_window.embedding_interface_format_var.get().strip(),
                'model_name': self.main_window.embedding_model_name_var.get().strip()
            }
            
            filepath = self.main_window.filepath_var.get().strip()
            
            if not all([embedding_config['api_key'], embedding_config['url'], 
                       embedding_config['model_name'], filepath]):
                messagebox.showwarning("配置错误", "请先在配置页面设置Embedding相关配置和保存路径")
                return
            
            # 在后台线程中执行导入
            def import_task():
                try:
                    self.log_message("🚀 开始导入到向量库...")
                    
                    from novel_generator import import_knowledge_file
                    
                    import_knowledge_file(
                        embedding_api_key=embedding_config['api_key'],
                        embedding_url=embedding_config['url'],
                        embedding_interface_format=embedding_config['interface_format'],
                        embedding_model_name=embedding_config['model_name'],
                        file_path=self.selected_file_path,
                        filepath=filepath
                    )
                    
                    self.main_window.master.after(0, lambda: self.log_message("✅ 向量库导入完成"))
                    
                except Exception as e:
                    error_msg = f"❌ 向量库导入失败: {str(e)}"
                    self.main_window.after(0, lambda: self.log_message(error_msg, is_error=True))
            
            Thread(target=import_task, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"❌ 导入配置错误: {str(e)}", is_error=True)
    
    def parse_knowledge_file(self):
        """解析知识库文件（简化版，直接调用已有功能）"""
        if not hasattr(self, 'selected_file_path'):
            messagebox.showwarning("警告", "请先选择文件")
            return
        
        messagebox.showinfo("提示", "当前版本使用简化解析。点击 '🚀 开始智能解析' 获得完整的AI驱动解析功能。")
        
        # 简单的文本解析预览
        try:
            content = read_file(self.selected_file_path)
            self.show_simple_preview(content)
            self.log_message("✅ 简化解析完成，查看右侧预览结果")
            
        except Exception as e:
            self.log_message(f"❌ 解析失败: {str(e)}", is_error=True)
    
    def show_simple_preview(self, content):
        """显示简单的内容预览"""
        # 简单的关键词提取预览
        lines = content.split('\n')
        
        # 模拟世界观提取（查找包含地名、设定等关键词的行）
        worldview_lines = [line for line in lines if any(kw in line for kw in ['世界', '地理', '历史', '科技', '魔法', '设定'])]
        worldview_preview = '\n'.join(worldview_lines[:10]) or "未找到明显的世界观信息"
        
        # 模拟角色提取
        character_lines = [line for line in lines if any(kw in line for kw in ['角色', '人物', '主角', '配角', '性格'])]
        character_preview = '\n'.join(character_lines[:10]) or "未找到明显的角色信息"
        
        # 模拟剧情提取  
        plot_lines = [line for line in lines if any(kw in line for kw in ['剧情', '故事', '情节', '冲突', '高潮'])]
        plot_preview = '\n'.join(plot_lines[:10]) or "未找到明显的剧情信息"
        
        # 更新预览
        self.update_preview("世界观", worldview_preview)
        self.update_preview("角色", character_preview)
        self.update_preview("剧情", plot_preview)
        self.update_preview("关系", "简化解析不支持关系分析")
        
        # 更新统计
        self.update_stats_display({
            "worldview_elements": len(worldview_lines),
            "character_count": len(character_lines),
            "plot_points": len(plot_lines)
        })
    
    def start_parsing(self):
        """开始智能解析（完整版）"""
        if not hasattr(self, 'selected_file_path'):
            messagebox.showwarning("警告", "请先选择文件")
            return
        
        # 获取LLM配置
        try:
            llm_config = {
                'interface_format': self.main_window.interface_format_var.get().strip(),
                'api_key': self.main_window.api_key_var.get().strip(),
                'base_url': self.main_window.base_url_var.get().strip(),
                'model_name': self.main_window.model_name_var.get().strip()
            }
            
            filepath = self.main_window.filepath_var.get().strip()
            
            if not all([llm_config['api_key'], llm_config['base_url'], 
                       llm_config['model_name'], filepath]):
                messagebox.showwarning("配置错误", "请先在配置页面设置LLM配置和保存路径")
                return
            
            # 更新UI状态
            self.start_parse_btn.configure(state="disabled")
            self.stop_parse_btn.configure(state="normal")
            self.progress_bar.set(0)
            self.progress_label.configure(text="准备解析...")
            
            # 在后台线程中执行解析
            def parsing_task():
                try:
                    self.main_window.master.after(0, lambda: self.log_message("🚀 开始智能解析..."))
                    self.main_window.master.after(0, lambda: self.progress_bar.set(0.1))
                    
                    # 调用知识解析功能
                    structured_data = parse_knowledge_from_file(
                        file_path=self.selected_file_path,
                        llm_interface_format=llm_config['interface_format'],
                        llm_api_key=llm_config['api_key'],
                        llm_base_url=llm_config['base_url'],
                        llm_model=llm_config['model_name'],
                        filepath=filepath
                    )
                    
                    if structured_data:
                        self.current_structured_knowledge = structured_data
                        self.main_window.master.after(0, self.on_parsing_success)
                    else:
                        self.main_window.master.after(0, lambda: self.log_message("❌ 解析失败，未获取到有效数据", is_error=True))
                        self.main_window.master.after(0, self.on_parsing_complete)
                    
                except Exception as e:
                    error_msg = f"❌ 解析过程出错: {str(e)}"
                    self.main_window.master.after(0, lambda: self.log_message(error_msg, is_error=True))
                    self.main_window.master.after(0, self.on_parsing_complete)
            
            Thread(target=parsing_task, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"❌ 启动解析失败: {str(e)}", is_error=True)
            self.on_parsing_complete()
    
    def on_parsing_success(self):
        """解析成功回调"""
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="解析完成 ✅")
        self.log_message("✅ 智能解析完成！")
        
        # 显示解析结果
        self.display_parsing_results()
        
        # 启用相关按钮
        self.save_results_btn.configure(state="normal")
        self.use_for_generation_btn.configure(state="normal")
        
        self.on_parsing_complete()
    
    def on_parsing_complete(self):
        """解析完成回调（恢复UI状态）"""
        self.start_parse_btn.configure(state="normal")
        self.stop_parse_btn.configure(state="disabled")
    
    def stop_parsing(self):
        """停止解析"""
        # 注意：实际的停止功能需要更复杂的线程管理
        self.log_message("⏹️ 用户请求停止解析")
        self.on_parsing_complete()
    
    def display_parsing_results(self):
        """显示解析结果"""
        if not self.current_structured_knowledge:
            return
        
        data = self.current_structured_knowledge
        
        # 显示世界观
        worldview_text = self.format_worldview_display(data.get("worldview", {}))
        self.update_preview("世界观", worldview_text)
        
        # 显示角色
        characters_text = self.format_characters_display(data.get("characters", []))
        self.update_preview("角色", characters_text)
        
        # 显示剧情
        plot_text = self.format_plot_display(data.get("plot_outline", {}))
        self.update_preview("剧情", plot_text)
        
        # 显示关系
        relationships_text = self.format_relationships_display(data.get("relationship_network", {}))
        self.update_preview("关系", relationships_text)
        
        # 更新统计信息
        stats = data.get("statistics", {})
        self.update_stats_display(stats)
    
    def format_worldview_display(self, worldview_data):
        """格式化世界观显示"""
        if not worldview_data:
            return "暂无世界观数据"
        
        lines = []
        if worldview_data.get("name"):
            lines.append(f"📍 {worldview_data['name']}")
        
        if worldview_data.get("overview"):
            lines.append(f"\n概述: {worldview_data['overview']}")
        
        categories = ["geography", "history", "technology", "society", "culture", "magic_system"]
        category_names = ["地理", "历史", "科技", "社会", "文化", "魔法体系"]
        
        for cat, name in zip(categories, category_names):
            if cat in worldview_data and worldview_data[cat]:
                lines.append(f"\n== {name} ==")
                for item in worldview_data[cat][:3]:  # 只显示前3个
                    lines.append(f"• {item.get('name', '')}: {item.get('description', '')[:100]}...")
        
        return "\n".join(lines)
    
    def format_characters_display(self, characters_data):
        """格式化角色显示"""
        if not characters_data:
            return "暂无角色数据"
        
        lines = []
        for char in characters_data[:5]:  # 只显示前5个角色
            name = char.get("name", "未知角色")
            role = char.get("role", "")
            lines.append(f"👤 {name} ({role})")
            
            if char.get("background"):
                lines.append(f"   背景: {char['background'][:100]}...")
            
            if char.get("personality"):
                personalities = ", ".join(char["personality"][:3])
                lines.append(f"   性格: {personalities}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def format_plot_display(self, plot_data):
        """格式化剧情显示"""
        if not plot_data:
            return "暂无剧情数据"
        
        lines = []
        if plot_data.get("title"):
            lines.append(f"📖 {plot_data['title']}")
        
        if plot_data.get("theme"):
            lines.append(f"主题: {plot_data['theme']}")
        
        if plot_data.get("main_storyline"):
            lines.append(f"主线: {plot_data['main_storyline']}")
        
        if plot_data.get("major_conflicts"):
            lines.append("\n== 主要冲突 ==")
            for conflict in plot_data["major_conflicts"][:3]:
                name = conflict.get("name", "")
                desc = conflict.get("description", "")
                lines.append(f"• {name}: {desc[:100]}...")
        
        return "\n".join(lines)
    
    def format_relationships_display(self, relationships_data):
        """格式化关系显示"""
        if not relationships_data:
            return "暂无关系数据"
        
        lines = []
        characters = relationships_data.get("characters", [])
        relationships = relationships_data.get("relationships", [])
        
        lines.append(f"角色总数: {len(characters)}")
        lines.append(f"关系总数: {len(relationships)}")
        lines.append("\n== 主要关系 ==")
        
        for rel in relationships[:5]:  # 只显示前5个关系
            char1 = rel.get("character1", "")
            char2 = rel.get("character2", "")
            rel_type = rel.get("relationship_type", "")
            lines.append(f"• {char1} ↔ {char2}: {rel_type}")
        
        return "\n".join(lines)
    
    def update_preview(self, tab_name, content):
        """更新预览内容"""
        preview_widgets = {
            "世界观": self.worldview_preview,
            "角色": self.characters_preview,
            "剧情": self.plot_preview,
            "关系": self.relationships_preview
        }
        
        widget = preview_widgets.get(tab_name)
        if widget:
            widget.delete("0.0", "end")
            widget.insert("0.0", content)
    
    def update_stats_display(self, stats=None):
        """更新统计信息显示"""
        if stats is None:
            stats_text = "暂无统计信息"
        else:
            stats_lines = []
            stats_lines.append(f"世界观要素: {stats.get('worldview_elements', 0)}")
            stats_lines.append(f"角色数量: {stats.get('character_count', 0)}")
            stats_lines.append(f"情节点: {stats.get('plot_points', 0)}")
            stats_lines.append(f"关系数量: {stats.get('relationship_count', 0)}")
            stats_text = "\n".join(stats_lines)
        
        self.stats_text.delete("0.0", "end")
        self.stats_text.insert("0.0", stats_text)
    
    def clear_previews(self):
        """清空所有预览"""
        previews = [self.worldview_preview, self.characters_preview, 
                   self.plot_preview, self.relationships_preview]
        
        for preview in previews:
            preview.delete("0.0", "end")
            preview.insert("0.0", "暂无数据...")
    
    def log_message(self, message, is_error=False):
        """记录日志消息"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert("end", log_entry)
        self.log_text.see("end")
        
        # 如果是错误消息，可以在这里添加特殊处理
        if is_error:
            print(f"ERROR: {message}")  # 也输出到控制台
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete("0.0", "end")
    
    def save_parsing_results(self):
        """保存解析结果"""
        if not self.current_structured_knowledge:
            messagebox.showwarning("警告", "没有可保存的解析结果")
            return
        
        try:
            filepath = self.main_window.filepath_var.get().strip()
            if not filepath:
                messagebox.showwarning("警告", "请先设置保存路径")
                return
            
            # 保存为JSON文件
            output_file = os.path.join(filepath, "knowledge_parsing_results.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_structured_knowledge, f, ensure_ascii=False, indent=2)
            
            self.log_message(f"✅ 解析结果已保存至: {output_file}")
            messagebox.showinfo("成功", f"解析结果已保存至:\n{output_file}")
            
        except Exception as e:
            error_msg = f"❌ 保存失败: {str(e)}"
            self.log_message(error_msg, is_error=True)
            messagebox.showerror("错误", error_msg)
    
    def use_for_architecture_generation(self):
        """将解析结果用于架构生成"""
        if not self.current_structured_knowledge:
            messagebox.showwarning("警告", "没有可用的解析结果")
            return
        
        # 确认操作
        if not messagebox.askyesno("确认", "确定要使用当前知识库数据进行架构生成吗？\n这将在下次生成架构时自动集成知识库内容。"):
            return
        
        try:
            # 确保解析结果已保存为extracted_knowledge.json（架构生成时会自动加载这个文件）
            filepath = self.main_window.filepath_var.get().strip()
            if not filepath:
                messagebox.showwarning("警告", "请先设置保存路径")
                return
            
            output_file = os.path.join(filepath, "extracted_knowledge.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_structured_knowledge, f, ensure_ascii=False, indent=2)
            
            self.log_message(f"✅ 知识库数据已准备用于架构生成: {output_file}")
            messagebox.showinfo("设置成功", 
                              "知识库数据已准备完成！\n\n"
                              "现在您可以到 '小说设定' 标签页，\n"
                              "勾选 '使用知识库' 选项后生成架构。\n"
                              "生成的架构将自动融入知识库内容。")
        
        except Exception as e:
            error_msg = f"❌ 设置失败: {str(e)}"
            self.log_message(error_msg, is_error=True)
            messagebox.showerror("错误", error_msg)
    
    def load_existing_knowledge(self):
        """加载已有的知识库"""
        filepath = self.main_window.filepath_var.get().strip()
        if not filepath:
            messagebox.showwarning("警告", "请先设置保存路径")
            return
        
        knowledge_file = os.path.join(filepath, "extracted_knowledge.json")
        if not os.path.exists(knowledge_file):
            messagebox.showinfo("提示", "未找到已有的知识库文件")
            return
        
        try:
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                self.current_structured_knowledge = json.load(f)
            
            self.display_parsing_results()
            self.save_results_btn.configure(state="normal")
            self.use_for_generation_btn.configure(state="normal")
            
            self.log_message("✅ 已加载现有知识库数据")
            
        except Exception as e:
            error_msg = f"❌ 加载失败: {str(e)}"
            self.log_message(error_msg, is_error=True)
            messagebox.showerror("错误", error_msg)
    
    def clear_knowledge_base(self):
        """清空知识库"""
        if not messagebox.askyesno("确认", "确定要清空所有知识库数据吗？\n此操作不可撤销！"):
            return
        
        try:
            filepath = self.main_window.filepath_var.get().strip()
            if filepath:
                # 清空相关文件
                files_to_clear = [
                    "extracted_knowledge.json",
                    "knowledge_parsing_results.json"
                ]
                
                for filename in files_to_clear:
                    file_path = os.path.join(filepath, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        self.log_message(f"🗑️ 已删除: {filename}")
            
            # 清空当前数据
            self.current_structured_knowledge = None
            self.clear_previews()
            self.update_stats_display()
            
            # 禁用相关按钮
            self.save_results_btn.configure(state="disabled")
            self.use_for_generation_btn.configure(state="disabled")
            
            self.log_message("✅ 知识库已清空")
            messagebox.showinfo("完成", "知识库已清空")
            
        except Exception as e:
            error_msg = f"❌ 清空失败: {str(e)}"
            self.log_message(error_msg, is_error=True)
            messagebox.showerror("错误", error_msg)