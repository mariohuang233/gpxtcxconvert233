#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美观简洁版 GPX转TCX 转换器
简洁中带有美观，用户友好的界面设计
集成所有修复功能：步频、海拔、心率、功率等
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
from datetime import datetime
import threading

# 导入转换器
try:
    from gpx_to_tcx import GPXToTCXConverter
except ImportError:
    print("警告: 无法导入 gpx_to_tcx 模块，请确保文件存在")
    sys.exit(1)

class BeautifulGPXConverterApp:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.converter = None
        self.conversion_thread = None
        
    def setup_window(self):
        """设置主窗口"""
        self.root.title("GPX转TCX 转换器 - 美观简洁版")
        self.root.geometry("900x750")
        self.root.minsize(800, 650)
        
        # 设置窗口图标和背景
        self.root.configure(bg='#f8f9fa')
        
        # 居中显示
        self.center_window()
        
    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        
        # 设置主题
        style.theme_use('clam')
        
        # 自定义样式 - 更现代的设计
        style.configure('Title.TLabel', 
                       font=('SF Pro Display', 26, 'bold'),
                       foreground='#1a202c',
                       background='#f7fafc')
        
        style.configure('Subtitle.TLabel',
                       font=('SF Pro Text', 12),
                       foreground='#718096',
                       background='#f7fafc')
        
        style.configure('Section.TLabelframe',
                       background='#ffffff',
                       borderwidth=0,
                       relief='flat')
        
        style.configure('Section.TLabelframe.Label',
                       font=('SF Pro Text', 13, 'bold'),
                       foreground='#2d3748',
                       background='#ffffff')
        
        style.configure('Primary.TButton',
                       font=('SF Pro Text', 12, 'bold'),
                       foreground='#ffffff',
                       background='#4299e1',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 12))
        
        style.map('Primary.TButton',
                 background=[('active', '#3182ce'),
                           ('pressed', '#2c5282')])
        
        style.configure('Secondary.TButton',
                       font=('SF Pro Text', 11),
                       foreground='#4a5568',
                       background='#edf2f7',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(16, 8))
        
        style.map('Secondary.TButton',
                 background=[('active', '#e2e8f0'),
                           ('pressed', '#cbd5e0')])
        
        # 进度条样式 - 更现代的渐变效果
        style.configure('TProgressbar',
                       background='#4299e1',
                       troughcolor='#edf2f7',
                       borderwidth=0,
                       lightcolor='#4299e1',
                       darkcolor='#4299e1')
        
        # 下拉框样式优化
        style.configure('TCombobox',
                       fieldbackground='#ffffff',
                       background='#ffffff',
                       borderwidth=1,
                       relief='solid',
                       bordercolor='#e2e8f0',
                       focuscolor='#4299e1')
        
        # 输入框样式优化
        style.configure('TEntry',
                       fieldbackground='#ffffff',
                       borderwidth=1,
                       relief='solid',
                       bordercolor='#e2e8f0',
                       focuscolor='#4299e1')
        
    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = tk.Frame(self.root, bg='#f8f9fa', padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # 标题区域
        header_frame = tk.Frame(main_frame, bg='#f8f9fa')
        header_frame.pack(fill='x', pady=(0, 30))
        
        title_label = ttk.Label(header_frame, 
                               text="GPX转TCX 转换器",
                               style='Title.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame,
                                  text="简洁美观 • 功能完整 • 数据真实",
                                  style='Subtitle.TLabel')
        subtitle_label.pack(pady=(5, 0))
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="📁 文件选择", 
                                   style='Section.TLabelframe', padding=20)
        file_frame.pack(fill='x', pady=(0, 20))
        
        # 输入文件
        input_label = ttk.Label(file_frame, text="输入GPX文件:", 
                               font=('SF Pro Text', 11, 'bold'))
        input_label.pack(anchor='w', pady=(0, 5))
        
        input_frame = tk.Frame(file_frame, bg='#ffffff')
        input_frame.pack(fill='x', pady=(0, 15))
        
        self.input_path_var = tk.StringVar()
        input_entry = ttk.Entry(input_frame, textvariable=self.input_path_var,
                               font=('SF Pro Text', 11))
        input_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        browse_input_btn = ttk.Button(input_frame, text="浏览", 
                                     command=self.browse_input_file,
                                     style='Secondary.TButton')
        browse_input_btn.pack(side='right')
        
        # 输出文件
        output_label = ttk.Label(file_frame, text="输出TCX文件:",
                                font=('SF Pro Text', 11, 'bold'))
        output_label.pack(anchor='w', pady=(0, 5))
        
        output_frame = tk.Frame(file_frame, bg='#ffffff')
        output_frame.pack(fill='x')
        
        self.output_path_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var,
                                font=('SF Pro Text', 11))
        output_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        browse_output_btn = ttk.Button(output_frame, text="另存为",
                                      command=self.browse_output_file,
                                      style='Secondary.TButton')
        browse_output_btn.pack(side='right')
        
        # 配置区域 - 更现代的卡片式设计
        config_frame = ttk.LabelFrame(main_frame, text="⚙️ 转换配置",
                                     style='Section.TLabelframe', padding=20)
        config_frame.pack(fill='x', pady=(0, 20))
        
        # 添加阴影效果的配置容器
        config_container = tk.Frame(config_frame, bg='#ffffff', relief='flat', bd=0)
        config_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 左侧配置 - 运动指标
        left_config = tk.Frame(config_container, bg='#ffffff')
        left_config.pack(side='left', fill='both', expand=True, padx=(0, 25))
        
        # 添加左侧标题
        left_title = tk.Label(left_config, text="🏃‍♂️ 运动指标", 
                             font=('SF Pro Text', 14, 'bold'),
                             fg='#2d3748', bg='#ffffff')
        left_title.grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 15))
        
        # 右侧配置 - 基本设置
        right_config = tk.Frame(config_container, bg='#ffffff')
        right_config.pack(side='right', fill='both', expand=True)
        
        # 添加右侧标题
        right_title = tk.Label(right_config, text="⚙️ 基本设置", 
                              font=('SF Pro Text', 14, 'bold'),
                              fg='#2d3748', bg='#ffffff')
        right_title.grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 15))
        
        self.config_vars = {}
        
        # 左侧配置项 - 使用下拉框（从第1行开始，因为第0行是标题）
        self.create_dropdown_config(left_config, 1, "💓 心率范围 (bpm):", "min_hr", ["120", "125", "130", "135", "140"], "135", "max_hr", ["155", "160", "165", "170", "175"], "165")
        self.create_dropdown_config(left_config, 2, "🏃 步频范围 (spm):", "min_cadence", ["45", "48", "50", "52", "55"], "50", "max_cadence", ["65", "68", "70", "72", "75"], "70")
        self.create_dropdown_config(left_config, 3, "⚡ 功率范围 (W):", "min_power", ["120", "130", "140", "150", "160"], "150", "max_power", ["280", "290", "300", "310", "320"], "300")
        
        # 右侧配置项 - 混合使用下拉框和输入框（从第1行开始，因为第0行是标题）
        self.create_dropdown_config(right_config, 1, "🎯 目标配速 (min/km):", "target_pace", ["4:30", "5:00", "5:30", "6:00", "6:30"], "5:30", None, None, None)
        self.create_dropdown_config(right_config, 2, "🏃‍♂️ 运动类型:", "sport_type", ["Running", "Cycling", "Walking", "Hiking"], "Running", None, None, None)
        
        # 开始时间使用输入框，默认当前时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.create_time_input(right_config, 3, "🕐 开始时间:", "start_time", current_time)
        
        # 时间格式提示
        time_hint = ttk.Label(right_config,
                             text="格式: YYYY-MM-DD HH:MM:SS (留空使用GPX时间)",
                             font=('SF Pro Text', 10),
                             foreground='#718096',
                             background='#ffffff')
        time_hint.grid(row=4, column=0, columnspan=4, sticky='w', pady=(5, 0))
        
        # 转换按钮区域 - 更突出的设计
        button_frame = tk.Frame(main_frame, bg='#f7fafc')
        button_frame.pack(pady=20)
        
        # 添加分隔线
        separator = tk.Frame(button_frame, height=1, bg='#e2e8f0')
        separator.pack(fill='x', pady=(0, 20))
        
        self.convert_btn = ttk.Button(button_frame,
                                     text="🚀 开始转换",
                                     command=self.start_conversion,
                                     style='Primary.TButton')
        self.convert_btn.pack(ipadx=20, ipady=8, pady=(0, 20))
        
        # 进度条
        progress_frame = tk.Frame(main_frame, bg='#f8f9fa')
        progress_frame.pack(fill='x', pady=(10, 20))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame,
                                          variable=self.progress_var,
                                          maximum=100,
                                          length=500)
        self.progress_bar.pack()
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="📋 转换日志",
                                  style='Section.TLabelframe', padding=15)
        log_frame.pack(fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=('SF Mono', 10),
            wrap='word',
            height=12,
            bg='#2c3e50',
            fg='#ecf0f1',
            insertbackground='#ecf0f1',
            selectbackground='#34495e'
        )
        self.log_text.pack(fill='both', expand=True)
        
        # 添加欢迎信息
        self.show_welcome_message()
        
    def create_config_row(self, parent, row, label, var1, val1, var2, val2):
        """创建配置行"""
        label_widget = ttk.Label(parent, text=label,
                                font=('SF Pro Text', 10, 'bold'),
                                background='#ffffff')
        label_widget.grid(row=row, column=0, sticky='w', pady=8, padx=(0, 10))
        
        self.config_vars[var1] = tk.StringVar(value=val1)
        entry1 = ttk.Entry(parent, textvariable=self.config_vars[var1],
                          width=8, font=('SF Pro Text', 10))
        entry1.grid(row=row, column=1, padx=5, pady=8)
        
        if var2:
            dash_label = ttk.Label(parent, text="-",
                                  font=('SF Pro Text', 10),
                                  background='#ffffff')
            dash_label.grid(row=row, column=2, padx=5, pady=8)
            
            self.config_vars[var2] = tk.StringVar(value=val2)
            entry2 = ttk.Entry(parent, textvariable=self.config_vars[var2],
                              width=8, font=('SF Pro Text', 10))
            entry2.grid(row=row, column=3, padx=5, pady=8)
    
    def create_dropdown_config(self, parent, row, label, var1, options1, default1, var2=None, options2=None, default2=None):
        """创建下拉框配置行"""
        # 标签
        label_widget = ttk.Label(parent, text=label,
                                font=('SF Pro Text', 10, 'bold'),
                                background='#ffffff')
        label_widget.grid(row=row, column=0, sticky='w', pady=8, padx=(0, 10))
        
        # 第一个下拉框
        self.config_vars[var1] = tk.StringVar(value=default1)
        combo1 = ttk.Combobox(parent, textvariable=self.config_vars[var1],
                             font=('SF Pro Text', 10), width=6,
                             values=options1, state='readonly')
        combo1.grid(row=row, column=1, padx=5, pady=8)
        
        # 第二个下拉框（如果存在）
        if var2 and options2:
            dash_label = ttk.Label(parent, text="-",
                                  font=('SF Pro Text', 10),
                                  background='#ffffff')
            dash_label.grid(row=row, column=2, padx=5, pady=8)
            
            self.config_vars[var2] = tk.StringVar(value=default2)
            combo2 = ttk.Combobox(parent, textvariable=self.config_vars[var2],
                                 font=('SF Pro Text', 10), width=6,
                                 values=options2, state='readonly')
            combo2.grid(row=row, column=3, padx=5, pady=8)
    
    def create_time_input(self, parent, row, label, var, default_value):
        """创建时间输入框"""
        # 标签
        label_widget = ttk.Label(parent, text=label,
                                font=('SF Pro Text', 10, 'bold'),
                                background='#ffffff')
        label_widget.grid(row=row, column=0, sticky='w', pady=8, padx=(0, 10))
        
        # 时间输入框
        self.config_vars[var] = tk.StringVar(value=default_value)
        time_entry = ttk.Entry(parent, textvariable=self.config_vars[var],
                              font=('SF Pro Text', 10), width=18)
        time_entry.grid(row=row, column=1, columnspan=3, padx=5, pady=8, sticky='w')
        
    def show_welcome_message(self):
        """显示欢迎信息"""
        welcome_msg = """🎉 欢迎使用 GPX转TCX 转换器 - 美观简洁版

✨ 核心功能:
  • 步频修复: 50-70真实范围 (替代错误170+)
  • 海拔修复: 准确GPX数据解析
  • 心率优化: 135-165智能变化
  • 功率计算: 150-300W真实跑步功率
  • 开始时间: 支持自定义运动开始时间

🎨 界面特色:
  • 现代化设计，简洁美观
  • 直观的操作流程
  • 实时转换进度显示
  • 详细的日志反馈

📝 使用说明:
  1. 选择输入的GPX文件
  2. 设置输出的TCX文件路径
  3. 调整配置参数(可选)
     - 开始时间格式: 2024-01-15 08:30:00
     - 留空则使用GPX文件中的时间
  4. 点击"🚀 开始转换"按钮

🚀 准备就绪，请开始您的转换任务！
"""
        
        # 设置不同颜色的文本
        self.log_text.insert('end', welcome_msg)
        self.log_text.see('end')
        
    def browse_input_file(self):
        """浏览输入文件"""
        filename = filedialog.askopenfilename(
            title="选择GPX文件",
            filetypes=[("GPX文件", "*.gpx"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_path_var.set(filename)
            # 自动设置输出文件名
            if not self.output_path_var.get():
                base_name = os.path.splitext(filename)[0]
                self.output_path_var.set(base_name + ".tcx")
                
    def browse_output_file(self):
        """浏览输出文件"""
        filename = filedialog.asksaveasfilename(
            title="保存TCX文件",
            defaultextension=".tcx",
            filetypes=[("TCX文件", "*.tcx"), ("所有文件", "*.*")]
        )
        if filename:
            self.output_path_var.set(filename)
            
    def start_conversion(self):
        """开始转换"""
        input_path = self.input_path_var.get().strip()
        output_path = self.output_path_var.get().strip()
        
        if not input_path or not output_path:
            messagebox.showerror("错误", "请选择输入和输出文件")
            return
            
        if not os.path.exists(input_path):
            messagebox.showerror("错误", "输入文件不存在")
            return
            
        # 禁用转换按钮
        self.convert_btn.config(state='disabled', text="转换中...")
        self.progress_var.set(0)
        
        # 清空日志
        self.log_text.delete(1.0, 'end')
        
        # 在新线程中执行转换
        self.conversion_thread = threading.Thread(
            target=self.perform_conversion,
            args=(input_path, output_path)
        )
        self.conversion_thread.daemon = True
        self.conversion_thread.start()
        
    def perform_conversion(self, input_path, output_path):
        """执行转换"""
        try:
            self.log_message("\n🚀 开始转换过程...")
            self.log_message(f"📁 输入文件: {os.path.basename(input_path)}")
            self.log_message(f"💾 输出文件: {os.path.basename(output_path)}")
            
            # 更新进度
            self.root.after(0, lambda: self.progress_var.set(10))
            
            # 创建转换器
            self.converter = GPXToTCXConverter()
            self.log_message("✅ 转换器初始化完成")
            
            # 应用配置
            self.apply_config_to_converter()
            self.root.after(0, lambda: self.progress_var.set(20))
            
            # 执行转换
            self.log_message("📖 正在解析GPX文件...")
            self.root.after(0, lambda: self.progress_var.set(40))
            
            result = self.converter.convert(input_path, output_path)
            self.root.after(0, lambda: self.progress_var.set(80))
            
            if result:
                self.log_message("✅ GPX文件解析完成")
                self.log_message("🔄 正在生成TCX文件...")
                self.root.after(0, lambda: self.progress_var.set(90))
                
                # 验证输出文件
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    self.log_message(f"🎉 TCX文件生成成功")
                    self.log_message(f"📊 文件大小: {file_size:,} 字节")
                    
                    # 显示修复功能状态
                    self.log_message("\n🔧 数据修复状态:")
                    self.log_message("✅ 步频修复: 50-70真实范围 (已启用)")
                    self.log_message("✅ 海拔修复: GPX数据准确解析 (已启用)")
                    self.log_message("✅ 心率优化: 135-165智能变化 (已启用)")
                    self.log_message("✅ 功率计算: 150-300W真实跑步功率 (已启用)")
                    self.log_message("✅ 开始时间: 支持自定义运动开始时间 (已启用)")
                    
                    self.root.after(0, lambda: self.progress_var.set(100))
                    self.log_message("\n🎊 转换完成！所有修复功能已生效")
                    
                    # 显示成功消息
                    self.root.after(0, lambda: messagebox.showinfo(
                        "转换成功",
                        f"🎉 文件转换完成！\n\n📁 输出文件: {os.path.basename(output_path)}\n📊 文件大小: {file_size:,} 字节\n\n✨ 所有数据修复功能已生效"
                    ))
                else:
                    raise Exception("输出文件未生成")
            else:
                raise Exception("转换过程失败")
                
        except Exception as e:
            self.log_message(f"❌ 转换失败: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("转换失败", f"转换过程中出现错误:\n{str(e)}"))
            
        finally:
            # 恢复转换按钮
            self.root.after(0, lambda: self.convert_btn.config(state='normal', text="🚀 开始转换"))
            
    def apply_config_to_converter(self):
        """应用配置到转换器"""
        if not self.converter:
            return
            
        try:
            # 获取配置值
            config = {}
            for key, var in self.config_vars.items():
                # 处理不同类型的变量
                if hasattr(var, 'get'):
                    value = var.get()
                    if isinstance(value, str):
                        value = value.strip()
                else:
                    # 如果是StringVar等tkinter变量
                    value = str(var.get()).strip() if var.get() else ""
                
                if value:
                    if key in ['min_hr', 'max_hr', 'min_cadence', 'max_cadence', 'min_power', 'max_power']:
                        try:
                            config[key] = int(value)
                        except ValueError:
                            self.log_message(f"⚠️ 配置项 {key} 的值 '{value}' 无法转换为整数，使用默认值")
                            continue
                    else:
                        config[key] = value
            
            # 应用心率配置
            hr_min = config.get('min_hr', 135)
            hr_max = config.get('max_hr', 165)
            self.converter.config['base_hr'] = hr_min
            self.converter.config['max_hr'] = hr_max
            self.log_message(f"💓 心率范围: {hr_min}-{hr_max} bpm")
            
            # 应用步频配置
            cadence_min = config.get('min_cadence', 50)
            cadence_max = config.get('max_cadence', 70)
            self.converter.config['base_cadence'] = cadence_min
            self.converter.config['max_cadence'] = cadence_max
            self.log_message(f"🏃 步频范围: {cadence_min}-{cadence_max} spm")
            
            # 应用功率配置
            power_min = config.get('min_power', 150)
            power_max = config.get('max_power', 300)
            self.converter.config['min_power'] = power_min
            self.converter.config['max_power'] = power_max
            self.log_message(f"⚡ 功率范围: {power_min}-{power_max} W")
            
            # 应用目标配速配置
            target_pace = config.get('target_pace', '5:30')
            self.converter.config['target_pace'] = target_pace
            self.log_message(f"🎯 目标配速: {target_pace} min/km")
            
            sport_type = config.get('sport_type', 'Running')
            self.converter.config['activity_type'] = sport_type
            self.log_message(f"🏃‍♂️ 运动类型: {sport_type}")
            
            # 应用卡路里配置
            self.converter.config['calories_per_km'] = 60  # 默认每公里消耗60卡路里
            self.log_message(f"🔥 卡路里消耗: 60 卡/公里")
            
            # 应用设备信息配置
            self.converter.config['device_name'] = 'Forerunner 570'
            self.converter.config['device_version'] = '12.70'
            self.converter.config['weight'] = 70  # 默认体重70kg
            self.log_message(f"📱 设备信息: Forerunner 570 v12.70")
            self.log_message(f"⚖️ 体重设置: 70 kg")
            
            # 处理开始时间设置
            start_time_str = config.get('start_time', '').strip()
            if start_time_str:
                try:
                    # 解析时间格式
                    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                    self.converter.config['start_time'] = start_time
                    self.log_message(f"🕐 自定义开始时间: {start_time_str}")
                except ValueError:
                    self.log_message(f"⚠️ 开始时间格式错误 '{start_time_str}'，将使用GPX文件中的时间")
            else:
                self.log_message("🕐 使用GPX文件中的原始时间")
                
            self.log_message("⚙️ 配置应用完成")
            
        except Exception as e:
            self.log_message(f"⚠️ 配置应用警告: {str(e)}")
            
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # 在主线程中更新UI
        self.root.after(0, lambda: self._update_log(formatted_message))
        
    def _update_log(self, message):
        """更新日志显示"""
        self.log_text.insert('end', message)
        self.log_text.see('end')
        self.root.update_idletasks()

def main():
    """主函数"""
    root = tk.Tk()
    app = BeautifulGPXConverterApp(root)
    
    # 设置窗口关闭事件
    def on_closing():
        if app.conversion_thread and app.conversion_thread.is_alive():
            if messagebox.askokcancel("退出", "转换正在进行中，确定要退出吗？"):
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()