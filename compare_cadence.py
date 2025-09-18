#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比真实文件和生成文件的平均步频数据
"""

import xml.etree.ElementTree as ET
import re

def extract_cadence_data(file_path):
    """提取TCX文件中的步频相关数据"""
    print(f"\n📁 分析文件: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取平均步频
        avg_cadence_match = re.search(r'<ns3:AvgRunCadence>(\d+)</ns3:AvgRunCadence>', content)
        avg_cadence = avg_cadence_match.group(1) if avg_cadence_match else "未找到"
        
        # 提取最大步频
        max_cadence_match = re.search(r'<ns3:MaxRunCadence>(\d+)</ns3:MaxRunCadence>', content)
        max_cadence = max_cadence_match.group(1) if max_cadence_match else "未找到"
        
        # 统计轨迹点步频
        cadence_values = []
        cadence_matches = re.findall(r'<ns3:RunCadence>(\d+)</ns3:RunCadence>', content)
        for match in cadence_matches:
            try:
                cadence_values.append(int(match))
            except ValueError:
                pass
        
        # 检查LX扩展是否存在
        has_lx_extension = '<ns3:LX>' in content
        
        # 提取LX扩展内容
        lx_content = ""
        if has_lx_extension:
            lx_match = re.search(r'<ns3:LX>(.*?)</ns3:LX>', content, re.DOTALL)
            if lx_match:
                lx_content = lx_match.group(1).strip()
        
        print(f"📊 步频数据分析:")
        print(f"   - 平均步频: {avg_cadence} spm")
        print(f"   - 最大步频: {max_cadence} spm")
        print(f"   - LX扩展: {'✅ 存在' if has_lx_extension else '❌ 不存在'}")
        
        if cadence_values:
            non_zero_values = [v for v in cadence_values if v > 0]
            zero_values = [v for v in cadence_values if v == 0]
            
            print(f"   - 轨迹点总数: {len(cadence_values)}")
            print(f"   - 非零步频点: {len(non_zero_values)} 个")
            print(f"   - 零步频点: {len(zero_values)} 个")
            
            if non_zero_values:
                actual_avg = sum(non_zero_values) / len(non_zero_values)
                print(f"   - 实际平均步频: {actual_avg:.1f} spm")
                print(f"   - 步频范围: {min(non_zero_values)}-{max(non_zero_values)} spm")
        
        if lx_content:
            print(f"\n📋 LX扩展详细内容:")
            for line in lx_content.split('\n'):
                if line.strip():
                    print(f"     {line.strip()}")
        
        return {
            'avg_cadence': avg_cadence,
            'max_cadence': max_cadence,
            'has_lx_extension': has_lx_extension,
            'cadence_values': cadence_values,
            'lx_content': lx_content
        }
        
    except Exception as e:
        print(f"❌ 分析文件失败: {e}")
        return None

def compare_files():
    """对比两个文件的步频数据"""
    print("🔍 对比TCX文件的平均步频数据")
    print("=" * 50)
    
    # 分析真实文件
    real_data = extract_cadence_data('/Users/huangjiawei/Downloads/0908/真实.tcx')
    
    # 分析生成文件
    generated_data = extract_cadence_data('/Users/huangjiawei/Downloads/0908/GPX转TCX应用/0918.tcx')
    
    if real_data and generated_data:
        print("\n📈 对比结果:")
        print("=" * 30)
        
        # 对比平均步频
        print(f"平均步频:")
        print(f"   真实文件: {real_data['avg_cadence']} spm")
        print(f"   生成文件: {generated_data['avg_cadence']} spm")
        
        if real_data['avg_cadence'] == generated_data['avg_cadence']:
            print(f"   ✅ 平均步频一致")
        else:
            print(f"   ⚠️  平均步频不同")
        
        # 对比最大步频
        print(f"\n最大步频:")
        print(f"   真实文件: {real_data['max_cadence']} spm")
        print(f"   生成文件: {generated_data['max_cadence']} spm")
        
        # 对比LX扩展
        print(f"\nLX扩展:")
        print(f"   真实文件: {'✅ 存在' if real_data['has_lx_extension'] else '❌ 不存在'}")
        print(f"   生成文件: {'✅ 存在' if generated_data['has_lx_extension'] else '❌ 不存在'}")
        
        # 检查可能的问题
        print(f"\n🔧 问题诊断:")
        
        if not generated_data['has_lx_extension']:
            print(f"   ❌ 生成文件缺少LX扩展")
        elif generated_data['avg_cadence'] == "未找到":
            print(f"   ❌ 生成文件LX扩展中缺少AvgRunCadence字段")
        elif generated_data['avg_cadence'] == "0":
            print(f"   ❌ 生成文件平均步频为0")
        else:
            print(f"   ✅ 生成文件包含正确的平均步频数据")
            print(f"   💡 可能是TCX查看器的兼容性问题")
        
        # 提供解决建议
        print(f"\n💡 建议:")
        if generated_data['has_lx_extension'] and generated_data['avg_cadence'] != "未找到" and generated_data['avg_cadence'] != "0":
            print(f"   1. 生成的TCX文件数据完整，包含平均步频")
            print(f"   2. 尝试使用不同的TCX查看器或应用程序")
            print(f"   3. 检查查看器是否支持ns3:LX扩展")
        else:
            print(f"   1. 需要修复TCX生成逻辑")
            print(f"   2. 确保正确计算和添加平均步频")

if __name__ == '__main__':
    compare_files()