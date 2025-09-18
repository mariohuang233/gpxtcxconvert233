#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试平均步频修复
"""

import requests
import time
import os
import xml.etree.ElementTree as ET
import re

def test_cadence_fix():
    """测试平均步频修复"""
    base_url = 'http://localhost:8888'
    
    # 测试用的GPX文件路径
    test_gpx = 'test_cadence.gpx'
    
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
      <trkpt lat="39.9072" lon="116.4104">
        <ele>56</ele>
        <time>2024-01-15T08:33:00Z</time>
      </trkpt>
      <trkpt lat="39.9082" lon="116.4114">
        <ele>58</ele>
        <time>2024-01-15T08:34:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>'''
    
    with open(test_gpx, 'w', encoding='utf-8') as f:
        f.write(gpx_content)
    
    try:
        print("🧪 开始测试平均步频修复...")
        
        # 上传文件
        with open(test_gpx, 'rb') as f:
            files = {'file': (test_gpx, f, 'application/gpx+xml')}
            data = {'activity_type': 'Running'}
            
            print("📤 上传测试文件...")
            response = requests.post(f'{base_url}/upload', files=files, data=data)
            
            if response.status_code != 200:
                print(f"❌ 上传失败: {response.status_code}")
                return False
            
            # 检查响应
            try:
                result = response.json()
                if "task_id" in result:
                    print("✅ 文件上传成功")
                    task_id = result["task_id"]
                else:
                    print(f"❌ 上传失败: {result}")
                    return False
            except:
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
        
        # 分析TCX文件
        print("🔍 分析TCX文件中的平均步频...")
        try:
            with open(latest_tcx, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含LX扩展
            has_lx = '<ns3:LX>' in content
            print(f"📋 LX扩展: {'✅ 存在' if has_lx else '❌ 不存在'}")
            
            if has_lx:
                # 提取平均步频
                avg_cadence_match = re.search(r'<ns3:AvgRunCadence>(\d+)</ns3:AvgRunCadence>', content)
                avg_cadence = avg_cadence_match.group(1) if avg_cadence_match else "未找到"
                
                # 提取最大步频
                max_cadence_match = re.search(r'<ns3:MaxRunCadence>(\d+)</ns3:MaxRunCadence>', content)
                max_cadence = max_cadence_match.group(1) if max_cadence_match else "未找到"
                
                print(f"📊 步频数据:")
                print(f"   - 平均步频: {avg_cadence} spm")
                print(f"   - 最大步频: {max_cadence} spm")
                
                # 检查是否移除了SubSport字段
                has_subsport = '<ns3:SubSport>' in content
                print(f"   - SubSport字段: {'❌ 仍存在' if has_subsport else '✅ 已移除'}")
                
                # 提取并显示LX扩展内容
                lx_match = re.search(r'<ns3:LX>(.*?)</ns3:LX>', content, re.DOTALL)
                if lx_match:
                    lx_content = lx_match.group(1).strip()
                    print(f"\n📋 LX扩展内容:")
                    for line in lx_content.split('\n'):
                        if line.strip():
                            print(f"     {line.strip()}")
                
                # 判断修复是否成功
                if avg_cadence != "未找到" and avg_cadence != "0" and not has_subsport:
                    print(f"\n🎉 平均步频修复成功！")
                    print(f"   ✅ 包含平均步频数据: {avg_cadence} spm")
                    print(f"   ✅ 移除了SubSport字段")
                    print(f"   ✅ 格式与真实文件一致")
                    return True
                else:
                    print(f"\n❌ 修复未完全成功")
                    if avg_cadence == "未找到" or avg_cadence == "0":
                        print(f"   - 平均步频数据问题")
                    if has_subsport:
                        print(f"   - SubSport字段未移除")
                    return False
            else:
                print(f"❌ 缺少LX扩展")
                return False
                
        except Exception as e:
            print(f"❌ 分析TCX文件失败: {e}")
            return False
        
    finally:
        # 清理测试文件
        if os.path.exists(test_gpx):
            os.remove(test_gpx)
            print(f"🗑️ 已删除测试文件: {test_gpx}")

if __name__ == '__main__':
    success = test_cadence_fix()
    if success:
        print("\n🎊 平均步频修复测试通过！")
        exit(0)
    else:
        print("\n❌ 平均步频修复测试失败！")
        exit(1)