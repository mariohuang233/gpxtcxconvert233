#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试时区调整功能
验证输入时间减去8小时后的转换结果
"""

import requests
import time
import os
from datetime import datetime
import xml.etree.ElementTree as ET

def test_timezone_adjustment():
    """测试时区调整功能"""
    base_url = 'http://localhost:8888'
    
    # 测试用的GPX文件路径
    test_gpx = 'test_adjustment.gpx'
    
    # 创建测试GPX文件
    gpx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="39.9042" lon="116.4074">
        <ele>50</ele>
        <time>2024-01-15T08:30:00Z</time>
      </trkpt>
      <trkpt lat="39.9052" lon="116.4084">
        <ele>52</ele>
        <time>2024-01-15T08:31:00Z</time>
      </trkpt>
      <trkpt lat="39.9062" lon="116.4094">
        <ele>54</ele>
        <time>2024-01-15T08:32:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>'''
    
    with open(test_gpx, 'w', encoding='utf-8') as f:
        f.write(gpx_content)
    
    try:
        print("🧪 开始测试时区调整功能...")
        
        # 设置测试时间：14:43 (期望转换后显示为 6:43)
        test_time = "2025-03-15T14:43"
        print(f"📅 设置测试时间: {test_time} (减去8小时后应该显示为 06:43)")
        
        # 上传文件并设置自定义开始时间
        with open(test_gpx, 'rb') as f:
            files = {'file': (test_gpx, f, 'application/gpx+xml')}
            data = {
                'start_time': test_time,
                'activity_type': 'Running'
            }
            
            print("📤 上传文件并设置自定义开始时间...")
            response = requests.post(f'{base_url}/upload', files=files, data=data)
            
            if response.status_code != 200:
                print(f"❌ 上传失败: {response.status_code}")
                return False
            
            # 检查响应是否成功
            try:
                # 尝试解析JSON响应
                result = response.json()
                if "task_id" in result:
                    print("✅ 文件上传成功")
                    task_id = result["task_id"]
                else:
                    print(f"❌ 上传失败: {result}")
                    return False
            except:
                # 如果不是JSON，检查HTML响应
                if "文件上传成功" in response.text:
                    print("✅ 文件上传成功")
                else:
                    print(f"❌ 上传可能失败: {response.text[:200]}...")
                    return False
        
        # 等待转换完成
        print("⏳ 等待转换完成...")
        time.sleep(3)
        
        # 检查最新的TCX文件
        import glob
        tcx_files = glob.glob('outputs/*.tcx')
        if not tcx_files:
            print("❌ 未找到TCX文件")
            return False
        
        # 获取最新的文件
        latest_tcx = max(tcx_files, key=os.path.getctime)
        print(f"📁 检查最新的TCX文件: {latest_tcx}")
        
        # 解析TCX文件检查时间
        print("🔍 检查TCX文件中的开始时间...")
        try:
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
                    
                    # 检查是否是我们期望的时间 (6:43，即14:43-8小时)
                    expected_hour = 6
                    expected_minute = 43
                    
                    if tcx_time.hour == expected_hour and tcx_time.minute == expected_minute:
                        print(f"✅ 时间调整正确！输入14:43，调整后显示为 {tcx_time.hour:02d}:{tcx_time.minute:02d}")
                        print("🎉 时区调整功能工作正常！")
                        return True
                    else:
                        print(f"❌ 时间调整错误！期望 {expected_hour:02d}:{expected_minute:02d}，实际 {tcx_time.hour:02d}:{tcx_time.minute:02d}")
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
        
    finally:
        # 清理测试文件
        if os.path.exists(test_gpx):
            os.remove(test_gpx)
            print(f"🗑️ 已删除测试文件: {test_gpx}")

if __name__ == '__main__':
    success = test_timezone_adjustment()
    if success:
        print("\n🎉 时区调整测试通过！")
        exit(0)
    else:
        print("\n❌ 时区调整测试失败！")
        exit(1)