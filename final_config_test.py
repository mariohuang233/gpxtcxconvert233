#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终配置项测试 - 验证所有配置项都正常工作
"""

from datetime import datetime
from gpx_to_tcx import GPXToTCXConverter
import os

def test_final_config():
    """最终配置测试"""
    print("🎯 最终配置项测试")
    print("=" * 50)
    
    # 完整的自定义配置
    config = {
        'start_time': datetime.strptime("2025-01-20 08:30:00", '%Y-%m-%d %H:%M:%S'),
        'base_hr': 120,
        'max_hr': 180,
        'base_cadence': 160,
        'max_cadence': 190,
        'min_power': 200,
        'max_power': 350,
        'target_pace': '4:30',  # 4分30秒/公里
        'activity_type': 'Running',
        'device_name': '我的GPS手表',
        'calories_per_km': 70,
        'speed_threshold': 1.2
    }
    
    print("📋 测试配置:")
    for key, value in config.items():
        if key == 'start_time':
            print(f"   {key}: {value.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"   {key}: {value}")
    
    # 创建转换器
    converter = GPXToTCXConverter(config=config)
    
    print("\n🔍 验证配置应用:")
    
    # 验证配置合并
    expected_configs = [
        ('start_time', config['start_time']),
        ('base_hr', 120),
        ('max_hr', 180),
        ('base_cadence', 160),
        ('max_cadence', 190),
        ('min_power', 200),
        ('max_power', 350),
        ('target_pace', '4:30'),
        ('activity_type', 'Running'),
        ('device_name', '我的GPS手表'),
        ('calories_per_km', 70),
        ('speed_threshold', 1.2)
    ]
    
    all_passed = True
    for key, expected in expected_configs:
        actual = converter.config.get(key)
        if actual == expected:
            if key == 'start_time':
                print(f"   ✅ {key}: {actual.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"   ✅ {key}: {actual}")
        else:
            print(f"   ❌ {key}: {actual} (期望: {expected})")
            all_passed = False
    
    # 验证默认配置也存在
    print("\n🔍 验证默认配置保留:")
    default_configs = [
        ('hr_factor', 1.5),
        ('cadence_factor', 2.0),
        ('power_factor', 1.0)
    ]
    
    for key, expected in default_configs:
        actual = converter.config.get(key)
        if actual == expected:
            print(f"   ✅ {key}: {actual} (默认值保留)")
        else:
            print(f"   ❌ {key}: {actual} (期望默认值: {expected})")
            all_passed = False
    
    # 执行转换测试
    print("\n🧪 执行转换测试:")
    success = converter.convert("测试轨迹.gpx", "final_test_output.tcx")
    
    if success and os.path.exists("final_test_output.tcx"):
        print("✅ 转换成功")
        
        # 检查输出文件
        with open("final_test_output.tcx", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证关键内容
        checks = [
            ("2025-01-20T00:30:00.000Z" in content, "开始时间（UTC转换）"),
            ("Running" in content, "运动类型"),
            ("我的GPS手表" in content, "设备名称"),
            ("<Value>" in content and "</Value>" in content, "心率数据"),
            ("<ns3:RunCadence>" in content, "步频数据"),
            ("<ns3:Watts>" in content, "功率数据")
        ]
        
        for check, description in checks:
            if check:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description}")
                all_passed = False
        
        # 清理文件
        os.remove("final_test_output.tcx")
        print("   🗑️ 清理测试文件")
    else:
        print("❌ 转换失败")
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有配置项测试通过！配置功能完全正常！")
        return True
    else:
        print("⚠️ 部分配置项测试失败")
        return False

if __name__ == "__main__":
    success = test_final_config()
    exit(0 if success else 1)