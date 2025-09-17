#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户反馈的时间配置问题
"""

from datetime import datetime
from gpx_to_tcx import GPXToTCXConverter
import os
import re

def test_user_time_issue():
    """测试用户反馈的时间配置问题"""
    print("🔍 测试用户反馈的时间配置问题")
    print("=" * 50)
    
    # 测试多个不同的自定义时间
    test_times = [
        datetime(2025, 1, 10, 15, 30, 0),
        "2025-06-15 10:45:20",
        datetime(2025, 9, 8, 7, 20, 15),
        "2025-12-31 23:59:59"
    ]
    
    all_passed = True
    
    for i, test_time in enumerate(test_times, 1):
        print(f"\n📅 测试 {i}: {test_time}")
        
        config = {'start_time': test_time}
        converter = GPXToTCXConverter(config=config)
        output_file = f"test_user_time_{i}.tcx"
        
        success = converter.convert("测试轨迹.gpx", output_file)
        
        if success and os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取时间戳
            time_matches = re.findall(r'<Time>(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', content)
            if time_matches:
                actual_time_str = time_matches[0]
                print(f"   TCX中的时间: {actual_time_str}")
                
                # 检查是否不是2024-12-25
                if "2024-12-25" in actual_time_str:
                    print("   ❌ 仍然使用默认时间2024-12-25！")
                    all_passed = False
                else:
                    print("   ✅ 时间配置生效，不是默认的2024-12-25")
            else:
                print("   ❌ 无法提取时间戳")
                all_passed = False
            
            os.remove(output_file)
        else:
            print("   ❌ 转换失败")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！时间配置问题已解决，不再使用2024-12-25！")
    else:
        print("❌ 测试失败！时间配置问题仍然存在！")
    
    return all_passed

if __name__ == "__main__":
    success = test_user_time_issue()
    exit(0 if success else 1)