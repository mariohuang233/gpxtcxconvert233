#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试时区修复功能
验证设置的时间是否正确显示，不会有8小时时差
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
import glob

def test_timezone_fix():
    """测试时区修复功能 - 检查最新的TCX文件"""
    
    print("🧪 开始测试时区修复功能...")
    
    # 查找最新的TCX文件
    tcx_files = glob.glob('outputs/*.tcx')
    if not tcx_files:
        print("❌ 未找到TCX文件")
        return False
    
    # 获取最新的文件
    latest_tcx = max(tcx_files, key=os.path.getctime)
    print(f"📁 检查最新的TCX文件: {latest_tcx}")
    
    try:
        # 解析TCX文件检查时间
        print("🔍 检查TCX文件中的开始时间...")
        tree = ET.parse(latest_tcx)
        root = tree.getroot()
        
        # 查找第一个时间点
        ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
        first_trackpoint = root.find('.//tcx:Trackpoint', ns)
        
        if first_trackpoint is not None:
            time_elem = first_trackpoint.find('tcx:Time', ns)
            if time_elem is not None:
                tcx_time_str = time_elem.text
                print(f"📅 TCX文件中的开始时间: {tcx_time_str}")
                
                # 解析时间并检查
                if 'Z' in tcx_time_str:
                    tcx_time = datetime.fromisoformat(tcx_time_str.replace('Z', '+00:00'))
                else:
                    tcx_time = datetime.fromisoformat(tcx_time_str)
                
                print(f"🕐 解析后的时间: {tcx_time.hour:02d}:{tcx_time.minute:02d}:{tcx_time.second:02d}")
                
                # 检查是否是我们期望的时间 (6:43)
                expected_hour = 6
                expected_minute = 43
                
                if tcx_time.hour == expected_hour and tcx_time.minute == expected_minute:
                    print(f"✅ 时间正确！显示为 {tcx_time.hour:02d}:{tcx_time.minute:02d}")
                    print("🎉 时区修复成功！用户设置的6:43正确显示，没有8小时时差")
                    return True
                elif tcx_time.hour == 14 and tcx_time.minute == 43:
                    print(f"❌ 时间错误！期望 {expected_hour:02d}:{expected_minute:02d}，实际 {tcx_time.hour:02d}:{tcx_time.minute:02d}")
                    print("⚠️ 仍然存在8小时时差问题 (6:43 -> 14:43)")
                    return False
                else:
                    print(f"❌ 时间不匹配！期望 {expected_hour:02d}:{expected_minute:02d}，实际 {tcx_time.hour:02d}:{tcx_time.minute:02d}")
                    return False
            else:
                print("❌ 未找到时间元素")
                return False
        else:
            print("❌ 未找到轨迹点")
            return False
            
    except Exception as e:
        print(f"❌ 解析TCX文件失败: {e}")
        return False

if __name__ == '__main__':
    success = test_timezone_fix()
    if success:
        print("\n🎉 时区修复测试通过！")
        exit(0)
    else:
        print("\n❌ 时区修复测试失败！")
        exit(1)