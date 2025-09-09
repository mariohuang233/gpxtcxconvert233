#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPX转TCX工具
============

这个工具可以直接从GPX文件生成完整的TCX文件，无需原始TCX文件。
适用于只有GPS轨迹，需要生成包含运动数据的TCX文件的场景。

主要功能：
1. 解析GPX文件的GPS轨迹
2. 根据轨迹计算速度、距离等数据
3. 模拟生成心率、步频、功率等运动指标
4. 生成完整的TCX文件，可直接上传到运动平台

使用方法：
    python3 gpx_to_tcx.py 路径.gpx -o 生成的运动.tcx

详细参数说明请运行：
    python3 gpx_to_tcx.py --help

作者: AI Assistant
版本: 1.0
"""

import re
import math
import argparse
import sys
from datetime import datetime, timedelta
from xml.sax.saxutils import escape


class GPXToTCXConverter:
    """
    GPX到TCX转换器
    
    这个类负责解析GPX文件并生成完整的TCX文件。
    """
    
    def __init__(self, config=None):
        """
        初始化转换器
        
        Args:
            config (dict): 配置参数字典
        """
        # 默认配置参数
        self.config = config or {
            'base_hr': 135,              # 基础心率 (bpm) - 真实运动心率
            'max_hr': 165,               # 最大心率 (bpm) - 真实运动心率
            'hr_factor': 1.5,            # 心率调整系数
            'base_cadence': 50,          # 基础步频 (spm) - 真实跑步步频
            'max_cadence': 70,           # 最大步频 (spm) - 真实跑步步频
            'cadence_factor': 2.0,       # 步频调整系数
            'power_factor': 1.0,         # 功率计算系数
            'min_power': 150,            # 最小功率 (W) - 真实跑步功率
            'max_power': 300,            # 最大功率 (W) - 真实跑步功率
            'speed_threshold': 0.8,      # 运动速度阈值 (m/s)
            'start_time': None,          # 自定义开始时间
            'activity_type': 'Running',  # 运动类型
            'device_name': 'GPX Converter', # 设备名称
            'calories_per_km': 60,       # 每公里消耗卡路里
            'target_pace': '5:30'        # 目标配速 (min/km)
        }
    
    def parse_target_pace(self, pace_str):
        """
        解析配速字符串并转换为目标速度 (m/s)
        
        Args:
            pace_str (str): 配速字符串，格式如 "5:30" (分:秒/公里)
            
        Returns:
            float: 目标速度 (m/s)
        """
        try:
            if ':' in pace_str:
                minutes, seconds = pace_str.split(':')
                total_seconds = int(minutes) * 60 + int(seconds)
                # 转换为m/s: 1000米 / 总秒数
                target_speed = 1000.0 / total_seconds
                return target_speed
            else:
                # 如果没有冒号，假设是分钟数
                minutes = float(pace_str)
                total_seconds = minutes * 60
                target_speed = 1000.0 / total_seconds
                return target_speed
        except (ValueError, ZeroDivisionError):
            # 解析失败，返回默认速度 (对应5:30配速)
            return 1000.0 / (5 * 60 + 30)  # 约1.52 m/s
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        使用Haversine公式计算两个GPS坐标点之间的距离
        
        Args:
            lat1, lon1: 第一个点的纬度和经度
            lat2, lon2: 第二个点的纬度和经度
            
        Returns:
            float: 两点间距离（米）
        """
        # 地球半径（米）
        R = 6371000
        
        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 计算差值
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine公式
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def parse_gpx_file(self, gpx_file_path):
        """
        解析GPX文件，提取轨迹点数据
        
        Args:
            gpx_file_path (str): GPX文件路径
            
        Returns:
            list: 包含轨迹点信息的列表
        """
        try:
            with open(gpx_file_path, 'r', encoding='utf-8') as f:
                gpx_content = f.read()
        except Exception as e:
            print(f"❌ 读取GPX文件失败: {e}")
            return []
        
        # 使用正则表达式提取轨迹点 - 修复以支持GPX格式
        # 先提取所有trkpt块（包括自闭合和开闭标签格式）
        trkpt_blocks = re.findall(r'<trkpt[^>]*lat="([^"]+)"[^>]*lon="([^"]+)"[^>]*>(?:.*?</trkpt>|[^>]*/>)', gpx_content, re.DOTALL)
        
        matches = []
        for block in trkpt_blocks:
            lat, lon = block if isinstance(block, tuple) else (block, '')
            # 在每个trkpt块中查找ele和time
            full_block = re.search(r'<trkpt[^>]*lat="' + re.escape(lat) + r'"[^>]*lon="' + re.escape(lon) + r'"[^>]*>.*?(?:</trkpt>|/>)', gpx_content, re.DOTALL)
            if full_block:
                block_content = full_block.group(0)
                ele_match = re.search(r'<ele>([^<]+)</ele>', block_content)
                time_match = re.search(r'<time>([^<]+)</time>', block_content)
                ele = ele_match.group(1) if ele_match else ''
                time_str = time_match.group(1) if time_match else ''
                matches.append((lat, lon, ele, time_str))
        
        gpx_points = []
        for i, match in enumerate(matches):
            lat, lon, ele, time_str = match
            
            # 处理时间
            if time_str:
                try:
                    # 解析GPX时间格式
                    point_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                except:
                    # 如果解析失败，使用合理的历史时间
                    if self.config.get('start_time'):
                        start_time_config = self.config['start_time']
                        if isinstance(start_time_config, datetime):
                            base_time = start_time_config
                        else:
                            # 如果是字符串，尝试解析
                            try:
                                base_time = datetime.fromisoformat(str(start_time_config).replace('Z', '+00:00'))
                            except:
                                base_time = datetime(2024, 12, 25, 6, 0, 0)
                    else:
                        # 使用一个合理的历史时间（比如2024年12月25日早上6点）
                        base_time = datetime(2024, 12, 25, 6, 0, 0)
                    point_time = base_time + timedelta(seconds=i)
            else:
                # 如果没有时间信息，使用合理的历史时间
                if self.config.get('start_time'):
                    start_time_config = self.config['start_time']
                    if isinstance(start_time_config, datetime):
                        base_time = start_time_config
                    else:
                        # 如果是字符串，尝试解析
                        try:
                            base_time = datetime.fromisoformat(str(start_time_config).replace('Z', '+00:00'))
                        except:
                            base_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
                else:
                    # 使用一个合理的历史时间（比如今天早上6点）
                    base_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
                point_time = base_time + timedelta(seconds=i)
            
            gpx_points.append({
                'lat': float(lat),
                'lon': float(lon),
                'ele': float(ele) if ele else 0.0,
                'time': point_time
            })
        
        print(f"✅ 找到 {len(gpx_points)} 个GPX轨迹点")
        return gpx_points
    
    def calculate_metrics(self, points):
        """
        计算轨迹的各种指标，使用与TCX输出一致的速度压缩逻辑
        
        Args:
            points (list): 轨迹点列表
            
        Returns:
            dict: 包含各种指标的字典
        """
        if len(points) < 2:
            return {
                'total_distance': 0,
                'total_time': 0,
                'avg_speed': 0,
                'max_speed': 0,
                'total_calories': 0
            }
        
        total_distance = 0
        raw_speeds = []
        compressed_speeds = []
        
        # 计算每段的距离和速度
        for i in range(1, len(points)):
            prev_point = points[i-1]
            curr_point = points[i]
            
            # 计算距离
            segment_distance = self.calculate_distance(
                prev_point['lat'], prev_point['lon'],
                curr_point['lat'], curr_point['lon']
            )
            total_distance += segment_distance
            
            # 计算时间差
            time_diff = (curr_point['time'] - prev_point['time']).total_seconds()
            
            # 计算原始速度
            if time_diff > 0:
                raw_speed = segment_distance / time_diff  # m/s
                raw_speeds.append(raw_speed)
                
                # 基于配置的目标配速进行速度压缩
                target_pace = self.config.get('target_pace', '5:30')
                target_speed = self.parse_target_pace(target_pace)
                
                # 基于目标速度创建合理的速度范围 (±15%)
                min_speed = target_speed * 0.85
                max_speed = target_speed * 1.15
                
                # 对原始速度进行调整，使其接近目标配速
                if raw_speed > max_speed * 1.5:  # 速度过快时进行压缩
                    # 压缩到目标范围
                    compressed_speed = min_speed + (raw_speed - max_speed * 1.5) / (raw_speed - max_speed * 1.5 + target_speed) * (max_speed - min_speed)
                elif raw_speed > max_speed:  # 轻微超速时轻微压缩
                    compressed_speed = max_speed + (raw_speed - max_speed) * 0.1
                else:
                    compressed_speed = raw_speed
                
                # 限制在合理的速度范围内
                compressed_speed = max(min_speed, min(compressed_speed, max_speed))
                compressed_speeds.append(compressed_speed)
            
            # 更新点的累积距离
            points[i]['cumulative_distance'] = total_distance
        
        # 设置第一个点的累积距离
        points[0]['cumulative_distance'] = 0
        
        # 计算总时间
        total_time = (points[-1]['time'] - points[0]['time']).total_seconds()
        
        # 使用压缩后的速度计算平均速度和最大速度
        avg_speed = sum(compressed_speeds) / len(compressed_speeds) if compressed_speeds else 0
        max_speed = max(compressed_speeds) if compressed_speeds else 0
        
        # 估算卡路里消耗
        total_calories = int((total_distance / 1000) * self.config['calories_per_km'])
        
        return {
            'total_distance': total_distance,
            'total_time': total_time,
            'avg_speed': avg_speed,
            'max_speed': max_speed,
            'total_calories': total_calories
        }
    
    def simulate_heart_rate(self, speed_ms, point_index, total_points):
        """
        模拟心率数据，基于配置的心率范围
        
        Args:
            speed_ms (float): 当前速度 (m/s)
            point_index (int): 当前点索引
            total_points (int): 总点数
            
        Returns:
            int: 模拟的心率值
        """
        # 使用配置的心率范围
        base_hr = self.config.get('base_hr', 120)
        max_hr = self.config.get('max_hr', 180)
        hr_factor = self.config.get('hr_factor', 1.5)
        
        # 运动进度因子（0-1）
        progress = point_index / max(1, total_points - 1)
        
        # 基于速度的心率调整
        speed_threshold = self.config.get('speed_threshold', 0.8)
        if speed_ms < speed_threshold:
            # 低速或静止时使用基础心率
            target_hr = base_hr
        else:
            # 根据速度调整心率
            speed_factor = min((speed_ms - speed_threshold) / 2.0, 1.0)
            target_hr = base_hr + (max_hr - base_hr) * speed_factor * hr_factor / 2.0
        
        # 添加运动进程的心率变化（热身和疲劳效应）
        if progress < 0.2:  # 热身阶段 - 轻微降低
            target_hr *= (0.95 + progress * 0.25)  # 0.95-1.0范围
        elif progress > 0.8:  # 疲劳阶段 - 轻微增加
            target_hr *= (1.0 + (progress - 0.8) * 0.15)  # 最多增加3%
        
        # 添加更大的随机波动增加真实性
        import random
        variation = random.uniform(-8, 12)  # 增加波动范围
        heart_rate = int(target_hr + variation)
        
        # 限制在合理范围内，但允许更大的变化
        return max(base_hr - 15, min(max_hr + 15, heart_rate))
    
    def simulate_cadence(self, speed_ms):
        """
        模拟步频数据，基于配置的跑步步频范围
        
        Args:
            speed_ms (float): 当前速度 (m/s)
            
        Returns:
            int: 模拟的步频值
        """
        # 使用配置的步频范围
        base_cadence = self.config.get('base_cadence', 50)
        max_cadence = self.config.get('max_cadence', 70)
            
        speed_threshold = self.config.get('speed_threshold', 0.8)
        
        # 对于极慢或静止状态，返回0或很低的步频
        if speed_ms < 0.5:  # 非常慢的速度
            return 0
        elif speed_ms < speed_threshold:
            return base_cadence
        
        # 基于速度的步频调整（速度越快步频稍高）
        speed_factor = min((speed_ms - speed_threshold) / 3.0, 1.0)
        
        # 计算步频
        cadence = base_cadence + (max_cadence - base_cadence) * speed_factor
        
        # 添加随机波动增加真实性
        import random
        variation = random.uniform(-3, 3)
        cadence = int(cadence + variation)
        
        # 限制在合理范围内
        return max(base_cadence - 5, min(max_cadence + 5, cadence))
    
    def simulate_power(self, speed_ms, heart_rate):
        """
        模拟功率数据，基于配置的功率范围
        
        Args:
            speed_ms (float): 当前速度 (m/s)
            heart_rate (int): 当前心率
            
        Returns:
            int: 模拟的功率值
        """
        speed_threshold = self.config.get('speed_threshold', 0.8)
        if speed_ms < speed_threshold:
            return 0
        
        # 使用配置的功率范围
        min_power = self.config.get('min_power', 150)
        max_power = self.config.get('max_power', 300)
        power_factor = self.config.get('power_factor', 2.5)
        
        # 基于速度和心率的功率调整
        speed_factor = min((speed_ms - speed_threshold) / 2.0, 1.0)
        
        # 心率因子计算（基于配置的心率范围）
        base_hr = self.config.get('base_hr', 120)
        max_hr = self.config.get('max_hr', 180)
        hr_factor = max(0, min(1, (heart_rate - base_hr) / max(1, max_hr - base_hr)))
        
        # 计算功率，结合速度和心率
        combined_factor = (speed_factor * 0.6 + hr_factor * 0.4) * power_factor / 3.0
        total_power = min_power + (max_power - min_power) * combined_factor
        
        # 添加随机波动增加真实性
        import random
        variation = random.uniform(-8, 8)
        total_power = int(total_power + variation)
        
        # 限制在合理范围内
        return max(min_power - 10, min(max_power + 10, total_power))
    
    def generate_tcx_content(self, points, metrics):
        """
        生成TCX文件内容
        
        Args:
            points (list): 轨迹点列表
            metrics (dict): 运动指标
            
        Returns:
            str: TCX文件内容
        """
        if not points:
            return ""
        
        # 确定开始时间
        if self.config.get('start_time'):
            # 处理时间输入格式
            start_time_input = self.config['start_time']
            
            if isinstance(start_time_input, datetime):
                # 如果已经是datetime对象，直接使用（保持本地时间）
                start_time = start_time_input
            elif isinstance(start_time_input, str):
                # 如果是字符串，需要解析
                if 'Z' in start_time_input:
                    # 如果已经是UTC格式，直接解析
                    start_time = datetime.fromisoformat(start_time_input.replace('Z', '+00:00'))
                else:
                    # 如果是本地时间格式，解析后转换为UTC时间
                    try:
                        # 尝试解析不同格式的时间
                        if 'T' in start_time_input:
                            local_time = datetime.fromisoformat(start_time_input)
                        else:
                            # 处理 "2025-09-09 01:52:39" 格式
                            local_time = datetime.strptime(start_time_input, '%Y-%m-%d %H:%M:%S')
                        # 直接使用本地时间，不进行时区转换
                        start_time = local_time
                    except:
                        # 如果解析失败，使用默认时间
                        start_time = datetime(2024, 12, 25, 6, 0, 0)
            else:
                # 其他类型，使用默认时间
                start_time = datetime(2024, 12, 25, 6, 0, 0)
                
            # 生成Activity ID，使用本地时间格式
            activity_id = start_time.strftime('%Y-%m-%dT%H:%M:%S.000')
        else:
            # 使用2024年12月25日早上6点作为默认开始时间
            start_time = datetime(2024, 12, 25, 6, 0, 0)
            activity_id = start_time.strftime('%Y-%m-%dT%H:%M:%S.000')
        
        # 根据压缩后的平均速度重新计算合理的总时间
        # 确保距离/时间比值与实际速度一致，避免运动平台显示异常配速
        realistic_total_time = metrics['total_distance'] / metrics['avg_speed'] if metrics['avg_speed'] > 0 else metrics['total_time']
        
        # 重新计算时间戳，确保与realistic_total_time一致
        if self.config.get('start_time'):
            # 使用自定义开始时间，按realistic_total_time重新分配时间间隔
            time_interval = realistic_total_time / max(1, len(points) - 1)
            for i, point in enumerate(points):
                point['time'] = start_time + timedelta(seconds=i * time_interval)
        else:
            # 使用原始时间，但按realistic_total_time重新分配时间间隔
            time_interval = realistic_total_time / max(1, len(points) - 1)
            for i, point in enumerate(points):
                point['time'] = start_time + timedelta(seconds=i * time_interval)
        
        # TCX文件头部
        tcx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase
  xsi:schemaLocation="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd"
  xmlns:ns5="http://www.garmin.com/xmlschemas/ActivityGoals/v1"
  xmlns:ns3="http://www.garmin.com/xmlschemas/ActivityExtension/v2"
  xmlns:ns2="http://www.garmin.com/xmlschemas/UserProfile/v2"
  xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ns4="http://www.garmin.com/xmlschemas/ProfileExtension/v1">
  <Activities>
    <Activity Sport="{sport}">
      <Id>{activity_id}</Id>
      <Lap StartTime="{start_time}">
        <TotalTimeSeconds>{total_time}</TotalTimeSeconds>
        <DistanceMeters>{total_distance}</DistanceMeters>
        <MaximumSpeed>{max_speed}</MaximumSpeed>
        <Calories>{calories}</Calories>
        <AverageHeartRateBpm>
          <Value>{avg_hr}</Value>
        </AverageHeartRateBpm>
        <MaximumHeartRateBpm>
          <Value>{max_hr}</Value>
        </MaximumHeartRateBpm>
        <Intensity>Active</Intensity>
        <TriggerMethod>Manual</TriggerMethod>
        <Track>'''.format(
            sport=self.config['activity_type'],
            activity_id=activity_id,
            start_time=start_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],
            total_time=realistic_total_time,
            total_distance=metrics['total_distance'],
            max_speed=metrics['max_speed'],
            calories=metrics['total_calories'],
            avg_hr=self.config['base_hr'] + 20,  # 估算平均心率
            max_hr=self.config['max_hr'] - 10    # 估算最大心率
        )
        
        # 生成轨迹点
        for i, point in enumerate(points):
            # 计算瞬时速度（基于相邻点）
            if i > 0:
                prev_point = points[i-1]
                time_diff = (point['time'] - prev_point['time']).total_seconds()
                distance_diff = point['cumulative_distance'] - prev_point['cumulative_distance']
                raw_speed = distance_diff / time_diff if time_diff > 0 else 0
                
                # 基于配置的目标配速计算合理的速度范围
                target_pace = self.config.get('target_pace', '5:30')
                target_speed = self.parse_target_pace(target_pace)
                
                # 基于目标速度创建合理的速度范围 (±15%)
                min_speed = target_speed * 0.85
                max_speed = target_speed * 1.15
                
                # 对原始速度进行调整，使其接近目标配速
                if raw_speed > max_speed * 1.5:  # 速度过快时进行压缩
                    # 压缩到目标范围
                    current_speed = min_speed + (raw_speed - max_speed * 1.5) / (raw_speed - max_speed * 1.5 + target_speed) * (max_speed - min_speed)
                elif raw_speed > max_speed:  # 轻微超速时轻微压缩
                    current_speed = max_speed + (raw_speed - max_speed) * 0.1
                else:
                    current_speed = raw_speed
                
                # 限制在合理的速度范围内
                current_speed = max(min_speed, min(current_speed, max_speed))
            else:
                current_speed = 0
            
            # 模拟运动指标
            heart_rate = self.simulate_heart_rate(current_speed, i, len(points))
            cadence = self.simulate_cadence(current_speed)
            power = self.simulate_power(current_speed, heart_rate)
            
            # 格式化时间（使用本地时间格式）
            time_str = point['time'].strftime('%Y-%m-%dT%H:%M:%S.000')
            
            # 生成轨迹点XML
            trackpoint_xml = f'''
          <Trackpoint>
            <Time>{time_str}</Time>
            <Position>
              <LatitudeDegrees>{point['lat']}</LatitudeDegrees>
              <LongitudeDegrees>{point['lon']}</LongitudeDegrees>
            </Position>
            <AltitudeMeters>{point['ele']}</AltitudeMeters>
            <DistanceMeters>{point['cumulative_distance']}</DistanceMeters>
            <HeartRateBpm>
              <Value>{heart_rate}</Value>
            </HeartRateBpm>
            <Extensions>
              <ns3:TPX>
                <ns3:Speed>{current_speed}</ns3:Speed>
                <ns3:RunCadence>{cadence}</ns3:RunCadence>
                <ns3:Watts>{power}</ns3:Watts>
              </ns3:TPX>
            </Extensions>
          </Trackpoint>'''
            
            tcx_content += trackpoint_xml
        
        # 计算汇总统计数据
        all_cadences = []
        all_powers = []
        
        for i, point in enumerate(points):
            if i > 0:
                prev_point = points[i-1]
                time_diff = (point['time'] - prev_point['time']).total_seconds()
                distance_diff = point['cumulative_distance'] - prev_point['cumulative_distance']
                raw_speed = distance_diff / time_diff if time_diff > 0 else 0
                
                # 基于配置的目标配速计算合理的速度范围
                target_pace = self.config.get('target_pace', '5:30')
                target_speed = self.parse_target_pace(target_pace)
                
                # 基于目标速度创建合理的速度范围 (±15%)
                min_speed = target_speed * 0.85
                max_speed = target_speed * 1.15
                
                # 对原始速度进行调整，使其接近目标配速
                if raw_speed > max_speed * 1.5:  # 速度过快时进行压缩
                    current_speed = min_speed + (raw_speed - max_speed * 1.5) / (raw_speed - max_speed * 1.5 + target_speed) * (max_speed - min_speed)
                elif raw_speed > max_speed:  # 轻微超速时轻微压缩
                    current_speed = max_speed + (raw_speed - max_speed) * 0.1
                else:
                    current_speed = raw_speed
                
                # 限制在合理的速度范围内
                current_speed = max(min_speed, min(current_speed, max_speed))
                
                # 收集统计数据
                cadence = self.simulate_cadence(current_speed)
                heart_rate = self.simulate_heart_rate(current_speed, i, len(points))
                power = self.simulate_power(current_speed, heart_rate)
                
                if cadence > 0:  # 只统计有效步频
                    all_cadences.append(cadence)
                if power > 0:  # 只统计有效功率
                    all_powers.append(power)
        
        # 计算平均值和最大值
        avg_cadence = int(sum(all_cadences) / len(all_cadences)) if all_cadences else self.config.get('base_cadence', 50)
        max_cadence = max(all_cadences) if all_cadences else self.config.get('max_cadence', 70)
        avg_power = int(sum(all_powers) / len(all_powers)) if all_powers else self.config.get('min_power', 150)
        max_power = max(all_powers) if all_powers else self.config.get('max_power', 300)
        
        # TCX文件尾部（模拟Garmin设备）
        tcx_content += f'''
        </Track>
        <Extensions>
          <ns3:LX>
            <ns3:AvgSpeed>{metrics['avg_speed']:.6f}</ns3:AvgSpeed>
            <ns3:AvgRunCadence>{avg_cadence}</ns3:AvgRunCadence>
            <ns3:MaxRunCadence>{max_cadence}</ns3:MaxRunCadence>
            <ns3:AvgWatts>{avg_power}</ns3:AvgWatts>
            <ns3:MaxWatts>{max_power}</ns3:MaxWatts>
          </ns3:LX>
        </Extensions>
      </Lap>
      <Creator xsi:type="Device_t">
        <Name>{escape(self.config.get('device_name', 'Forerunner 570'))} - 47mm</Name>
        <UnitId>3605783213</UnitId>
        <ProductID>4570</ProductID>
        <Version>
          <VersionMajor>{self.config.get('device_version', '12.70').split('.')[0]}</VersionMajor>
          <VersionMinor>{self.config.get('device_version', '12.70').split('.')[1] if '.' in self.config.get('device_version', '12.70') else '0'}</VersionMinor>
          <BuildMajor>0</BuildMajor>
          <BuildMinor>0</BuildMinor>
        </Version>
      </Creator>
    </Activity>
  </Activities>
  <Author xsi:type="Application_t">
    <Name>GPX to TCX Converter by mariohuang</Name>
    <Build>
      <Version>
        <VersionMajor>1</VersionMajor>
        <VersionMinor>0</VersionMinor>
        <BuildMajor>0</BuildMajor>
        <BuildMinor>0</BuildMinor>
      </Version>
    </Build>
    <LangID>en</LangID>
    <PartNumber>GPX-TCX-001</PartNumber>
  </Author>
