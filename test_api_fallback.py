#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气API备用方案测试脚本
测试5重备用机制的切换
"""

import requests
import json
import time
from datetime import datetime

def test_api_fallback():
    """测试API备用方案切换机制"""
    print("🔄 天气API备用方案测试")
    print("=" * 40)
    
    # 测试不同场景下的API切换
    test_scenarios = [
        {
            "name": "正常城市查询",
            "params": {"city": "Beijing", "lang": "zh"},
            "expected": "应该使用wttr.in API"
        },
        {
            "name": "英文城市查询", 
            "params": {"city": "Tokyo", "lang": "en"},
            "expected": "应该使用wttr.in API"
        },
        {
            "name": "GPS坐标查询",
            "params": {"lat": 31.2304, "lon": 121.4737, "lang": "zh"},
            "expected": "应该使用wttr.in API"
        },
        {
            "name": "无效城市名",
            "params": {"city": "InvalidCityName123", "lang": "zh"},
            "expected": "可能触发备用方案"
        },
        {
            "name": "IP自动定位",
            "params": {"lang": "zh"},
            "expected": "使用IP定位 + wttr.in"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 测试场景 {i}: {scenario['name']}")
        print(f"   期望: {scenario['expected']}")
        
        try:
            start_time = time.time()
            response = requests.get(
                "http://localhost:8888/greeting-info",
                params=scenario["params"],
                timeout=15
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                weather = data.get('weather', {})
                location = data.get('location', {})
                
                print(f"   ✅ 成功 - 响应时间: {end_time - start_time:.2f}s")
                print(f"   🌡️  温度: {weather.get('temperature', 'N/A')}")
                print(f"   🌤️  天气: {weather.get('description', 'N/A')}")
                print(f"   📍 位置: {location.get('city', 'N/A')}, {location.get('country', 'N/A')}")
                
                # 检查数据完整性
                has_temp = weather.get('temperature') is not None
                has_desc = weather.get('description') is not None
                has_location = location.get('city') is not None
                
                data_quality = "完整" if (has_temp and has_desc and has_location) else "部分"
                print(f"   📊 数据质量: {data_quality}")
                
                results.append({
                    "scenario": scenario["name"],
                    "status": "success",
                    "response_time": round(end_time - start_time, 2),
                    "data_quality": data_quality,
                    "weather": weather,
                    "location": location
                })
                
            else:
                print(f"   ❌ 失败 - 状态码: {response.status_code}")
                results.append({
                    "scenario": scenario["name"],
                    "status": "failed",
                    "error": f"HTTP {response.status_code}"
                })
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ 超时 - 可能API响应较慢")
            results.append({
                "scenario": scenario["name"],
                "status": "timeout",
                "error": "Request timeout"
            })
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            results.append({
                "scenario": scenario["name"],
                "status": "error",
                "error": str(e)
            })
        
        # 避免请求过于频繁
        time.sleep(2)
    
    return results

def test_multilang_weather():
    """专门测试多语言天气描述"""
    print("\n🌍 多语言天气描述测试")
    print("=" * 30)
    
    # 同一个城市的不同语言测试
    city = "Shanghai"
    languages = ["zh", "en"]
    
    for lang in languages:
        print(f"\n🗣️  测试语言: {lang.upper()}")
        try:
            response = requests.get(
                "http://localhost:8888/greeting-info",
                params={"city": city, "lang": lang},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                weather_desc = data.get('weather', {}).get('description', '')
                greeting = data.get('greeting', '')
                
                print(f"   🌤️  天气描述: {weather_desc}")
                print(f"   💬 问候语: {greeting[:50]}...")
                
                # 语言检测
                if lang == 'zh':
                    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in weather_desc)
                    print(f"   🈳 中文检测: {'✅ 正确' if has_chinese else '❌ 错误'}")
                else:
                    has_english = any(char.isalpha() and ord(char) < 128 for char in weather_desc)
                    print(f"   🔤 英文检测: {'✅ 正确' if has_english else '❌ 错误'}")
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
        
        time.sleep(1)

def main():
    """主函数"""
    print(f"🚀 天气API备用方案综合测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 测试目标: 验证5重备用方案和多语言功能")
    
    # 测试备用方案
    fallback_results = test_api_fallback()
    
    # 测试多语言
    test_multilang_weather()
    
    # 生成汇总报告
    print("\n" + "=" * 50)
    print("📋 测试汇总报告")
    print("=" * 50)
    
    success_count = sum(1 for r in fallback_results if r["status"] == "success")
    total_count = len(fallback_results)
    
    print(f"✅ 成功测试: {success_count}/{total_count}")
    print(f"📈 成功率: {success_count/total_count*100:.1f}%")
    
    # 按状态分组显示
    for result in fallback_results:
        status_icon = {
            "success": "✅",
            "failed": "❌", 
            "timeout": "⏰",
            "error": "🚫"
        }.get(result["status"], "❓")
        
        print(f"{status_icon} {result['scenario']}")
        if result["status"] == "success":
            print(f"   响应时间: {result['response_time']}s, 数据质量: {result['data_quality']}")
        elif "error" in result:
            print(f"   错误: {result['error']}")
    
    # 保存详细报告
    report_file = f"api_fallback_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_type": "API Fallback Test",
            "results": fallback_results,
            "summary": {
                "total_tests": total_count,
                "successful_tests": success_count,
                "success_rate": success_count / total_count * 100,
                "avg_response_time": sum(r.get("response_time", 0) for r in fallback_results if r["status"] == "success") / max(success_count, 1)
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细报告已保存: {report_file}")
    print("\n🎉 备用方案测试完成！")
    
    # 给出建议
    if success_count == total_count:
        print("\n🌟 所有测试通过！天气API备用方案工作正常。")
    elif success_count >= total_count * 0.8:
        print("\n👍 大部分测试通过，系统基本稳定。")
    else:
        print("\n⚠️  部分测试失败，建议检查API配置。")

if __name__ == "__main__":
    main()