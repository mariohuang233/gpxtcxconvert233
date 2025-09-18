#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试网页开始时间配置是否完全生效
验证开始时间不受GPX文件或其他固定值影响
"""

from datetime import datetime
from gpx_to_tcx import GPXToTCXConverter
import os
import re

def test_web_start_time_priority():
    """测试网页开始时间配置的优先级"""
    print("🌐 测试网页开始时间配置优先级")
    print("=" * 60)
    
    # 测试1: 网页设置的开始时间应该完全覆盖GPX文件中的时间
    print("\n📅 测试1: 网页自定义开始时间优先级")
    web_start_time = datetime(2025, 3, 15, 10, 30, 0)  # 网页设置的时间
    print(f"   网页设置时间: {web_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 模拟网页端的配置方式
    config = {
        'start_time': web_start_time,  # 网页端设置的开始时间
        'base_hr': 140,
        'max_hr': 170,
        'activity_type': 'Running'
    }
    
    converter = GPXToTCXConverter(config=config)
    
    # 转换GPX文件（GPX文件中有自己的时间戳）
    success = converter.convert("测试轨迹.gpx", "test_web_priority.tcx")
    
    if success and os.path.exists("test_web_priority.tcx"):
        with open("test_web_priority.tcx", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查TCX文件中的Activity ID和开始时间
        activity_id_match = re.search(r'<Id>([^<]+)</Id>', content)
        start_time_match = re.search(r'<Lap StartTime="([^"]+)">', content)
        first_trackpoint_match = re.search(r'<Time>([^<]+)</Time>', content)
        
        print("\n🔍 TCX文件内容检查:")
        if activity_id_match:
            activity_id = activity_id_match.group(1)
            print(f"   Activity ID: {activity_id}")
            
        if start_time_match:
            lap_start_time = start_time_match.group(1)
            print(f"   Lap开始时间: {lap_start_time}")
            
        if first_trackpoint_match:
            first_trackpoint_time = first_trackpoint_match.group(1)
            print(f"   第一个轨迹点时间: {first_trackpoint_time}")
        
        # 验证时间是否匹配网页设置
        expected_time_str = "2025-03-15T10:30:00"
        
        success_count = 0
        total_checks = 3
        
        if activity_id_match and expected_time_str in activity_id_match.group(1):
            print("   ✅ Activity ID使用了网页设置的开始时间")
            success_count += 1
        else:
            print("   ❌ Activity ID未使用网页设置的开始时间")
            
        if start_time_match and expected_time_str in start_time_match.group(1):
            print("   ✅ Lap开始时间使用了网页设置的开始时间")
            success_count += 1
        else:
            print("   ❌ Lap开始时间未使用网页设置的开始时间")
            
        if first_trackpoint_match and expected_time_str in first_trackpoint_match.group(1):
            print("   ✅ 第一个轨迹点使用了网页设置的开始时间")
            success_count += 1
        else:
            print("   ❌ 第一个轨迹点未使用网页设置的开始时间")
        
        # 清理测试文件
        os.remove("test_web_priority.tcx")
        
        return success_count == total_checks
    else:
        print("❌ 转换失败或文件不存在")
        return False

def test_different_web_times():
    """测试不同的网页设置时间"""
    print("\n📅 测试2: 不同网页设置时间")
    
    test_times = [
        datetime(2025, 1, 1, 6, 0, 0),    # 早晨6点
        datetime(2025, 6, 15, 18, 45, 30), # 傍晚6点45分30秒
        datetime(2025, 12, 31, 23, 59, 59) # 年末最后一秒
    ]
    
    all_passed = True
    
    for i, test_time in enumerate(test_times, 1):
        print(f"\n   测试时间 {i}: {test_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        config = {'start_time': test_time}
        converter = GPXToTCXConverter(config=config)
        
        output_file = f"test_web_time_{i}.tcx"
        success = converter.convert("测试轨迹.gpx", output_file)
        
        if success and os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含设置的时间
            expected_date = test_time.strftime('%Y-%m-%d')
            expected_time_part = test_time.strftime('%H:%M:%S')
            
            if expected_date in content and expected_time_part in content:
                print(f"   ✅ 时间 {i} 配置生效")
            else:
                print(f"   ❌ 时间 {i} 配置未生效")
                all_passed = False
            
            # 清理文件
            os.remove(output_file)
        else:
            print(f"   ❌ 时间 {i} 转换失败")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("🚀 网页开始时间配置测试")
    print("验证开始时间完全按照网页设置，不受GPX文件影响")
    print("=" * 60)
    
    # 检查测试文件
    if not os.path.exists("测试轨迹.gpx"):
        print("❌ 测试文件 '测试轨迹.gpx' 不存在")
        exit(1)
    
    # 执行测试
    test1_result = test_web_start_time_priority()
    test2_result = test_different_web_times()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"   网页时间优先级测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"   多种时间格式测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！")
        print("✅ 开始时间完全按照网页设置生效，不受GPX文件影响")
        exit(0)
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查")
        exit(1)