#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的转换功能测试脚本
用于调试转换过程中的问题
"""

import os
import sys
from datetime import datetime
from gpx_to_tcx import GPXToTCXConverter

def test_conversion():
    """测试转换功能"""
    print("🔍 开始测试GPX转TCX转换功能...")
    
    # 查找测试GPX文件
    test_files = [
        "测试轨迹.gpx",
        "example_route.gpx",
    ]
    
    test_file = None
    for filename in test_files:
        if os.path.exists(filename):
            test_file = filename
            break
    
    if not test_file:
        print("❌ 未找到测试GPX文件")
        return False
    
    print(f"📁 使用测试文件: {test_file}")
    
    try:
        # 创建转换器
        print("⚙️ 初始化转换器...")
        converter = GPXToTCXConverter()
        
        # 设置输出文件
        output_file = f"test_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tcx"
        
        print(f"🔄 开始转换: {test_file} -> {output_file}")
        
        # 执行转换
        success = converter.convert(test_file, output_file)
        
        if success and os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ 转换成功! 输出文件: {output_file} ({file_size} bytes)")
            
            # 显示输出文件的前几行
            print("\n📄 输出文件预览:")
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
                for i, line in enumerate(lines, 1):
                    print(f"  {i}: {line.strip()}")
            
            return True
        else:
            print("❌ 转换失败")
            return False
            
    except Exception as e:
        print(f"💥 转换过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_web_endpoints():
    """测试Web端点"""
    print("\n🌐 测试Web端点...")
    
    import requests
    base_url = "http://localhost:8888"
    
    try:
        # 测试主页
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ 主页正常")
        else:
            print(f"❌ 主页错误: {response.status_code}")
            
        return True
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到Web服务器")
        return False
    except Exception as e:
        print(f"❌ Web测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 GPX转TCX功能测试")
    print("=" * 50)
    
    # 测试转换功能
    conversion_ok = test_conversion()
    
    # 测试Web端点
    web_ok = test_web_endpoints()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"  转换功能: {'✅ 正常' if conversion_ok else '❌ 异常'}")
    print(f"  Web服务: {'✅ 正常' if web_ok else '❌ 异常'}")
    
    if conversion_ok and web_ok:
        print("🎉 所有测试通过!")
        sys.exit(0)
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
        sys.exit(1)

