#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自定义开始时间功能
"""

from datetime import datetime
from gpx_to_tcx import GPXToTCXConverter
import os
import re

def test_custom_start_time():
    """测试自定义开始时间功能"""
    print("🔍 测试自定义开始时间功能")
    print("=" * 50)
    
    # 测试1: datetime对象格式的自定义时间
    print("\n📅 测试1: datetime对象格式")
    custom_time1 = datetime(2025, 8, 15, 14, 30, 45)
    config1 = {'start_time': custom_time1}
    converter1 = GPXToTCXConverter(config=config1)
    success1 = converter1.convert("测试轨迹.gpx", "test_custom1.tcx")
    
    result1 = check_tcx_start_time("test_custom1.tcx", "2025-08-15T14:30:45")
    
    # 测试2: 字符串格式的自定义时间
    print("\n📅 测试2: 字符串格式")
    config2 = {'start_time': "2025-11-20 09:15:30"}
    converter2 = GPXToTCXConverter(config=config2)
    success2 = converter2.convert("测试轨迹.gpx", "test_custom2.tcx")
    
    result2 = check_tcx_start_time("test_custom2.tcx", "2025-11-20T09:15:30")
    
    # 测试3: 无自定义时间（对照组）
    print("\n📅 测试3: 无自定义时间（对照组）")
    config3 = {}
    converter3 = GPXToTCXConverter(config=config3)
    success3 = converter3.convert("测试轨迹.gpx", "test_custom3.tcx")
    
    result3 = check_tcx_no_custom_time("test_custom3.tcx")
    
    # 清理测试文件
    for i in range(1, 4):
        test_file = f"test_custom{i}.tcx"
        if os.path.exists(test_file):
            os.remove(test_file)
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"   测试1 (datetime对象): {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"   测试2 (字符串格式): {'✅ 通过' if result2 else '❌ 失败'}")
    print(f"   测试3 (无自定义时间): {'✅ 通过' if result3 else '❌ 失败'}")
    
    all_passed = result1 and result2 and result3
    
    if all_passed:
        print("\n🎉 所有测试通过！自定义开始时间功能正常工作！")
    else:
        print("\n❌ 测试失败！自定义开始时间功能存在问题！")
    
    return all_passed

def check_tcx_start_time(filename, expected_start_time):
    """检查TCX文件中的开始时间是否符合预期"""
    if not os.path.exists(filename):
        print(f"   ❌ 文件 {filename} 不存在")
        return False
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取第一个时间戳（开始时间）
    time_matches = re.findall(r'<Time>(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', content)
    if time_matches:
        actual_start_time = time_matches[0]
        print(f"   期望开始时间: {expected_start_time}")
        print(f"   实际开始时间: {actual_start_time}")
        
        if actual_start_time == expected_start_time:
            print("   ✅ 开始时间匹配正确")
            return True
        else:
            print("   ❌ 开始时间不匹配")
            return False
    else:
        print("   ❌ 无法提取开始时间")
        return False

def check_tcx_no_custom_time(filename):
    """检查TCX文件中没有自定义时间时的行为"""
    if not os.path.exists(filename):
        print(f"   ❌ 文件 {filename} 不存在")
        return False
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取第一个时间戳
    time_matches = re.findall(r'<Time>(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', content)
    if time_matches:
        actual_start_time = time_matches[0]
        print(f"   实际开始时间: {actual_start_time}")
        
        # 检查是否使用了GPX文件中的时间或当前时间（不是硬编码的2024-12-25）
        if "2024-12-25" not in actual_start_time:
            print("   ✅ 没有使用硬编码时间，使用了GPX文件时间或当前时间")
            return True
        else:
            print("   ❌ 仍然使用硬编码的2024-12-25时间")
            return False
    else:
        print("   ❌ 无法提取开始时间")
        return False

if __name__ == "__main__":
    success = test_custom_start_time()
    exit(0 if success else 1)