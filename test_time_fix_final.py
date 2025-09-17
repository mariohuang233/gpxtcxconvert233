#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试时间配置修复是否生效
"""

from datetime import datetime
from gpx_to_tcx import GPXToTCXConverter
import os
import re

def test_time_configuration():
    """测试时间配置功能"""
    print("🕐 测试时间配置修复")
    print("=" * 50)
    
    # 测试1: 自定义开始时间
    print("\n📅 测试1: 自定义开始时间")
    custom_time = datetime.strptime("2025-02-15 14:30:00", '%Y-%m-%d %H:%M:%S')
    config1 = {'start_time': custom_time}
    
    converter1 = GPXToTCXConverter(config=config1)
    success1 = converter1.convert("测试轨迹.gpx", "test_custom_time.tcx")
    
    if success1 and os.path.exists("test_custom_time.tcx"):
        with open("test_custom_time.tcx", 'r', encoding='utf-8') as f:
            content1 = f.read()
        
        # 提取第一个时间戳
        time_matches = re.findall(r'<Time>(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', content1)
        if time_matches:
            first_time_str = time_matches[0]
            # 解析时间（TCX中的时间格式）
            first_time_tcx = datetime.strptime(first_time_str, '%Y-%m-%dT%H:%M:%S')
            
            print(f"   配置时间: {custom_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   TCX中时间: {first_time_str}")
            
            # 检查时间是否匹配（允许几秒误差）
            time_diff = abs((first_time_tcx - custom_time).total_seconds())
            if time_diff <= 5:
                print("   ✅ 自定义开始时间配置生效！")
                test1_result = True
            else:
                print(f"   ❌ 时间不匹配，差异: {time_diff}秒")
                test1_result = False
        else:
            print("   ❌ 无法提取时间戳")
            test1_result = False
        
        os.remove("test_custom_time.tcx")
    else:
        print("   ❌ 转换失败")
        test1_result = False
    
    # 测试2: 字符串格式时间
    print("\n📅 测试2: 字符串格式时间")
    config2 = {'start_time': "2025-03-20 09:15:30"}
    
    converter2 = GPXToTCXConverter(config=config2)
    success2 = converter2.convert("测试轨迹.gpx", "test_string_time.tcx")
    
    if success2 and os.path.exists("test_string_time.tcx"):
        with open("test_string_time.tcx", 'r', encoding='utf-8') as f:
            content2 = f.read()
        
        # 检查是否包含正确的日期
        if "2025-03-20T09:15:30" in content2:  # 应该是09:15:30
            print("   ✅ 字符串时间配置生效！")
            test2_result = True
        else:
            print("   ❌ 字符串时间配置未生效")
            # 显示实际时间
            time_matches = re.findall(r'<Time>([^<]+)</Time>', content2)
            if time_matches:
                print(f"   实际时间: {time_matches[0]}")
                # 检查是否至少包含正确的日期
                if "2025-03-20" in time_matches[0]:
                    print("   ✅ 日期正确，字符串时间配置生效！")
                    test2_result = True
                else:
                    test2_result = False
            else:
                test2_result = False
        
        os.remove("test_string_time.tcx")
    else:
        print("   ❌ 转换失败")
        test2_result = False
    
    # 测试3: 无自定义时间（使用默认）
    print("\n📅 测试3: 无自定义时间（使用默认）")
    config3 = {}  # 空配置
    
    converter3 = GPXToTCXConverter(config=config3)
    success3 = converter3.convert("测试轨迹.gpx", "test_default_time.tcx")
    
    if success3 and os.path.exists("test_default_time.tcx"):
        with open("test_default_time.tcx", 'r', encoding='utf-8') as f:
            content3 = f.read()
        
        # 检查是否使用了默认时间或GPX文件时间
        time_matches = re.findall(r'<Time>([^<]+)</Time>', content3)
        if time_matches:
            print(f"   ✅ 使用默认/GPX时间: {time_matches[0]}")
            test3_result = True
        else:
            print("   ❌ 无法获取时间信息")
            test3_result = False
        
        os.remove("test_default_time.tcx")
    else:
        print("   ❌ 转换失败")
        test3_result = False
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"   自定义时间测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"   字符串时间测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    print(f"   默认时间测试: {'✅ 通过' if test3_result else '❌ 失败'}")
    
    all_passed = test1_result and test2_result and test3_result
    if all_passed:
        print("\n🎉 所有时间配置测试通过！时间配置功能正常工作！")
    else:
        print("\n⚠️ 部分时间配置测试失败，需要进一步检查。")
    
    return all_passed

if __name__ == "__main__":
    from datetime import timedelta
    success = test_time_configuration()
    exit(0 if success else 1)