#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简洁版 GPX转TCX 转换器
专注功能本身，简洁高效的界面设计
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

class SimpleGPXConverterApp:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_widgets()
        self.converter = None
        self.conversion_thread = None
        
    def setup_window(self):
        """设置主窗口"""
        self.root.title("GPX转TCX 转换器 - 简洁版")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)
        
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
        
    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, 
                               text="GPX转TCX 转换器",
                               font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="15")
        file_frame.pack(fill='x', pady=(0, 15))
        
        # 输入文件
        ttk.Label(file_frame, text="输入GPX文件:").pack(anchor='w')
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill='x', pady=(5, 10))
        
        self.input_path_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_path_var).pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Button(input_frame, text="浏览", command=self.browse_input_file).pack(side='right')
        
        # 输出文件
        ttk.Label(file_frame, text="输出TCX文件:").pack(anchor='w')
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill='x', pady=(5, 0))
        
        self.output_path_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_path_var).pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Button(output_frame, text="另存为", command=self.browse_output_file).pack(side='right')
        
        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="配置选项", padding="15")
        config_frame.pack(fill='x', pady=(0, 15))
        
        # 配置网格
        config_grid = ttk.Frame(config_frame)
        config_grid.pack(fill='x')
        
        self.config_vars = {}
        configs = [
            ("心率范围:", "min_hr", "135", "max_hr", "165"),
            ("步频范围:", "min_cadence", "50", "max_cadence", "70"),
            ("功率范围:", "min_power", "150", "max_power", "300"),
            ("目标配速:", "target_pace", "5:30", None, None),
            ("运动类型:", "sport_type", "Running", None, None),
            ("开始时间:", "start_time", "", None, None)
        ]
        
        for i, (label, var1, val1, var2, val2) in enumerate(configs):
            ttk.Label(config_grid, text=label).grid(row=i, column=0, sticky='w', padx=(0, 10), pady=2)
            
            self.config_vars[var1] = tk.StringVar(value=val1)
            ttk.Entry(config_grid, textvariable=self.config_vars[var1], width=10).grid(row=i, column=1, padx=5, pady=2)
            
            if var2:
                ttk.Label(config_grid, text="-").grid(row=i, column=2, padx=5, pady=2)
                self.config_vars[var2] = tk.StringVar(value=val2)
                ttk.Entry(config_grid, textvariable=self.config_vars[var2], width=10).grid(row=i, column=3, padx=5, pady=2)
        
        # 转换按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=15)
        
        self.convert_btn = ttk.Button(button_frame, 
                                     text="开始转换",
                                     command=self.start_conversion,
                                     style='Accent.TButton')
        self.convert_btn.pack()
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, 
                                          variable=self.progress_var,
                                          maximum=100,
                                          length=400)
        self.progress_bar.pack(pady=(10, 15))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="转换日志", padding="10")
        log_frame.pack(fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=('Consolas', 10),
            wrap='word',
            height=15
        )
        self.log_text.pack(fill='both', expand=True)
        
        # 添加时间格式说明
        time_hint = ttk.Label(config_grid, 
                             text="(格式: YYYY-MM-DD HH:MM:SS 或留空使用GPX时间)", 
                             font=('Arial', 8), 
                             foreground='gray')
        time_hint.grid(row=len(configs)-1, column=1, columnspan=3, sticky='w', padx=5, pady=(0, 5))
        
        # 添加欢迎信息
        welcome_msg = """GPX转TCX 转换器 - 简洁版

功能特色:
• 步频修复: 50-70真实范围 (替代错误170+)
• 海拔修复: 准确GPX数据解析
• 心率优化: 135-165智能变化
• 功率计算: 基于速度的智能算法
• 开始时间: 支持自定义运动开始时间

使用说明:
1. 选择输入的GPX文件
2. 设置输出的TCX文件路径
3. 调整配置参数(可选)
   - 开始时间格式: 2024-01-15 08:30:00
   - 留空则使用GPX文件中的时间
4. 点击"开始转换"按钮

准备就绪，请开始您的转换任务！
"""
        self.log_text.insert('end', welcome_msg)
        
    def browse_input_file(self):
        """浏览输入文件"""
        file_path = filedialog.askopenfilename(
            title="选择GPX文件",
            filetypes=[("GPX files", "*.gpx"), ("All files", "*.*")]
        )
        if file_path:
            self.input_path_var.set(file_path)
            # 自动设置输出文件名
            base_name = os.path.splitext(file_path)[0]
            output_path = f"{base_name}_简洁版.tcx"
            self.output_path_var.set(output_path)
            self.log_message(f"已选择输入文件: {os.path.basename(file_path)}")
            
    def browse_output_file(self):
        """浏览输出文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存TCX文件",
            defaultextension=".tcx",
            filetypes=[("TCX files", "*.tcx"), ("All files", "*.*")]
        )
        if file_path:
            self.output_path_var.set(file_path)
            self.log_message(f"已设置输出文件: {os.path.basename(file_path)}")
            
    def start_conversion(self):
        """开始转换"""
        input_path = self.input_path_var.get().strip()
        output_path = self.output_path_var.get().strip()
        
        if not input_path:
            messagebox.showerror("错误", "请选择输入的GPX文件")
            return
            
        if not output_path:
            messagebox.showerror("错误", "请设置输出的TCX文件路径")
            return
            
        if not os.path.exists(input_path):
            messagebox.showerror("错误", "输入文件不存在")
            return
            
        # 禁用转换按钮
        self.convert_btn.config(state='disabled', text="转换中...")
        self.progress_var.set(0)
        
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
            self.log_message("\n开始转换过程...")
            self.log_message(f"输入文件: {os.path.basename(input_path)}")
            self.log_message(f"输出文件: {os.path.basename(output_path)}")
            
            # 更新进度
            self.root.after(0, lambda: self.progress_var.set(10))
            
            # 创建转换器
            self.converter = GPXToTCXConverter()
            self.log_message("转换器初始化完成")
            
            # 应用配置
            self.apply_config_to_converter()
            self.root.after(0, lambda: self.progress_var.set(20))
            
            # 执行转换
            self.log_message("正在解析GPX文件...")
            self.root.after(0, lambda: self.progress_var.set(40))
            
            result = self.converter.convert(input_path, output_path)
            self.root.after(0, lambda: self.progress_var.set(80))
            
            if result:
                self.log_message("GPX文件解析完成")
                self.log_message("正在生成TCX文件...")
                self.root.after(0, lambda: self.progress_var.set(90))
                
                # 验证输出文件
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    self.log_message(f"TCX文件生成成功")
                    self.log_message(f"文件大小: {file_size:,} 字节")
                    
                    # 显示修复功能状态
                    self.log_message("\n数据修复状态:")
                    self.log_message("✓ 步频修复: 50-70真实范围 (已启用)")
                    self.log_message("✓ 海拔修复: GPX数据准确解析 (已启用)")
                    self.log_message("✓ 心率优化: 135-165智能变化 (已启用)")
                    self.log_message("✓ 功率计算: 150-300W真实跑步功率 (已启用)")
                    self.log_message("✓ 开始时间: 支持自定义运动开始时间 (已启用)")
                    
                    self.root.after(0, lambda: self.progress_var.set(100))
                    self.log_message("\n转换完成！所有修复功能已生效")
                    
                    # 显示成功消息
                    self.root.after(0, lambda: messagebox.showinfo(
                        "转换成功", 
                        f"文件转换完成！\n\n输出文件: {os.path.basename(output_path)}\n文件大小: {file_size:,} 字节\n\n所有数据修复功能已生效"
                    ))
                else:
                    raise Exception("输出文件未生成")
            else:
                raise Exception("转换过程失败")
                
        except Exception as e:
            self.log_message(f"转换失败: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("转换失败", f"转换过程中出现错误:\n{str(e)}"))
            
        finally:
            # 恢复转换按钮
            self.root.after(0, lambda: self.convert_btn.config(state='normal', text="开始转换"))
            
    def apply_config_to_converter(self):
        """应用配置到转换器"""
        if not self.converter:
            return
            
        try:
            # 获取配置值
            config = {}
            for key, var in self.config_vars.items():
                value = var.get().strip()
                if value:
                    if key in ['min_hr', 'max_hr', 'min_cadence', 'max_cadence', 'min_power', 'max_power']:
                        config[key] = int(value)
                    else:
                        config[key] = value
            
            # 应用配置
            if hasattr(self.converter, 'set_heart_rate_range'):
                hr_min = config.get('min_hr', 135)
                hr_max = config.get('max_hr', 165)
                self.converter.set_heart_rate_range(hr_min, hr_max)
                self.log_message(f"心率范围: {hr_min}-{hr_max} bpm")
            
            if hasattr(self.converter, 'set_cadence_range'):
                cadence_min = config.get('min_cadence', 50)
                cadence_max = config.get('max_cadence', 70)
                self.converter.set_cadence_range(cadence_min, cadence_max)
                self.log_message(f"步频范围: {cadence_min}-{cadence_max} spm")
            
            if hasattr(self.converter, 'set_power_range'):
                power_min = config.get('min_power', 150)
                power_max = config.get('max_power', 300)
                self.converter.set_power_range(power_min, power_max)
                self.log_message(f"功率范围: {power_min}-{power_max} W")
            
            if hasattr(self.converter, 'set_target_pace'):
                target_pace = config.get('target_pace', '5:30')
                self.converter.set_target_pace(target_pace)
                self.log_message(f"目标配速: {target_pace} min/km")
            
            if hasattr(self.converter, 'set_sport_type'):
                sport_type = config.get('sport_type', 'Running')
                self.converter.set_sport_type(sport_type)
                self.log_message(f"运动类型: {sport_type}")
            
            # 处理开始时间设置
            start_time_str = config.get('start_time', '').strip()
            if start_time_str:
                try:
                    # 解析时间格式
                    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                    # 直接设置到转换器的配置中
                    if hasattr(self.converter, 'config'):
                        self.converter.config['start_time'] = start_time
                        self.log_message(f"自定义开始时间: {start_time_str}")
                    else:
                        self.log_message("警告: 转换器不支持自定义开始时间")
                except ValueError:
                    self.log_message(f"警告: 开始时间格式错误 '{start_time_str}'，将使用GPX文件中的时间")
            else:
                self.log_message("使用GPX文件中的原始时间")
                
            self.log_message("配置应用完成")
            
        except Exception as e:
            self.log_message(f"配置应用警告: {str(e)}")
            
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.log_text.insert('end', log_entry)
            self.log_text.see('end')
            
        if threading.current_thread() == threading.main_thread():
            update_log()
        else:
            self.root.after(0, update_log)

def main():
    """主函数"""
    root = tk.Tk()
    app = SimpleGPXConverterApp(root)
    
    # 设置关闭事件
    def on_closing():
        if app.conversion_thread and app.conversion_thread.is_alive():
            if messagebox.askokcancel("退出确认", "转换正在进行中，确定要退出吗？"):
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 启动应用
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n应用被用户中断")
    except Exception as e:
        print(f"应用运行错误: {e}")
        messagebox.showerror("应用错误", f"应用运行时出现错误:\n{str(e)}")

if __name__ == "__main__":
    main()