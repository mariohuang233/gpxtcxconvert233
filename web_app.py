#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, abort
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
import shutil
from datetime import datetime, timedelta
import json
from gpx_to_tcx import GPXToTCXConverter
import threading
import time
import logging
from pathlib import Path
import psutil
import requests

app = Flask(__name__)
app.secret_key = 'gpx_to_tcx_converter_2025'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 配置
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'gpx'}

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 确保文件夹存在
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 存储转换任务状态
conversion_tasks = {}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class ConversionTask:
    """转换任务类"""
    def __init__(self, task_id, input_file, output_file, config):
        self.task_id = task_id
        self.input_file = input_file
        self.output_file = output_file
        self.config = config
        self.status = 'pending'  # pending, processing, completed, error
        self.progress = 0
        self.message = '等待开始转换...'
        self.error = None
        self.created_at = datetime.now()
        self.completed_at = None
        
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

def perform_conversion(task):
    """执行转换任务"""
    try:
        task.status = 'processing'
        task.progress = 10
        task.message = '正在初始化转换器...'
        logger.info(f"开始转换任务 {task.task_id}")
        
        # 创建转换器
        converter = GPXToTCXConverter()
        
        # 应用配置
        task.progress = 20
        task.message = '正在应用配置...'
        
        converter.config.update({
            'activity_type': task.config.get('activity_type', 'Running'),
            'device_name': task.config.get('device_name', 'Forerunner 570'),
            'device_version': task.config.get('device_version', '12.70'),
            'base_hr': int(task.config.get('base_hr', 135)),
            'max_hr': int(task.config.get('max_hr', 165)),
            'base_cadence': int(task.config.get('base_cadence', 50)),
            'max_cadence': int(task.config.get('max_cadence', 70)),
            'base_power': int(task.config.get('base_power', 150)),
            'max_power': int(task.config.get('max_power', 300)),
            'calories_per_km': int(task.config.get('calories_per_km', 60)),
            'weight': int(task.config.get('weight', 70)),
            'target_pace': task.config.get('target_pace', '5:30')
        })
        
        # 处理开始时间
        start_time_str = task.config.get('start_time', '').strip()
        if start_time_str:
            try:
                # 支持HTML datetime-local格式: 2024-01-01T10:30
                if 'T' in start_time_str:
                    # HTML datetime-local 输入的是本地时间，需要保持原样
                    start_time = datetime.fromisoformat(start_time_str)
                else:
                    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                
                # 直接使用用户输入的本地时间，不进行时区转换
                converter.config['start_time'] = start_time
                logger.info(f"设置自定义开始时间 (本地时间): {start_time}")
            except (ValueError, TypeError) as e:
                logger.warning(f"时间格式解析失败: {start_time_str}, 错误: {e}")
                pass  # 使用GPX文件中的时间
        
        logger.info(f"转换器配置完成: {task.config}")
        
        task.progress = 40
        task.message = '正在解析GPX文件...'
        
        # 执行转换
        task.progress = 60
        task.message = '转换中...'
        
        success = converter.convert(task.input_file, task.output_file)
        
        task.progress = 90
        task.message = '保存文件...'
        
        if success and os.path.exists(task.output_file):
            file_size = os.path.getsize(task.output_file)
            task.progress = 100
            task.status = 'completed'
            task.message = f'转换完成！文件大小: {file_size/1024:.1f} KB'
            task.completed_at = datetime.now()
            logger.info(f"转换任务 {task.task_id} 完成，输出文件: {task.output_file}")
        else:
            task.status = 'error'
            task.error = '转换失败，请检查GPX文件格式'
            
    except Exception as e:
        logger.error(f"转换任务 {task.task_id} 失败: {str(e)}")
        task.status = 'error'
        task.error = f'转换过程中出现错误: {str(e)}'
        
