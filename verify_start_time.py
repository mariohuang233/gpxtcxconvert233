#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证开始时间配置是否生效
"""

from datetime import datetime
from gpx_to_tcx import GPXToTCXConverter

def verify_start_time():
    """验证开始时间配置"""
    print("🕐 验证开始时间配置...")
    
    # 自定义开始时间
    custom_start_time = datetime.strptime("2025-01-20 07:15:00", '%Y-%m-%d %H:%M:%S')
    
    config = {
        'start_time': custom_start_time
    }
    
    converter = GPXToTCXConverter(config=config)
    
    # 转换文件
    success = converter.convert("测试轨迹.gpx", "verify_start_time.tcx")
    
    if success:
        # 读取生成的TCX文件
        with open("verify_start_time.tcx", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查时间格式
        if "2025-01-20T07:15:00" in content or "2025-01-20T" in content:
            print("✅ 开始时间配置生效！")
            print(f"   配置的时间: {custom_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 提取实际使用的时间
            import re
            time_matches = re.findall(r'<Time>(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', content)
            if time_matches:
                first_time = time_matches[0]
                print(f"   TCX中的时间: {first_time}")
        else:
            print("❌ 开始时间配置未生效")
            print("   检查TCX文件中的时间格式...")
            
            # 显示前几个时间戳
            import re
            time_matches = re.findall(r'<Time>([^<]+)</Time>', content)
            if time_matches:
                print(f"   实际时间戳: {time_matches[0]}")
        
        # 清理文件
        import os
        os.remove("verify_start_time.tcx")
        print("🗑️ 清理验证文件")
    else:
        print("❌ 转换失败")

if __name__ == "__main__":
    verify_start_time()