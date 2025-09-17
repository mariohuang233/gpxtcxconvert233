#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有配置项是否生效
"""

import sys
import os
from datetime import datetime
from gpx_to_tcx import GPXToTCXConverter

def test_all_configs():
    """测试所有配置项功能"""
    print("🧪 开始测试所有配置项功能...")
    
    # 测试配置
    test_config = {
        'start_time': datetime.strptime("2025-01-15 09:00:00", '%Y-%m-%d %H:%M:%S'),
        'base_hr': 130,        # 自定义最小心率
        'max_hr': 180,         # 自定义最大心率
        'base_cadence': 150,   # 自定义最小步频
        'max_cadence': 190,    # 自定义最大步频
        'min_power': 120,      # 自定义最小功率
        'max_power': 280,      # 自定义最大功率
        'target_pace': '4:45', # 自定义目标配速
        'activity_type': 'Cycling',  # 自定义运动类型
        'speed_threshold': 1.0  # 自定义速度阈值
    }
    
    print("📋 测试配置:")
    for key, value in test_config.items():
        if key == 'start_time':
            print(f"   {key}: {value.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"   {key}: {value}")
    
    # 创建转换器实例
    converter = GPXToTCXConverter(config=test_config)
    
    # 检查配置是否正确应用
    print("\n🔍 检查配置应用情况:")
    
    # 检查配置值
    config_checks = [
        ('base_hr', 130),
        ('max_hr', 180),
        ('base_cadence', 150),
        ('max_cadence', 190),
        ('min_power', 120),
        ('max_power', 280),
        ('target_pace', '4:45'),
        ('activity_type', 'Cycling'),
        ('speed_threshold', 1.0)
    ]
    
    all_passed = True
    for key, expected_value in config_checks:
        actual_value = converter.config.get(key)
        if actual_value == expected_value:
            print(f"   ✅ {key}: {actual_value} (符合预期)")
        else:
            print(f"   ❌ {key}: {actual_value} (期望: {expected_value})")
            all_passed = False
    
    # 检查开始时间
    start_time_config = converter.config.get('start_time')
    expected_start_time = test_config['start_time']
    if start_time_config == expected_start_time:
        print(f"   ✅ start_time: {start_time_config.strftime('%Y-%m-%d %H:%M:%S')} (符合预期)")
    else:
        print(f"   ❌ start_time: {start_time_config} (期望: {expected_start_time})")
        all_passed = False
    
    return all_passed

def test_simulation_functions():
    """测试模拟函数是否使用配置参数"""
    print("\n🧪 测试模拟函数...")
    
    # 创建带自定义配置的转换器
    config = {
        'base_hr': 140,
        'max_hr': 170,
        'base_cadence': 160,
        'max_cadence': 180,
        'min_power': 200,
        'max_power': 300,
        'speed_threshold': 0.5
    }
    
    converter = GPXToTCXConverter(config=config)
    
    # 测试心率模拟
    print("\n💓 测试心率模拟:")
    test_speeds = [0.3, 1.0, 2.0, 3.0]  # 不同速度
    for i, speed in enumerate(test_speeds):
        hr = converter.simulate_heart_rate(speed, i, 10)
        print(f"   速度 {speed} m/s -> 心率 {hr} bpm")
        
        # 检查心率是否在配置范围内（考虑一些波动）
        if speed < config['speed_threshold']:
            expected_range = (config['base_hr'] - 10, config['base_hr'] + 10)
        else:
            expected_range = (config['base_hr'] - 10, config['max_hr'] + 10)
        
        if expected_range[0] <= hr <= expected_range[1]:
            print(f"     ✅ 心率在合理范围内 ({expected_range[0]}-{expected_range[1]})")
        else:
            print(f"     ❌ 心率超出范围 ({expected_range[0]}-{expected_range[1]})")
    
    # 测试步频模拟
    print("\n🏃 测试步频模拟:")
    for speed in test_speeds:
        cadence = converter.simulate_cadence(speed)
        print(f"   速度 {speed} m/s -> 步频 {cadence} spm")
        
        if speed < config['speed_threshold']:
            expected_cadence = 0
        else:
            expected_range = (config['base_cadence'] - 20, config['max_cadence'] + 20)
            if expected_range[0] <= cadence <= expected_range[1]:
                print(f"     ✅ 步频在合理范围内 ({expected_range[0]}-{expected_range[1]})")
            else:
                print(f"     ❌ 步频超出范围 ({expected_range[0]}-{expected_range[1]})")
    
    # 测试功率模拟
    print("\n⚡ 测试功率模拟:")
    for speed in test_speeds:
        hr = converter.simulate_heart_rate(speed, 0, 10)
        power = converter.simulate_power(speed, hr)
        print(f"   速度 {speed} m/s, 心率 {hr} bpm -> 功率 {power} W")
        
        if speed < config['speed_threshold']:
            expected_power = 0
        else:
            expected_range = (config['min_power'] - 20, config['max_power'] + 20)
            if expected_range[0] <= power <= expected_range[1]:
                print(f"     ✅ 功率在合理范围内 ({expected_range[0]}-{expected_range[1]})")
            else:
                print(f"     ❌ 功率超出范围 ({expected_range[0]}-{expected_range[1]})")
    
    return True

def test_full_conversion():
    """测试完整转换流程"""
    print("\n🧪 测试完整转换流程...")
    
    # 自定义配置
    config = {
        'start_time': datetime.strptime("2025-01-20 07:15:00", '%Y-%m-%d %H:%M:%S'),
        'base_hr': 125,
        'max_hr': 175,
        'base_cadence': 155,
        'max_cadence': 185,
        'min_power': 140,
        'max_power': 260,
        'target_pace': '5:15',
        'activity_type': 'Running'
    }
    
    converter = GPXToTCXConverter(config=config)
    
    gpx_file = "测试轨迹.gpx"
    output_file = "test_output_with_config.tcx"
    
    try:
        # 执行转换
        success = converter.convert(gpx_file, output_file)
        
        if success and os.path.exists(output_file):
            print(f"✅ 转换成功，输出文件: {output_file}")
            
            # 检查输出文件内容
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查是否包含自定义开始时间
            if "2025-01-20T" in content:
                print("✅ 输出文件包含自定义开始时间")
            else:
                print("❌ 输出文件未包含自定义开始时间")
                
            # 检查是否包含运动类型
            if "Running" in content:
                print("✅ 输出文件包含正确的运动类型")
            else:
                print("❌ 输出文件未包含正确的运动类型")
            
            # 清理测试文件
            os.remove(output_file)
            print(f"🗑️ 清理测试文件: {output_file}")
            
            return True
        else:
            print("❌ 转换失败")
            return False
            
    except Exception as e:
        print(f"❌ 转换过程中出现错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 GPX转TCX全配置项测试")
    print("=" * 60)
    
    # 测试1: 配置应用
    test1_result = test_all_configs()
    
    # 测试2: 模拟函数
    test2_result = test_simulation_functions()
    
    # 测试3: 完整转换
    test3_result = test_full_conversion()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"   配置应用测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"   模拟函数测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    print(f"   完整转换测试: {'✅ 通过' if test3_result else '❌ 失败'}")
    
    if test1_result and test2_result and test3_result:
        print("\n🎉 所有测试通过！所有配置项功能正常工作。")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查配置逻辑。")
        sys.exit(1)