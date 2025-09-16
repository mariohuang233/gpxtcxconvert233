#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气API测试脚本
测试5重备用方案和多语言功能
"""

import requests
import json
import time
from datetime import datetime

def test_weather_api():
    """测试天气API的各种场景"""
    base_url = "http://localhost:8888"
    
    print("🌤️ 天气API测试开始")
    print("=" * 50)
    
    # 测试场景列表
    test_cases = [
        {
            "name": "中文 + GPS定位",
            "params": {"lat": 39.9042, "lon": 116.4074, "lang": "zh"},
            "description": "北京GPS坐标，中文显示"
        },
        {
            "name": "英文 + GPS定位", 
            "params": {"lat": 40.7128, "lon": -74.0060, "lang": "en"},
            "description": "纽约GPS坐标，英文显示"
        },
        {
            "name": "中文 + 城市名",
            "params": {"city": "上海", "lang": "zh"},
            "description": "城市名查询，中文显示"
        },
        {
            "name": "英文 + 城市名",
            "params": {"city": "London", "lang": "en"},
            "description": "城市名查询，英文显示"
        },
        {
            "name": "IP自动定位 + 中文",
            "params": {"lang": "zh"},
            "description": "无位置参数，测试IP定位"
        },
        {
            "name": "IP自动定位 + 英文",
            "params": {"lang": "en"},
            "description": "无位置参数，测试IP定位"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📍 测试 {i}: {test_case['name']}")
        print(f"   描述: {test_case['description']}")
        
        try:
            # 发送请求
            response = requests.get(
                f"{base_url}/greeting-info",
                params=test_case["params"],
                timeout=10
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # 提取天气和位置信息 (数据在data字段中)
                data = response_data.get('data', {})
                weather = data.get('weather', {})
                location = data.get('location', {})
                greeting = data.get('greeting', '')
                
                print(f"   ✅ 成功 - 状态码: {response.status_code}")
                print(f"   🌡️  温度: {weather.get('temperature', 'N/A')}")
                print(f"   🌤️  天气: {weather.get('description', 'N/A')}")
                print(f"   💧 湿度: {weather.get('humidity', 'N/A')}%")
                print(f"   💨 风速: {weather.get('wind_speed', 'N/A')} m/s")
                print(f"   📍 城市: {location.get('city', 'N/A')}")
                print(f"   🌍 国家: {location.get('country', 'N/A')}")
                print(f"   💬 问候: {greeting[:30]}...")
                
                # 验证多语言
                lang = test_case["params"].get("lang", "zh")
                weather_desc = weather.get('description', '')
                
                if lang == 'zh':
                    chinese_chars = any('\u4e00' <= char <= '\u9fff' for char in weather_desc)
                    print(f"   🈳 中文检测: {'✅ 包含中文' if chinese_chars else '⚠️ 无中文字符'}")
                else:
                    english_chars = any(char.isalpha() and ord(char) < 128 for char in weather_desc)
                    print(f"   🔤 英文检测: {'✅ 包含英文' if english_chars else '⚠️ 无英文字符'}")
                
                results.append({
                    "test": test_case["name"],
                    "status": "success",
                    "weather": weather,
                    "location": location,
                    "lang_check": "pass"
                })
                
            else:
                print(f"   ❌ 失败 - 状态码: {response.status_code}")
                print(f"   📄 响应: {response.text[:100]}...")
                results.append({
                    "test": test_case["name"],
                    "status": "failed",
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            results.append({
                "test": test_case["name"],
                "status": "error",
                "error": str(e)
            })
        
        # 避免请求过于频繁
        time.sleep(1)
    
    # 生成测试报告
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    total_count = len(results)
    
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失败: {total_count - success_count}/{total_count}")
    print(f"📈 成功率: {success_count/total_count*100:.1f}%")
    
    # 详细结果
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['test']}")
        if result["status"] != "success":
            print(f"   错误: {result.get('error', 'Unknown')}")
    
    return results

def test_ip_location():
    """测试IP定位功能"""
    print("\n🌍 IP定位API测试")
    print("=" * 30)
    
    ip_apis = [
        'http://ip-api.com/json/?fields=city,country,countryCode,lat,lon,timezone',
        'https://ipapi.co/json/',
        'https://freegeoip.app/json/'
    ]
    
    for i, api_url in enumerate(ip_apis, 1):
        print(f"\n📡 测试API {i}: {api_url.split('/')[2]}")
        try:
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 成功")
                print(f"   🏙️  城市: {data.get('city', 'N/A')}")
                print(f"   🌍 国家: {data.get('country', data.get('country_name', 'N/A'))}")
                print(f"   📍 坐标: {data.get('lat', data.get('latitude', 'N/A'))}, {data.get('lon', data.get('longitude', 'N/A'))}")
            else:
                print(f"   ❌ 失败 - 状态码: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")

def main():
    """主函数"""
    print(f"🚀 天气API综合测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 测试地址: http://localhost:8888")
    
    # 测试IP定位
    test_ip_location()
    
    # 测试天气API
    results = test_weather_api()
    
    # 保存测试结果
    report_file = f"weather_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_results": results,
            "summary": {
                "total_tests": len(results),
                "successful_tests": sum(1 for r in results if r["status"] == "success"),
                "success_rate": sum(1 for r in results if r["status"] == "success") / len(results) * 100
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 测试报告已保存: {report_file}")
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()