@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '只支持GPX文件格式'}), 400
        
        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'文件大小超过限制 ({MAX_FILE_SIZE // (1024*1024)}MB)'}), 400
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_{filename}")
        file.save(input_path)
        
        # 生成输出文件路径
        output_filename = filename.rsplit('.', 1)[0] + '.tcx'
        output_path = os.path.join(OUTPUT_FOLDER, f"{task_id}_{output_filename}")
        
        # 获取配置
        config = {
            'activity_type': request.form.get('activity_type', 'Running'),
            'device_name': request.form.get('device_name', 'Forerunner 570'),
            'device_version': request.form.get('device_version', '12.70'),
            'base_hr': request.form.get('base_hr', '135'),
            'max_hr': request.form.get('max_hr', '165'),
            'base_cadence': request.form.get('base_cadence', '50'),
            'max_cadence': request.form.get('max_cadence', '70'),
            'base_power': request.form.get('base_power', '150'),
            'max_power': request.form.get('max_power', '300'),
            'calories_per_km': request.form.get('calories_per_km', '60'),
            'weight': request.form.get('weight', '70'),
            'target_pace': request.form.get('target_pace', '5:30'),
            'start_time': request.form.get('start_time', '')
        }
        
        # 创建转换任务
        task = ConversionTask(task_id, input_path, output_path, config)
        conversion_tasks[task_id] = task
        
        # 启动转换线程
        thread = threading.Thread(target=perform_conversion, args=(task,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'message': '文件上传成功，开始转换...',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/status/<task_id>')
def get_status(task_id):
    """获取转换状态"""
    task = conversion_tasks.get(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify(task.to_dict())

@app.route('/convert', methods=['POST'])
def convert_file():
    """直接转换文件（兼容性路由）"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '只支持GPX文件格式'}), 400
        
        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'文件大小超过限制 ({MAX_FILE_SIZE // (1024*1024)}MB)'}), 400
        
        # 生成临时文件名
        task_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_{filename}")
        file.save(input_path)
        
        # 生成输出文件路径
        output_filename = filename.rsplit('.', 1)[0] + '.tcx'
        output_path = os.path.join(OUTPUT_FOLDER, f"{task_id}_{output_filename}")
        
        # 创建转换器并执行转换
        converter = GPXToTCXConverter()
        
        # 应用默认配置
        converter.config.update({
            'activity_type': 'Running',
            'device_name': 'Forerunner 570',
            'device_version': '12.70',
            'base_hr': 135,
            'max_hr': 165,
            'base_cadence': 50,
            'max_cadence': 70,
            'base_power': 150,
            'max_power': 300,
            'calories_per_km': 60,
            'weight': 70,
            'target_pace': '5:30'
        })
        
        # 执行转换
        success = converter.convert(input_path, output_path)
        
        if success and os.path.exists(output_path):
            # 返回转换后的文件
            return send_file(
                output_path,
                as_attachment=True,
                download_name=output_filename,
                mimetype='application/xml'
            )
        else:
            return jsonify({'error': '转换失败'}), 500
            
    except Exception as e:
        logger.error(f"转换失败: {str(e)}")
        return jsonify({'error': f'转换失败: {str(e)}'}), 500
    finally:
        # 清理临时文件
        try:
            if 'input_path' in locals() and os.path.exists(input_path):
                os.remove(input_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                # 延迟删除输出文件，给下载一些时间
                threading.Timer(30.0, lambda: os.path.exists(output_path) and os.remove(output_path)).start()
        except Exception as e:
            logger.warning(f"清理临时文件失败: {str(e)}")

@app.route('/download/<task_id>')
def download_file(task_id):
    """下载转换后的文件"""
    task = conversion_tasks.get(task_id)
    if not task:
        logger.warning(f"下载请求失败: 任务 {task_id} 不存在")
        abort(404)
    
    if task.status != 'completed':
        logger.warning(f"下载请求失败: 任务 {task_id} 状态为 {task.status}")
        return jsonify({'error': '转换尚未完成'}), 400
    
    if not os.path.exists(task.output_file):
        logger.error(f"下载请求失败: 文件 {task.output_file} 不存在")
        return jsonify({'error': '输出文件不存在'}), 404
    
    # 获取原始文件名
    original_filename = os.path.basename(task.input_file).split('_', 1)[1]
    base_name = original_filename.rsplit('.', 1)[0]
    download_filename = f'{base_name}_converted.tcx'
    
    logger.info(f"开始下载文件: {task.output_file} -> {download_filename}")
    
    try:
        return send_file(
            task.output_file,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/xml'
        )
    except Exception as e:
        logger.error(f"文件下载失败: {str(e)}")
        return jsonify({'error': '文件下载失败'}), 500

def cleanup_old_files():
    """清理旧文件和任务"""
    try:
        current_time = datetime.now()
        cleaned_files = 0
        cleaned_tasks = 0
        
        # 清理超过1小时的任务和文件
        tasks_to_remove = []
        for task_id, task in list(conversion_tasks.items()):
            if (current_time - task.created_at).total_seconds() > 3600:  # 1小时
                # 删除相关文件
                for file_path in [task.input_file, task.output_file]:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            cleaned_files += 1
                            logger.info(f"删除过期文件: {file_path}")
                        except Exception as e:
                            logger.warning(f"删除文件失败 {file_path}: {str(e)}")
                tasks_to_remove.append(task_id)
        
        # 从内存中移除任务
        for task_id in tasks_to_remove:
            del conversion_tasks[task_id]
            cleaned_tasks += 1
        
        # 清理空的上传和输出目录中的孤立文件
        for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path):
                        file_age = current_time.timestamp() - os.path.getmtime(file_path)
                        if file_age > 3600:  # 1小时
                            try:
                                os.remove(file_path)
                                cleaned_files += 1
                                logger.info(f"删除孤立文件: {file_path}")
                            except Exception as e:
                                logger.warning(f"删除孤立文件失败 {file_path}: {str(e)}")
        
        logger.info(f"清理完成: {cleaned_files} 个文件, {cleaned_tasks} 个任务")
        return cleaned_files, cleaned_tasks
        
    except Exception as e:
        logger.error(f"清理过程中出现错误: {str(e)}")
        return 0, 0

@app.route('/cleanup')
def cleanup_endpoint():
    """手动清理端点"""
    try:
        cleaned_files, cleaned_tasks = cleanup_old_files()
        return jsonify({
            'message': f'清理完成，删除了 {cleaned_files} 个文件，{cleaned_tasks} 个任务',
            'cleaned_files': cleaned_files,
            'cleaned_tasks': cleaned_tasks
        })
    except Exception as e:
        return jsonify({'error': f'清理过程中出现错误: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """健康检查端点"""
    try:
        # 检查系统资源
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 检查必要目录
        directories_ok = all(os.path.exists(folder) for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER])
        
        # 检查活跃任务数量
        active_tasks = len([task for task in conversion_tasks.values() if task.status in ['pending', 'processing']])
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available // (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free // (1024 * 1024 * 1024)
            },
            'application': {
                'directories_ok': directories_ok,
                'active_tasks': active_tasks,
                'total_tasks': len(conversion_tasks)
            }
        }
        
        # 检查是否有异常情况
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
            health_status['status'] = 'warning'
            health_status['warnings'] = []
            if cpu_percent > 90:
                health_status['warnings'].append('High CPU usage')
            if memory.percent > 90:
                health_status['warnings'].append('High memory usage')
            if disk.percent > 95:
                health_status['warnings'].append('Low disk space')
        
        if not directories_ok:
            health_status['status'] = 'unhealthy'
            health_status['error'] = 'Required directories not accessible'
            return jsonify(health_status), 503
        
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': f'Health check failed: {str(e)}'
        }), 503

@app.route('/1.jpg')
def serve_background_image():
    """提供背景图片"""
    try:
        return send_file('1.jpg', mimetype='image/jpeg')
    except FileNotFoundError:
        abort(404)

@app.route('/greeting-info')
def get_greeting_info():
    """获取用户位置和天气信息用于个性化问候"""
    try:
        # 获取用户真实IP地址
        if request.headers.get('X-Forwarded-For'):
            user_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            user_ip = request.headers.get('X-Real-IP')
        else:
            user_ip = request.remote_addr
        
        # 如果是本地IP，直接使用默认位置信息
        if user_ip in ['127.0.0.1', '::1', 'localhost']:
            # 使用默认的北京位置信息
            ip_data = {
                'country_name': 'China',
                'country_code': 'CN',
                'region_name': 'Beijing',
                'city': 'Beijing',
                'latitude': 39.9042,
                'longitude': 116.4074,
                'time_zone': {'id': 'Asia/Shanghai'},
                'connection': {'isp': 'Local Network'},
                'continent_name': 'Asia'
            }
        else:
            # 尝试多个IP地理位置API服务
            ip_data = None
            
            # API服务列表（按优先级排序）
            api_services = [
                # ip-api.com - 免费，无需API密钥
                {
                    'name': 'ip-api.com',
                    'url': f'http://ip-api.com/json/{user_ip}?fields=status,message,country,countryCode,region,regionName,city,lat,lon,timezone,isp,continent',
                    'parser': lambda data: {
                        'country_name': data.get('country', 'Unknown'),
                        'country_code': data.get('countryCode', 'XX'),
                        'region_name': data.get('regionName', 'Unknown Region'),
                        'city': data.get('city', 'Unknown City'),
                        'latitude': data.get('lat', 39.9042),
                        'longitude': data.get('lon', 116.4074),
                        'time_zone': {'id': data.get('timezone', 'UTC')},
                        'connection': {'isp': data.get('isp', 'Unknown ISP')},
                        'continent_name': data.get('continent', 'Unknown')
                    } if data.get('status') == 'success' else None
                },
                # ipapi.co - 免费，无需API密钥
                {
                    'name': 'ipapi.co',
                    'url': f'https://ipapi.co/{user_ip}/json/',
                    'parser': lambda data: {
                        'country_name': data.get('country_name', 'Unknown'),
                        'country_code': data.get('country_code', 'XX'),
                        'region_name': data.get('region', 'Unknown Region'),
                        'city': data.get('city', 'Unknown City'),
                        'latitude': data.get('latitude', 39.9042),
                        'longitude': data.get('longitude', 116.4074),
                        'time_zone': {'id': data.get('timezone', 'UTC')},
                        'connection': {'isp': data.get('org', 'Unknown ISP')},
                        'continent_name': data.get('continent_code', 'Unknown')
                    } if not data.get('error') else None
                },
                # ipwhois.io - 免费，无需API密钥
                {
                    'name': 'ipwhois.io',
                    'url': f'http://ipwhois.app/json/{user_ip}',
                    'parser': lambda data: {
                        'country_name': data.get('country', 'Unknown'),
                        'country_code': data.get('country_code', 'XX'),
                        'region_name': data.get('region', 'Unknown Region'),
                        'city': data.get('city', 'Unknown City'),
                        'latitude': data.get('latitude', 39.9042),
                        'longitude': data.get('longitude', 116.4074),
                        'time_zone': {'id': data.get('timezone', 'UTC')},
                        'connection': {'isp': data.get('isp', 'Unknown ISP')},
                        'continent_name': data.get('continent', 'Unknown')
                    } if data.get('success') else None
                },
                # ipstack - 备用（有API密钥限制）
                {
                    'name': 'ipstack',
                    'url': f'http://api.ipstack.com/{user_ip}?access_key=a67f3911868f6c642b949296b6f6ef6a',
                    'parser': lambda data: {
                        'country_name': data.get('country_name', 'Unknown'),
                        'country_code': data.get('country_code', 'XX'),
                        'region_name': data.get('region_name', 'Unknown Region'),
                        'city': data.get('city', 'Unknown City'),
                        'latitude': data.get('latitude', 39.9042),
                        'longitude': data.get('longitude', 116.4074),
                        'time_zone': data.get('time_zone', {'id': 'UTC'}),
                        'connection': data.get('connection', {'isp': 'Unknown ISP'}),
                        'continent_name': data.get('continent_name', 'Unknown')
                    } if not data.get('error') and data.get('city') else None
                }
            ]
            
            # 依次尝试各个API服务
            for service in api_services:
                try:
                    response = requests.get(service['url'], timeout=3)
                    if response.status_code == 200:
                        data = response.json()
                        parsed_data = service['parser'](data)
                        if parsed_data and parsed_data.get('city') != 'Unknown City':
                            ip_data = parsed_data
                            logger.info(f"成功使用 {service['name']} 获取位置信息")
                            break
                except Exception as e:
                    logger.warning(f"{service['name']} API调用失败: {str(e)}")
                    continue
            
            # 如果所有API都失败，使用默认位置
            if not ip_data:
                ip_data = {
                    'country_name': 'Unknown',
                    'country_code': 'XX',
                    'region_name': 'Unknown Region',
                    'city': 'Unknown City',
                    'latitude': 39.9042,  # 默认北京坐标
                    'longitude': 116.4074,
                    'time_zone': {'id': 'UTC'},
                    'connection': {'isp': 'Unknown ISP'},
                    'continent_name': 'Unknown'
                }
                logger.info("所有IP地理位置API都失败，使用默认位置信息")
        
        # 获取城市名称用于天气查询
        city = ip_data.get('city', 'Beijing')
        if not city or city == 'Unknown':
            city = ip_data.get('region_name', 'Beijing')
        
        # 使用Open-Meteo免费天气API（无需API密钥）
        latitude = ip_data.get('latitude')
        longitude = ip_data.get('longitude')
        
        weather_info = None
        
        if latitude and longitude:
            # Open-Meteo API调用
            weather_url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weather_code&timezone=auto'
            
            try:
                weather_response = requests.get(weather_url, timeout=10)
                
                if weather_response.status_code == 200:
                    weather_data = weather_response.json()
                    
                    if 'current' in weather_data:
                        current = weather_data['current']
                        
                        # 天气代码映射到中文描述
                        weather_codes = {
                            0: '晴朗', 1: '晴朗', 2: '部分多云', 3: '多云',
                            45: '雾', 48: '雾凇', 51: '小雨', 53: '中雨', 55: '大雨',
                            61: '小雨', 63: '中雨', 65: '大雨', 71: '小雪', 73: '中雪', 75: '大雪',
                            80: '阵雨', 81: '阵雨', 82: '暴雨', 95: '雷暴', 96: '雷暴', 99: '雷暴'
                        }
                        
                        weather_code = current.get('weather_code', 0)
                        weather_desc = weather_codes.get(weather_code, '晴朗')
                        
                        # 只有当所有关键数据都存在时才显示天气信息
                        if (current.get('temperature_2m') is not None and 
                            current.get('relative_humidity_2m') is not None and 
                            current.get('wind_speed_10m') is not None):
                            weather_info = {
                                'temperature': f"{round(current.get('temperature_2m', 0))}°C",
                                'description': weather_desc,
                                'humidity': f"{current.get('relative_humidity_2m')}%",
                                'wind_speed': f"{round(current.get('wind_speed_10m', 0))} km/h",
                                'wind_dir': f"{current.get('wind_direction_10m', 0)}°"
                            }
            except Exception as e:
                # 天气API调用失败时，weather_info保持为None
                pass
        
        return jsonify({
            'success': True,
            'data': {
                'location': {
                    'ip': user_ip,
                    'country': ip_data.get('country_name', 'Unknown'),
                    'country_code': ip_data.get('country_code', 'Unknown'),
                    'region': ip_data.get('region_name', 'Unknown'),
                    'city': ip_data.get('city', 'Unknown'),
                    'latitude': ip_data.get('latitude', 0),
                    'longitude': ip_data.get('longitude', 0),
                    'timezone': ip_data.get('time_zone', {}).get('id', 'Unknown'),
                    'isp': ip_data.get('connection', {}).get('isp', 'Unknown'),
                    'continent': ip_data.get('continent_name', 'Unknown')
                },
                'weather': weather_info,
                'greeting': f"你好，来自{ip_data.get('city', ip_data.get('region_name', '未知地区'))}的用户！" + (f"今天天气{weather_info['description']}，气温{weather_info['temperature']}" if weather_info else "欢迎使用GPX转TCX转换器")
            }
        })
            
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'API请求超时'
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'网络请求错误: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        })

# 定时清理任务
def schedule_cleanup():
    """定时清理任务"""
    while True:
        try:
            time.sleep(1800)  # 每30分钟清理一次
            cleanup_old_files()
        except Exception as e:
            logger.error(f"定时清理任务出错: {str(e)}")

# 启动定时清理线程
cleanup_thread = threading.Thread(target=schedule_cleanup, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    # 创建必要的目录
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # 获取端口号，优先使用环境变量PORT，否则使用8888
    port = int(os.environ.get('PORT', 8888))
    
    print("🌐 GPX转TCX Web应用启动中...")
    print(f"📁 本地访问: http://localhost:{port}")
    print(f"🌍 网络访问: http://你的IP地址:{port}")
    print("🔧 支持功能: 文件上传、实时转换、配置自定义")
    print("👥 同事可通过网络地址访问此应用")
    print("⚠️  仅用于测试场景，不能作为比赛作弊用途")
    
    # 在生产环境中关闭debug模式
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)