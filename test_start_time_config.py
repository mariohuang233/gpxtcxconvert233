#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试开始时间配置是否生效
"""

import sys
import os
from datetime import datetime
from gpx_to_tcx import GPXToTCXConverter

def test_start_time_config():
    """测试开始时间配置功能"""
    print("🧪 开始测试开始时间配置功能...")
    
    # 测试用的自定义开始时间
    custom_start_time = "2025-01-15 08:30:00"
    print(f"📅 设置自定义开始时间: {custom_start_time}")
    
    # 创建转换器实例，配置自定义开始时间
    config = {
        'start_time': datetime.strptime(custom_start_time, '%Y-%m-%d %H:%M:%S'),
        'base_hr': 140,
        'max_hr': 170,
        'base_cadence': 160,
        'max_cadence': 180,
        'min_power': 180,
        'max_power': 250,
        'target_pace': '5:00'
    }
    
    converter = GPXToTCXConverter(config=config)
    
    # 检查测试文件是否存在
    gpx_file = "测试轨迹.gpx"
    if not os.path.exists(gpx_file):
        print(f"❌ 测试文件 {gpx_file} 不存在")
        return False
    
    print(f"📁 使用测试文件: {gpx_file}")
    
    try:
        # 解析GPX文件
        print("\n🔍 解析GPX文件...")
        points = converter.parse_gpx_file(gpx_file)
        
        if not points:
            print("❌ 没有找到有效的轨迹点")
            return False
        
        print(f"✅ 找到 {len(points)} 个轨迹点")
        
        # 检查第一个点的时间是否使用了自定义开始时间
        first_point_time = points[0]['time']
        expected_time = datetime.strptime(custom_start_time, '%Y-%m-%d %H:%M:%S')
        
        print(f"\n⏰ 时间检查:")
        print(f"   期望开始时间: {expected_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   实际开始时间: {first_point_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查时间是否匹配（允许几秒的误差）
        time_diff = abs((first_point_time - expected_time).total_seconds())
        if time_diff <= 5:  # 允许5秒误差
            print("✅ 开始时间配置生效！")
            
            # 检查后续几个点的时间间隔
            if len(points) > 1:
                second_point_time = points[1]['time']
                time_interval = (second_point_time - first_point_time).total_seconds()
                print(f"   时间间隔: {time_interval} 秒")
            
            return True
        else:
            print(f"❌ 开始时间配置未生效，时间差: {time_diff} 秒")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_without_custom_time():
    """测试不设置自定义时间的情况"""
    print("\n🧪 测试不设置自定义时间的情况...")
    
    # 创建转换器实例，不设置自定义开始时间
    converter = GPXToTCXConverter()
    
    gpx_file = "测试轨迹.gpx"
    
    try:
        # 解析GPX文件
        points = converter.parse_gpx_file(gpx_file)
        
        if points:
            first_point_time = points[0]['time']
            print(f"📅 使用GPX文件时间: {first_point_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        else:
            print("❌ 没有找到有效的轨迹点")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 GPX转TCX开始时间配置测试")
    print("=" * 50)
    
    # 测试1: 自定义开始时间
    test1_result = test_start_time_config()
    
    # 测试2: 不设置自定义时间
    test2_result = test_without_custom_time()
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"   自定义开始时间测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"   默认时间处理测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！开始时间配置功能正常工作。")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查配置逻辑。")
        sys.exit(1)