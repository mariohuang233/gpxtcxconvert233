#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细分析Trackpoint字段差异
"""

import xml.etree.ElementTree as ET
import re
from collections import defaultdict

def analyze_trackpoint_fields():
    """详细分析Trackpoint字段差异"""
    real_file = '/Users/huangjiawei/Downloads/0908/真实.tcx'
    generated_file = '/Users/huangjiawei/Downloads/0908/0918.tcx'
    
    print("🔍 详细分析Trackpoint字段差异...")
    print("="*60)
    
    try:
        # 读取文件
        with open(real_file, 'r', encoding='utf-8') as f:
            real_content = f.read()
        
        with open(generated_file, 'r', encoding='utf-8') as f:
            generated_content = f.read()
        
        # 提取所有Trackpoint
        real_trackpoints = re.findall(r'<Trackpoint>(.*?)</Trackpoint>', real_content, re.DOTALL)
        generated_trackpoints = re.findall(r'<Trackpoint>(.*?)</Trackpoint>', generated_content, re.DOTALL)
        
        print(f"📊 Trackpoint数量:")
        print(f"   真实文件: {len(real_trackpoints)} 个")
        print(f"   生成文件: {len(generated_trackpoints)} 个")
        print()
        
        # 分析字段结构
        def extract_trackpoint_structure(trackpoints, name):
            """提取trackpoint结构"""
            all_fields = set()
            field_frequency = defaultdict(int)
            sample_structures = []
            
            for i, tp in enumerate(trackpoints[:5]):  # 分析前5个trackpoint
                fields = re.findall(r'<(\w+)[^>]*>', tp)
                tp_fields = set(fields)
                all_fields.update(tp_fields)
                
                for field in tp_fields:
                    field_frequency[field] += 1
                
                sample_structures.append({
                    'index': i,
                    'fields': sorted(tp_fields)
                })
            
            print(f"📋 {name} Trackpoint字段分析:")
            print(f"   所有字段: {sorted(all_fields)}")
            print(f"   字段频率:")
            for field, freq in sorted(field_frequency.items()):
                percentage = (freq / min(len(trackpoints), 5)) * 100
                print(f"     {field}: {freq}/5 ({percentage:.0f}%)")
            
            print(f"   前5个Trackpoint结构:")
            for struct in sample_structures:
                print(f"     #{struct['index']}: {struct['fields']}")
            
            return all_fields, field_frequency
        
        # 分析真实文件
        real_fields, real_freq = extract_trackpoint_structure(real_trackpoints, "真实文件")
        print()
        
        # 分析生成文件
        generated_fields, generated_freq = extract_trackpoint_structure(generated_trackpoints, "生成文件")
        print()
        
        # 对比差异
        print("🔍 字段差异分析:")
        
        only_real = real_fields - generated_fields
        only_generated = generated_fields - real_fields
        common_fields = real_fields & generated_fields
        
        if only_real:
            print(f"   ⚠️ 真实文件独有字段: {sorted(only_real)}")
        
        if only_generated:
            print(f"   ⚠️ 生成文件独有字段: {sorted(only_generated)}")
        
        print(f"   ✅ 共同字段: {sorted(common_fields)}")
        print()
        
        # 分析具体字段内容
        print("📋 字段内容对比:")
        
        def analyze_field_content(trackpoints, field_name, file_name):
            """分析特定字段的内容"""
            values = []
            for tp in trackpoints[:3]:  # 分析前3个
                match = re.search(f'<{field_name}[^>]*>([^<]*)</{field_name}>', tp)
                if match:
                    values.append(match.group(1))
                else:
                    values.append('N/A')
            return values
        
        # 分析关键字段
        key_fields = ['Time', 'Position', 'AltitudeMeters', 'DistanceMeters', 'HeartRateBpm', 'Extensions']
        
        for field in key_fields:
            if field in common_fields:
                real_values = analyze_field_content(real_trackpoints, field, "真实")
                generated_values = analyze_field_content(generated_trackpoints, field, "生成")
                
                print(f"   {field}:")
                print(f"     真实文件前3个值: {real_values}")
                print(f"     生成文件前3个值: {generated_values}")
        
        # 特别分析Extensions内容
        print()
        print("📋 Extensions内容详细对比:")
        
        def extract_extensions_content(trackpoints, file_name):
            """提取Extensions内容"""
            extensions_data = []
            for i, tp in enumerate(trackpoints[:3]):
                ext_match = re.search(r'<Extensions>(.*?)</Extensions>', tp, re.DOTALL)
                if ext_match:
                    ext_content = ext_match.group(1).strip()
                    # 提取所有扩展字段
                    ext_fields = re.findall(r'<([^>\s]+)[^>]*>([^<]*)</[^>]+>', ext_content)
                    extensions_data.append({
                        'index': i,
                        'raw': ext_content[:100] + '...' if len(ext_content) > 100 else ext_content,
                        'fields': ext_fields
                    })
                else:
                    extensions_data.append({
                        'index': i,
                        'raw': 'N/A',
                        'fields': []
                    })
            return extensions_data
        
        real_extensions = extract_extensions_content(real_trackpoints, "真实")
        generated_extensions = extract_extensions_content(generated_trackpoints, "生成")
        
        print("   真实文件Extensions:")
        for ext in real_extensions:
            print(f"     #{ext['index']}: {ext['fields']}")
        
        print("   生成文件Extensions:")
        for ext in generated_extensions:
            print(f"     #{ext['index']}: {ext['fields']}")
        
        print()
        
        # 分析Position字段结构
        print("📋 Position字段结构对比:")
        
        def analyze_position_structure(trackpoints, file_name):
            """分析Position字段结构"""
            position_structures = []
            for i, tp in enumerate(trackpoints[:3]):
                pos_match = re.search(r'<Position>(.*?)</Position>', tp, re.DOTALL)
                if pos_match:
                    pos_content = pos_match.group(1)
                    pos_fields = re.findall(r'<(\w+)[^>]*>([^<]*)</\w+>', pos_content)
                    position_structures.append({
                        'index': i,
                        'fields': pos_fields
                    })
                else:
                    position_structures.append({
                        'index': i,
                        'fields': []
                    })
            return position_structures
        
        real_positions = analyze_position_structure(real_trackpoints, "真实")
        generated_positions = analyze_position_structure(generated_trackpoints, "生成")
        
        print("   真实文件Position结构:")
        for pos in real_positions:
            print(f"     #{pos['index']}: {pos['fields']}")
        
        print("   生成文件Position结构:")
        for pos in generated_positions:
            print(f"     #{pos['index']}: {pos['fields']}")
        
        print()
        
        # 总结差异
        print("📝 Trackpoint差异总结:")
        
        issues = []
        
        if only_real:
            issues.append(f"真实文件包含额外字段: {', '.join(sorted(only_real))}")
        
        if only_generated:
            issues.append(f"生成文件包含额外字段: {', '.join(sorted(only_generated))}")
        
        # 检查字段频率差异
        for field in common_fields:
            real_freq_val = real_freq.get(field, 0)
            generated_freq_val = generated_freq.get(field, 0)
            if real_freq_val != generated_freq_val:
                issues.append(f"字段 {field} 出现频率不同: 真实({real_freq_val}/5) vs 生成({generated_freq_val}/5)")
        
        if issues:
            print("   发现以下差异:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("   ✅ Trackpoint结构基本一致")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ 分析过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = analyze_trackpoint_fields()
    if success:
        print("\n🎊 Trackpoint字段分析完成，结构基本一致！")
        exit(0)
    else:
        print("\n⚠️ 发现Trackpoint字段差异，需要调整！")
        exit(1)