</TrainingCenterDatabase>'''
        
        return tcx_content
    
    def convert(self, gpx_file_path, output_path):
        """
        转换GPX文件为TCX文件
        
        Args:
            gpx_file_path (str): GPX文件路径
            output_path (str): 输出TCX文件路径
            
        Returns:
            bool: 转换是否成功
        """
        print(f"🔄 正在解析GPX文件: {gpx_file_path}")
        points = self.parse_gpx_file(gpx_file_path)
        
        if not points:
            print("❌ GPX文件解析失败或没有轨迹点")
            return False
        
        print(f"🔄 正在计算运动指标...")
        metrics = self.calculate_metrics(points)
        
        print(f"📏 总距离: {metrics['total_distance']:.2f} 米")
        print(f"⏱️  总时间: {metrics['total_time']:.0f} 秒")
        print(f"🏃 平均速度: {metrics['avg_speed']:.2f} m/s")
        print(f"🔥 估算卡路里: {metrics['total_calories']} 卡")
        
        print(f"🔄 正在生成TCX文件...")
        tcx_content = self.generate_tcx_content(points, metrics)
        
        try:
            print(f"💾 正在保存到: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(tcx_content)
            print("✅ 转换完成！")
            return True
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
            return False


def print_usage_examples():
    """
    打印使用示例
    """
    print("\n" + "="*60)
    print("📖 使用示例")
    print("="*60)
    print("\n1. 基本用法：")
    print("   python3 gpx_to_tcx.py 路径.gpx -o 运动.tcx")
    
    print("\n2. 自定义心率参数：")
    print("   python3 gpx_to_tcx.py 路径.gpx -o 运动.tcx \\")
    print("     --base-hr 120 --max-hr 175")
    
    print("\n3. 自定义开始时间：")
    print("   python3 gpx_to_tcx.py 路径.gpx -o 运动.tcx \\")
    print("     --start-time 2024-12-25T08:30:00Z")
    
    print("\n4. 自定义运动类型：")
    print("   python3 gpx_to_tcx.py 路径.gpx -o 运动.tcx \\")
    print("     --activity-type Biking --base-cadence 80")
    
    print("\n5. 完整自定义：")
    print("   python3 gpx_to_tcx.py 路径.gpx -o 运动.tcx \\")
    print("     --base-hr 110 --max-hr 180 --activity-type Running \\")
    print("     --start-time 2024-12-25T08:30:00Z --calories-per-km 65")
    print("\n" + "="*60)


def main():
    """
    主函数：处理命令行参数并执行转换操作
    """
    parser = argparse.ArgumentParser(
        description='将GPX文件转换为TCX文件，生成完整的运动数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n更多使用示例请运行: python3 gpx_to_tcx.py --examples"
    )
    
    # 先检查是否请求显示示例
    if '--examples' in sys.argv:
        print_usage_examples()
        return
    
    # 基本参数
    parser.add_argument('gpx_file', help='输入的GPX文件路径')
    parser.add_argument('-o', '--output', default='converted_activity.tcx', help='输出TCX文件路径（默认为converted_activity.tcx）')
    parser.add_argument('--examples', action='store_true', help='显示使用示例')
    
    # 心率参数
    parser.add_argument('--base-hr', type=int, default=120, help='基础心率 (默认: 120)')
    parser.add_argument('--max-hr', type=int, default=180, help='最大心率 (默认: 180)')
    parser.add_argument('--hr-factor', type=float, default=1.5, help='心率调整系数 (默认: 1.5)')
    
    # 步频参数
    parser.add_argument('--base-cadence', type=int, default=160, help='基础步频 (默认: 160)')
    parser.add_argument('--max-cadence', type=int, default=180, help='最大步频 (默认: 180)')
    parser.add_argument('--cadence-factor', type=float, default=2.0, help='步频调整系数 (默认: 2.0)')
    
    # 功率参数
    parser.add_argument('--power-factor', type=float, default=1.0, help='功率计算系数 (默认: 1.0)')
    parser.add_argument('--min-power', type=int, default=100, help='最小功率 (默认: 100)')
    
    # 其他参数
    parser.add_argument('--speed-threshold', type=float, default=0.8, help='运动速度阈值 (默认: 0.8)')
    parser.add_argument('--start-time', type=str, help='自定义活动开始时间 (ISO格式，如: 2024-01-01T10:00:00Z)')
    parser.add_argument('--activity-type', type=str, default='Running', help='运动类型 (默认: Running)')
    parser.add_argument('--device-name', type=str, default='GPX Converter', help='设备名称 (默认: GPX Converter)')
    parser.add_argument('--calories-per-km', type=int, default=60, help='每公里消耗卡路里 (默认: 60)')
    
    args = parser.parse_args()
    
    # 检查必需参数
    if not args.gpx_file:
        parser.print_help()
        return
    
    # 打印配置信息
    print("\n" + "="*50)
    print("🚀 GPX转TCX工具")
    print("="*50)
    print(f"📁 GPX文件: {args.gpx_file}")
    print(f"📁 输出文件: {args.output}")
    print("\n⚙️  配置参数:")
    print(f"  运动类型: {args.activity_type}")
    print(f"  基础心率: {args.base_hr} bpm")
    print(f"  最大心率: {args.max_hr} bpm")
    print(f"  心率系数: {args.hr_factor}")
    print(f"  基础步频: {args.base_cadence} spm")
    print(f"  最大步频: {args.max_cadence} spm")
    print(f"  步频系数: {args.cadence_factor}")
    print(f"  功率系数: {args.power_factor}")
    print(f"  最小功率: {args.min_power} W")
    print(f"  速度阈值: {args.speed_threshold} m/s")
    print(f"  设备名称: {args.device_name}")
    print(f"  卡路里/公里: {args.calories_per_km}")
    if args.start_time:
        print(f"  开始时间: {args.start_time}")
    print("="*50)
    
    # 构建配置字典
    config = {
        'base_hr': args.base_hr,
        'max_hr': args.max_hr,
        'hr_factor': args.hr_factor,
        'base_cadence': args.base_cadence,
        'max_cadence': args.max_cadence,
        'cadence_factor': args.cadence_factor,
        'power_factor': args.power_factor,
        'min_power': args.min_power,
        'speed_threshold': args.speed_threshold,
        'start_time': args.start_time,
        'activity_type': args.activity_type,
        'device_name': args.device_name,
        'calories_per_km': args.calories_per_km
    }
    
    # 创建转换器并执行转换
    converter = GPXToTCXConverter(config)
    success = converter.convert(args.gpx_file, args.output)
    
    if success:
        print(f"\n🎉 成功！TCX文件已保存为: {args.output}")
        print("\n💡 提示：")
        print("   - 生成的TCX文件可以直接上传到Garmin Connect、Strava等平台")
        print("   - 如需调整运动数据，请使用相应的命令行参数")
        print("   - 运行 --examples 查看更多使用示例")
    else:
        print("\n❌ 转换失败，请检查输入文件")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
