#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试平均步频显示
"""

import requests
import time
import os
import shutil

def test_final_cadence():
    """最终测试平均步频显示"""
    base_url = 'http://localhost:8888'
    
    # 使用测试轨迹GPX文件重新生成TCX
    original_gpx = '/Users/huangjiawei/Downloads/0908/GPX转TCX应用/测试轨迹.gpx'
    
    if not os.path.exists(original_gpx):
        print(f"❌ 找不到GPX文件: {original_gpx}")
        return False
    
    try:
        print("🔄 重新生成0918.tcx文件...")
        
        # 上传原始GPX文件
        with open(original_gpx, 'rb') as f:
            files = {'file': ('0918.gpx', f, 'application/gpx+xml')}
            data = {'activity_type': 'Running'}
            
            print("📤 上传原始GPX文件...")
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
        time.sleep(5)
        
        # 查找新生成的TCX文件
        import glob
        tcx_files = glob.glob('outputs/*0918*.tcx')
        if not tcx_files:
            print("❌ 未找到新生成的0918.tcx文件")
            return False
        
        # 获取最新的文件
        latest_tcx = max(tcx_files, key=os.path.getctime)
        print(f"📁 找到新生成的TCX文件: {latest_tcx}")
        
        # 复制到根目录替换原文件
        target_path = '/Users/huangjiawei/Downloads/0908/0918.tcx'
        shutil.copy2(latest_tcx, target_path)
        print(f"📋 已更新文件: {target_path}")
        
        # 验证文件内容
        print("🔍 验证更新后的文件...")
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键字段
        has_lx = '<ns3:LX>' in content
        has_avg_cadence = '<ns3:AvgRunCadence>' in content
        has_subsport = '<ns3:SubSport>' in content
        
        print(f"📊 文件验证结果:")
        print(f"   - LX扩展: {'✅ 存在' if has_lx else '❌ 不存在'}")
        print(f"   - 平均步频: {'✅ 存在' if has_avg_cadence else '❌ 不存在'}")
        print(f"   - SubSport字段: {'❌ 仍存在' if has_subsport else '✅ 已移除'}")
        
        if has_lx and has_avg_cadence and not has_subsport:
            print(f"\n🎉 文件更新成功！")
            print(f"   ✅ 新的0918.tcx文件已生成")
            print(f"   ✅ 包含正确的平均步频格式")
            print(f"   ✅ 移除了可能导致兼容性问题的字段")
            print(f"\n💡 请重新在TCX查看器中打开文件查看平均步频")
            return True
        else:
            print(f"\n❌ 文件更新有问题")
            return False
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return False

if __name__ == '__main__':
    success = test_final_cadence()
    if success:
        print("\n🎊 0918.tcx文件已成功更新！")
        print("\n📋 建议操作:")
        print("   1. 重新在TCX查看器中打开0918.tcx文件")
        print("   2. 检查'总览数据'中是否显示'平均步频'")
        print("   3. 如果仍有问题，可能是查看器兼容性问题")
        exit(0)
    else:
        print("\n❌ 文件更新失败！")
        exit(1)