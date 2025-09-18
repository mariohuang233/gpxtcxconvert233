#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比TCX文件的字段结构和定义
"""

import xml.etree.ElementTree as ET
import re
from collections import defaultdict

def extract_xml_structure(content):
    """提取XML结构信息"""
    structure = {
        'namespaces': {},
        'root_attributes': {},
        'activity_attributes': {},
        'lap_fields': set(),
        'trackpoint_fields': set(),
        'extensions_fields': set(),
        'creator_fields': set(),
        'data_types': {}
    }
    
    # 提取命名空间
    ns_matches = re.findall(r'xmlns:?([^=]*)="([^"]+)"', content)
    for prefix, uri in ns_matches:
        structure['namespaces'][prefix or 'default'] = uri
    
    # 提取根元素属性
    root_match = re.search(r'<TrainingCenterDatabase([^>]*)>', content)
    if root_match:
        attrs = re.findall(r'(\w+)="([^"]+)"', root_match.group(1))
        structure['root_attributes'] = dict(attrs)
    
    # 提取Activity属性
    activity_match = re.search(r'<Activity([^>]*)>', content)
    if activity_match:
        attrs = re.findall(r'(\w+)="([^"]+)"', activity_match.group(1))
        structure['activity_attributes'] = dict(attrs)
    
    # 提取Lap字段
    lap_section = re.search(r'<Lap[^>]*>(.*?)</Lap>', content, re.DOTALL)
    if lap_section:
        lap_content = lap_section.group(1)
        # 查找所有直接子元素
        lap_fields = re.findall(r'<(\w+)[^>]*>', lap_content)
        structure['lap_fields'] = set(lap_fields)
    
    # 提取Trackpoint字段
    trackpoint_matches = re.findall(r'<Trackpoint>(.*?)</Trackpoint>', content, re.DOTALL)
    if trackpoint_matches:
        # 分析第一个trackpoint的结构
        tp_content = trackpoint_matches[0]
        tp_fields = re.findall(r'<(\w+)[^>]*>', tp_content)
        structure['trackpoint_fields'] = set(tp_fields)
    
    # 提取Extensions字段
    ext_matches = re.findall(r'<Extensions>(.*?)</Extensions>', content, re.DOTALL)
    for ext_content in ext_matches:
        ext_fields = re.findall(r'<([^>\s]+)[^>]*>', ext_content)
        structure['extensions_fields'].update(ext_fields)
    
    # 提取Creator字段
    creator_match = re.search(r'<Creator[^>]*>(.*?)</Creator>', content, re.DOTALL)
    if creator_match:
        creator_content = creator_match.group(1)
        creator_fields = re.findall(r'<(\w+)[^>]*>', creator_content)
        structure['creator_fields'] = set(creator_fields)
    
    return structure

def analyze_field_values(content):
    """分析字段值的格式和类型"""
    field_analysis = {}
    
    # 分析时间格式
    time_matches = re.findall(r'<Time>([^<]+)</Time>', content)
    if time_matches:
        field_analysis['Time'] = {
            'sample_values': time_matches[:3],
            'format': 'ISO8601' if 'T' in time_matches[0] else 'Unknown'
        }
    
    # 分析数值字段
    numeric_fields = ['TotalTimeSeconds', 'DistanceMeters', 'MaximumSpeed', 'Calories', 
                     'LatitudeDegrees', 'LongitudeDegrees', 'AltitudeMeters']
    
    for field in numeric_fields:
        matches = re.findall(f'<{field}>([^<]+)</{field}>', content)
        if matches:
            field_analysis[field] = {
                'sample_values': matches[:3],
                'type': 'float' if '.' in matches[0] else 'int'
            }
    
    # 分析扩展字段
    ext_fields = ['ns3:AvgSpeed', 'ns3:AvgRunCadence', 'ns3:MaxRunCadence', 
                 'ns3:AvgWatts', 'ns3:MaxWatts', 'ns3:Speed', 'ns3:RunCadence', 'ns3:Watts']
    
    for field in ext_fields:
        matches = re.findall(f'<{field}>([^<]+)</{field}>', content)
        if matches:
            field_analysis[field] = {
                'sample_values': matches[:3],
                'type': 'float' if '.' in matches[0] else 'int'
            }
    
    return field_analysis

def compare_field_structures():
    """对比两个文件的字段结构"""
    real_file = '/Users/huangjiawei/Downloads/0908/真实.tcx'
    generated_file = '/Users/huangjiawei/Downloads/0908/0918.tcx'
    
    print("🔍 对比TCX文件的字段结构和定义...")
    print("="*60)
    
    try:
        # 读取文件
        with open(real_file, 'r', encoding='utf-8') as f:
            real_content = f.read()
        
        with open(generated_file, 'r', encoding='utf-8') as f:
            generated_content = f.read()
        
        # 提取结构
        real_structure = extract_xml_structure(real_content)
        generated_structure = extract_xml_structure(generated_content)
        
        # 分析字段值
        real_values = analyze_field_values(real_content)
        generated_values = analyze_field_values(generated_content)
        
        print("📋 1. 命名空间对比:")
        print("   真实文件命名空间:")
        for prefix, uri in real_structure['namespaces'].items():
            print(f"     {prefix}: {uri}")
        
        print("   生成文件命名空间:")
        for prefix, uri in generated_structure['namespaces'].items():
            print(f"     {prefix}: {uri}")
        
        # 检查命名空间差异
        ns_diff = set(real_structure['namespaces'].items()) ^ set(generated_structure['namespaces'].items())
        if ns_diff:
            print("   ⚠️ 命名空间差异:")
            for item in ns_diff:
                print(f"     {item}")
        else:
            print("   ✅ 命名空间一致")
        
        print()
        
        print("📋 2. 根元素属性对比:")
        print(f"   真实文件: {real_structure['root_attributes']}")
        print(f"   生成文件: {generated_structure['root_attributes']}")
        
        root_diff = set(real_structure['root_attributes'].items()) ^ set(generated_structure['root_attributes'].items())
        if root_diff:
            print(f"   ⚠️ 根元素属性差异: {root_diff}")
        else:
            print("   ✅ 根元素属性一致")
        
        print()
        
        print("📋 3. Activity属性对比:")
        print(f"   真实文件: {real_structure['activity_attributes']}")
        print(f"   生成文件: {generated_structure['activity_attributes']}")
        
        activity_diff = set(real_structure['activity_attributes'].items()) ^ set(generated_structure['activity_attributes'].items())
        if activity_diff:
            print(f"   ⚠️ Activity属性差异: {activity_diff}")
        else:
            print("   ✅ Activity属性一致")
        
        print()
        
        print("📋 4. Lap字段对比:")
        print(f"   真实文件Lap字段: {sorted(real_structure['lap_fields'])}")
        print(f"   生成文件Lap字段: {sorted(generated_structure['lap_fields'])}")
        
        lap_only_real = real_structure['lap_fields'] - generated_structure['lap_fields']
        lap_only_generated = generated_structure['lap_fields'] - real_structure['lap_fields']
        
        if lap_only_real:
            print(f"   ⚠️ 真实文件独有字段: {sorted(lap_only_real)}")
        if lap_only_generated:
            print(f"   ⚠️ 生成文件独有字段: {sorted(lap_only_generated)}")
        if not lap_only_real and not lap_only_generated:
            print("   ✅ Lap字段完全一致")
        
        print()
        
        print("📋 5. Trackpoint字段对比:")
        print(f"   真实文件Trackpoint字段: {sorted(real_structure['trackpoint_fields'])}")
        print(f"   生成文件Trackpoint字段: {sorted(generated_structure['trackpoint_fields'])}")
        
        tp_only_real = real_structure['trackpoint_fields'] - generated_structure['trackpoint_fields']
        tp_only_generated = generated_structure['trackpoint_fields'] - real_structure['trackpoint_fields']
        
        if tp_only_real:
            print(f"   ⚠️ 真实文件独有字段: {sorted(tp_only_real)}")
        if tp_only_generated:
            print(f"   ⚠️ 生成文件独有字段: {sorted(tp_only_generated)}")
        if not tp_only_real and not tp_only_generated:
            print("   ✅ Trackpoint字段完全一致")
        
        print()
        
        print("📋 6. Extensions字段对比:")
        print(f"   真实文件Extensions字段: {sorted(real_structure['extensions_fields'])}")
        print(f"   生成文件Extensions字段: {sorted(generated_structure['extensions_fields'])}")
        
        ext_only_real = real_structure['extensions_fields'] - generated_structure['extensions_fields']
        ext_only_generated = generated_structure['extensions_fields'] - real_structure['extensions_fields']
        
        if ext_only_real:
            print(f"   ⚠️ 真实文件独有字段: {sorted(ext_only_real)}")
        if ext_only_generated:
            print(f"   ⚠️ 生成文件独有字段: {sorted(ext_only_generated)}")
        if not ext_only_real and not ext_only_generated:
            print("   ✅ Extensions字段完全一致")
        
        print()
        
        print("📋 7. Creator字段对比:")
        print(f"   真实文件Creator字段: {sorted(real_structure['creator_fields'])}")
        print(f"   生成文件Creator字段: {sorted(generated_structure['creator_fields'])}")
        
        creator_only_real = real_structure['creator_fields'] - generated_structure['creator_fields']
        creator_only_generated = generated_structure['creator_fields'] - real_structure['creator_fields']
        
        if creator_only_real:
            print(f"   ⚠️ 真实文件独有字段: {sorted(creator_only_real)}")
        if creator_only_generated:
            print(f"   ⚠️ 生成文件独有字段: {sorted(creator_only_generated)}")
        if not creator_only_real and not creator_only_generated:
            print("   ✅ Creator字段完全一致")
        
        print()
        
        print("📋 8. 字段值格式对比:")
        
        # 对比共同字段的值格式
        common_fields = set(real_values.keys()) & set(generated_values.keys())
        
        for field in sorted(common_fields):
            real_val = real_values[field]
            generated_val = generated_values[field]
            
            print(f"   {field}:")
            print(f"     真实文件: {real_val['sample_values'][0]} (类型: {real_val.get('type', 'unknown')})")
            print(f"     生成文件: {generated_val['sample_values'][0]} (类型: {generated_val.get('type', 'unknown')})")
            
            if real_val.get('type') != generated_val.get('type'):
                print(f"     ⚠️ 数据类型不同")
            
            # 检查格式差异
            if field == 'Time':
                real_format = real_val.get('format', 'Unknown')
                generated_format = generated_val.get('format', 'Unknown')
                if real_format != generated_format:
                    print(f"     ⚠️ 时间格式不同: {real_format} vs {generated_format}")
        
        print()
        
        print("📋 9. XML声明和编码对比:")
        
        # 提取XML声明
        real_declaration = re.search(r'<\?xml[^>]+\?>', real_content)
        generated_declaration = re.search(r'<\?xml[^>]+\?>', generated_content)
        
        if real_declaration and generated_declaration:
            real_decl = real_declaration.group(0)
            generated_decl = generated_declaration.group(0)
            
            print(f"   真实文件: {real_decl}")
            print(f"   生成文件: {generated_decl}")
            
            if real_decl != generated_decl:
                print("   ⚠️ XML声明不同")
            else:
                print("   ✅ XML声明一致")
        
        print()
        
        print("📋 10. 特殊字段检查:")
        
        # 检查特殊字段
        special_checks = [
            ('SubSport', '<ns3:SubSport>'),
            ('TPX扩展', '<ns3:TPX>'),
            ('LX扩展', '<ns3:LX>'),
            ('心率区间', '<HeartRateBpm>'),
            ('位置信息', '<Position>')
        ]
        
        for name, pattern in special_checks:
            real_has = pattern in real_content
            generated_has = pattern in generated_content
            
            status = "✅" if real_has == generated_has else "⚠️"
            print(f"   {name}: 真实文件{'有' if real_has else '无'}, 生成文件{'有' if generated_has else '无'} {status}")
        
        print()
        
        # 总结
        print("📝 结构差异总结:")
        
        issues = []
        
        if ns_diff:
            issues.append("命名空间定义不同")
        
        if root_diff:
            issues.append("根元素属性不同")
        
        if activity_diff:
            issues.append("Activity属性不同")
        
        if lap_only_real or lap_only_generated:
            issues.append("Lap字段结构不同")
        
        if tp_only_real or tp_only_generated:
            issues.append("Trackpoint字段结构不同")
        
        if ext_only_real or ext_only_generated:
            issues.append("Extensions字段结构不同")
        
        if creator_only_real or creator_only_generated:
            issues.append("Creator字段结构不同")
        
        # 检查SubSport字段
        if '<ns3:SubSport>' in generated_content and '<ns3:SubSport>' not in real_content:
            issues.append("生成文件包含额外的SubSport字段")
        
        if issues:
            print("   发现以下结构差异:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("   ✅ 字段结构基本一致")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ 分析过程出错: {e}")
        return False

if __name__ == '__main__':
    success = compare_field_structures()
    if success:
        print("\n🎊 字段结构对比完成，结构基本一致！")
        exit(0)
    else:
        print("\n⚠️ 发现字段结构差异，需要调整！")
        exit(1)