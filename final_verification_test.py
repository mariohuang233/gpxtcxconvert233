#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证测试：确保不再出现2024-12-25硬编码时间
"""

from datetime import datetime
from gpx_to_tcx import GPXToTCXConverter
import os
import re

def final_verification():
    """最终验证测试"""
    print("🔍 最终验证：确保不再出现2024-12-25硬编码时间")
    print("=" * 60)
    
    # 测试1: 正常的自定义时间
    print("\n📅 测试1: 正常自定义时间")
    config1 = {'start_time': datetime(2025, 3, 15, 14, 20, 30)}
    converter1 = GPXToTCXConverter(config=config1)
    success1 = converter1.convert("测试轨迹.gpx", "final_test1.tcx")
    
    result1 = check_tcx_time("final_test1.tcx", "2025-03-15T14:20:30")
    
    # 测试2: 字符串格式时间
    print("\n📅 测试2: 字符串格式时间")
    config2 = {'start_time': "2025-07-20 09:30:45"}
    converter2 = GPXToTCXConverter(config=config2)
    success2 = converter2.convert("测试轨迹.gpx", "final_test2.tcx")
    
    result2 = check_tcx_time("final_test2.tcx", "2025-07-20T09:30:45")
    
    # 测试3: 无效时间格式（应该使用当前时间，不是2024-12-25）
    print("\n📅 测试3: 无效时间格式")
    config3 = {'start_time': "invalid_time_format"}
    converter3 = GPXToTCXConverter(config=config3)
    success3 = converter3.convert("测试轨迹.gpx", "final_test3.tcx")
    
    result3 = check_no_hardcoded_time("final_test3.tcx")
    
    # 测试4: 空配置（应该使用GPX时间或当前时间，不是2024-12-25）
    print("\n📅 测试4: 空配置")
    config4 = {}
    converter4 = GPXToTCXConverter(config=config4)
    success4 = converter4.convert("测试轨迹.gpx", "final_test4.tcx")
    
    result4 = check_no_hardcoded_time("final_test4.tcx")
    
    # 清理测试文件
    for i in range(1, 5):
        test_file = f"final_test{i}.tcx"
        if os.path.exists(test_file):
            os.remove(test_file)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 最终验证结果:")
    print(f"   测试1 (正常自定义时间): {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"   测试2 (字符串格式时间): {'✅ 通过' if result2 else '❌ 失败'}")
    print(f"   测试3 (无效时间格式): {'✅ 通过' if result3 else '❌ 失败'}")
    print(f"   测试4 (空配置): {'✅ 通过' if result4 else '❌ 失败'}")
    
    all_passed = result1 and result2 and result3 and result4
    
    if all_passed:
        print("\n🎉 最终验证通过！2024-12-25硬编码时间问题已彻底解决！")
    else:
        print("\n❌ 最终验证失败！仍然存在2024-12-25硬编码时间问题！")
    
    return all_passed

def check_tcx_time(filename, expected_time):
    """检查TCX文件中的时间是否符合预期"""
    if not os.path.exists(filename):
        print(f"   ❌ 文件 {filename} 不存在")
        return False
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    time_matches = re.findall(r'<Time>(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', content)
    if time_matches:
        actual_time = time_matches[0]
        print(f"   期望时间: {expected_time}")
        print(f"   实际时间: {actual_time}")
        
        if actual_time == expected_time:
            print("   ✅ 时间匹配正确")
            return True
        else:
            print("   ❌ 时间不匹配")
            return False
    else:
        print("   ❌ 无法提取时间戳")
        return False

def check_no_hardcoded_time(filename):
    """检查TCX文件中是否不包含硬编码的2024-12-25时间"""
    if not os.path.exists(filename):
        print(f"   ❌ 文件 {filename} 不存在")
        return False
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    time_matches = re.findall(r'<Time>(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', content)
    if time_matches:
        actual_time = time_matches[0]
        print(f"   实际时间: {actual_time}")
        
        if "2024-12-25" in actual_time:
            print("   ❌ 仍然使用硬编码的2024-12-25时间！")
            return False
        else:
            print("   ✅ 没有使用硬编码的2024-12-25时间")
            return True
    else:
        print("   ❌ 无法提取时间戳")
        return False

if __name__ == "__main__":
    success = final_verification()
    exit(0 if success else 1)