#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试时间修复效果
"""

from gpx_to_tcx import GPXToTCXConverter
from datetime import datetime
import tempfile
import os

def test_time_conversion():
    """测试时间转换是否正确"""
    
    # 创建测试GPX内容
    test_gpx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="31.2304" lon="121.4737">
        <ele>10</ele>
        <time>2024-12-25T06:00:00Z</time>
      </trkpt>
      <trkpt lat="31.2305" lon="121.4738">
        <ele>11</ele>
        <time>2024-12-25T06:01:00Z</time>
      </trkpt>
      <trkpt lat="31.2306" lon="121.4739">
        <ele>12</ele>
        <time>2024-12-25T06:02:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>'''
    
    # 创建临时GPX文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as f:
        f.write(test_gpx_content)
        gpx_file = f.name
    
    try:
        # 测试不同的开始时间
        test_times = [
            datetime(2024, 12, 25, 17, 10),  # 17:10
            datetime(2024, 12, 25, 9, 30),   # 09:30
            datetime(2024, 12, 25, 23, 45),  # 23:45
        ]
        
        for test_time in test_times:
            print(f"\n=== 测试时间: {test_time.strftime('%H:%M')} ===")
            
            # 创建转换器
            converter = GPXToTCXConverter()
            converter.config['start_time'] = test_time
            
            # 创建临时输出文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tcx', delete=False) as f:
                tcx_file = f.name
            
            try:
                # 执行转换
                converter.convert(gpx_file, tcx_file)
                
                # 读取生成的TCX文件
                with open(tcx_file, 'r', encoding='utf-8') as f:
                    tcx_content = f.read()
                
                # 查找时间相关的行
                lines = tcx_content.split('\n')
                for line in lines:
                    if '<Time>' in line or 'Id=' in line:
                        print(f"  {line.strip()}")
                        
            finally:
                if os.path.exists(tcx_file):
                    os.unlink(tcx_file)
                    
    finally:
        if os.path.exists(gpx_file):
            os.unlink(gpx_file)

if __name__ == '__main__':
    test_time_conversion()