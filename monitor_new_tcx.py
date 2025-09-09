#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import glob
from datetime import datetime

def monitor_new_tcx_files():
    """监控新生成的TCX文件"""
    
    print("=== 监控新生成的TCX文件 ===")
    print("等待用户通过GUI应用生成新的TCX文件...")
    print("(请在GUI应用中选择GPX文件并点击转换)")
    print("按Ctrl+C停止监控\n")
    
    # 记录当前已存在的TCX文件
    downloads_dir = '/Users/huangjiawei/Downloads'
    existing_files = set()
    
    for f in os.listdir(downloads_dir):
        if f.endswith('.tcx'):
            existing_files.add(f)
    
    print(f"📁 当前已有 {len(existing_files)} 个TCX文件")
    
    try:
        while True:
            # 检查新文件
            current_files = set()
            for f in os.listdir(downloads_dir):
                if f.endswith('.tcx'):
                    current_files.add(f)
            
            # 找出新文件
            new_files = current_files - existing_files
            
            if new_files:
                for new_file in new_files:
                    print(f"\n🆕 发现新文件: {new_file}")
                    
                    file_path = os.path.join(downloads_dir, new_file)
                    
                    # 等待文件写入完成
                    time.sleep(1)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        print(f"📊 文件大小: {len(content)} 字符")
                        
                        # 检查平均步频
                        avg_cadence_found = False
                        if '<ns3:AvgRunCadence>' in content:
                            start = content.find('<ns3:AvgRunCadence>') + len('<ns3:AvgRunCadence>')
                            end = content.find('</ns3:AvgRunCadence>')
                            avg_cadence = content[start:end]
                            print(f"✅ 平均步频: {avg_cadence} spm")
                            avg_cadence_found = True
                            
                            if avg_cadence == '0':
                                print(f"⚠️  平均步频为0！")
                            else:
                                print(f"🎉 平均步频正常！")
                        else:
                            print(f"❌ 缺少平均步频字段")
                        
                        # 检查最大步频
                        if '<ns3:MaxRunCadence>' in content:
                            start = content.find('<ns3:MaxRunCadence>') + len('<ns3:MaxRunCadence>')
                            end = content.find('</ns3:MaxRunCadence>')
                            max_cadence = content[start:end]
                            print(f"✅ 最大步频: {max_cadence} spm")
                        else:
                            print(f"❌ 缺少最大步频字段")
                        
                        # 检查LX扩展
                        if '<ns3:LX>' in content:
                            print(f"✅ 包含LX扩展")
                            
                            # 提取LX内容
                            lx_start = content.find('<ns3:LX>')
                            lx_end = content.find('</ns3:LX>') + len('</ns3:LX>')
                            if lx_start != -1 and lx_end != -1:
                                lx_content = content[lx_start:lx_end]
                                print(f"📋 LX扩展内容:")
                                for line in lx_content.split('\n'):
                                    if line.strip():
                                        print(f"     {line.strip()}")
                        else:
                            print(f"❌ 缺少LX扩展")
                        
                        # 统计轨迹点步频
                        cadence_values = []
                        lines = content.split('\n')
                        
                        for line in lines:
                            if '<ns3:RunCadence>' in line:
                                start = line.find('<ns3:RunCadence>') + len('<ns3:RunCadence>')
                                end = line.find('</ns3:RunCadence>')
                                value = line[start:end]
                                try:
                                    cadence_values.append(int(value))
                                except ValueError:
                                    pass
                        
                        if cadence_values:
                            non_zero_values = [v for v in cadence_values if v > 0]
                            zero_values = [v for v in cadence_values if v == 0]
                            
                            print(f"📈 轨迹点步频统计:")
                            print(f"   - 总点数: {len(cadence_values)}")
                            print(f"   - 非零值: {len(non_zero_values)} 个")
                            print(f"   - 零值: {len(zero_values)} 个")
                            
                            if non_zero_values:
                                print(f"   - 范围: {min(non_zero_values)}-{max(non_zero_values)}")
                                print(f"   - 平均: {sum(non_zero_values)/len(non_zero_values):.1f}")
                        
                        # 判断修复是否成功
                        if avg_cadence_found and avg_cadence != '0':
                            print(f"\n🎊 修复成功！TCX文件包含正确的平均步频数据")
                        else:
                            print(f"\n❌ 修复失败！TCX文件仍然缺少平均步频或数据为0")
                            
                    except Exception as e:
                        print(f"❌ 读取文件出错: {e}")
                
                # 更新已存在文件列表
                existing_files = current_files
            
            # 等待一段时间再检查
            time.sleep(2)
            
    except KeyboardInterrupt:
        print(f"\n👋 监控已停止")

if __name__ == '__main__':
    monitor_new_tcx_files()