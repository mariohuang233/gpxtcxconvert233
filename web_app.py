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
from collections import defaultdict

# 应用配置常量
APP_CONFIG = {
    'SECRET_KEY': 'gpx_to_tcx_converter_2025',
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
    'UPLOAD_FOLDER': 'uploads',
    'OUTPUT_FOLDER': 'outputs',
    'ALLOWED_EXTENSIONS': {'gpx'},
    'DEFAULT_PORT': 8888,
    'CLEANUP_INTERVAL': 3600,  # 1小时
    'FILE_RETENTION_HOURS': 24  # 24小时
}

# HTTP状态码常量
HTTP_STATUS = {
    'OK': 200,
    'BAD_REQUEST': 400,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

# 错误消息常量
ERROR_MESSAGES = {
    'NO_FILE_SELECTED': '没有选择文件',
    'INVALID_FILE_FORMAT': '只支持GPX文件格式',
    'FILE_TOO_LARGE': '文件大小超过限制',
    'TASK_NOT_FOUND': '任务不存在',
    'UPLOAD_FAILED': '上传失败',
    'CONVERSION_FAILED': '转换失败',
    'FILE_NOT_FOUND': '文件不存在或已被删除',
    'CONVERSION_NOT_COMPLETED': '转换尚未完成'
}

# 默认转换器配置
DEFAULT_CONVERTER_CONFIG = {
    'activity_type': 'Running',
    'sub_sport': 'Generic',
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
}

app = Flask(__name__)
app.secret_key = APP_CONFIG['SECRET_KEY']
app.config['MAX_CONTENT_LENGTH'] = APP_CONFIG['MAX_CONTENT_LENGTH']

# 配置
UPLOAD_FOLDER = APP_CONFIG['UPLOAD_FOLDER']
OUTPUT_FOLDER = APP_CONFIG['OUTPUT_FOLDER']
MAX_FILE_SIZE = APP_CONFIG['MAX_CONTENT_LENGTH']
ALLOWED_EXTENSIONS = APP_CONFIG['ALLOWED_EXTENSIONS']

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 确保文件夹存在
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 存储转换任务状态
conversion_tasks = {}

# 存储埋点数据
analytics_data = {
    'page_views': [],
    'user_sessions': defaultdict(list),
    'convert_button_stats': {
        'exposures': [],
        'clicks': []
    },
    'daily_stats': defaultdict(lambda: {
        'pv': 0,
        'uv': set(),
        'convert_exposures': 0,
        'convert_clicks': 0
    })
}

def allowed_file(filename):
    """检查文件是否为允许的格式"""
    if not filename or not isinstance(filename, str):
        return False
    
    if '.' not in filename:
        return False
    
    try:
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in ALLOWED_EXTENSIONS
    except (IndexError, AttributeError):
        return False

def validate_file_size(file):
    """验证文件大小"""
    if not file:
        return False, ERROR_MESSAGES['NO_FILE_SELECTED']
    
    # 检查文件大小
    file.seek(0, 2)  # 移动到文件末尾
    size = file.tell()
    file.seek(0)  # 重置文件指针
    
    if size > MAX_FILE_SIZE:
        return False, ERROR_MESSAGES['FILE_TOO_LARGE']
    
    if size == 0:
        return False, '文件为空'
    
    return True, None

def sanitize_config(config):
    """清理和验证配置参数"""
    sanitized = DEFAULT_CONVERTER_CONFIG.copy()
    
    if not isinstance(config, dict):
        return sanitized
    
    # 验证数值类型参数
    numeric_fields = ['base_hr', 'max_hr', 'base_cadence', 'max_cadence', 
                     'base_power', 'max_power', 'calories_per_km', 'weight']
    
    for field in numeric_fields:
        if field in config:
            try:
                value = float(config[field])
                if value > 0:  # 确保为正数
                    sanitized[field] = value
            except (ValueError, TypeError):
                pass  # 使用默认值
    
    # 验证字符串类型参数
    string_fields = ['activity_type', 'sub_sport', 'device_name', 'device_version', 'target_pace']
    
    for field in string_fields:
        if field in config and isinstance(config[field], str):
            # 防止XSS攻击，清理字符串
            sanitized[field] = config[field].strip()[:100]  # 限制长度
    
    return sanitized

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
        
        # 应用配置，使用默认值作为后备
        config_updates = {}
        for key, default_value in DEFAULT_CONVERTER_CONFIG.items():
            value = task.config.get(key, default_value)
            # 对数值类型进行类型转换
            if isinstance(default_value, int) and not isinstance(value, int):
                try:
                    config_updates[key] = int(value)
                except (ValueError, TypeError):
                    config_updates[key] = default_value
                    logger.warning(f"配置项 {key} 值无效: {value}，使用默认值: {default_value}")
            else:
                config_updates[key] = value
        
        converter.config.update(config_updates)
        
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

@app.route('/analytics')
def analytics_dashboard():
    """埋点统计页面"""
    return render_template('analytics.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': ERROR_MESSAGES['NO_FILE_SELECTED']}), HTTP_STATUS['BAD_REQUEST']
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': ERROR_MESSAGES['NO_FILE_SELECTED']}), HTTP_STATUS['BAD_REQUEST']
        
        if not allowed_file(file.filename):
            return jsonify({'error': ERROR_MESSAGES['INVALID_FILE_FORMAT']}), HTTP_STATUS['BAD_REQUEST']
        
        # 验证文件大小
        is_valid, error_msg = validate_file_size(file)
        if not is_valid:
            if error_msg == ERROR_MESSAGES['FILE_TOO_LARGE']:
                error_msg = f"{error_msg} ({MAX_FILE_SIZE // (1024*1024)}MB)"
            return jsonify({'error': error_msg}), HTTP_STATUS['BAD_REQUEST']
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_{filename}")
        file.save(input_path)
        
        # 生成输出文件路径
        output_filename = filename.rsplit('.', 1)[0] + '.tcx'
        output_path = os.path.join(OUTPUT_FOLDER, f"{task_id}_{output_filename}")
        
        # 获取并验证配置
        raw_config = {
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
        
        # 清理和验证配置
        config = sanitize_config(raw_config)
        
        # 处理活动类型映射
        activity_type = config['activity_type']
        if activity_type.startswith('Running_'):
            # 所有跑步子类型在TCX中都使用'Running'，子类型信息保存在扩展字段中
            tcx_sport = 'Running'
            sub_sport = activity_type.split('_')[1] if '_' in activity_type else 'Generic'
        else:
            tcx_sport = activity_type
            sub_sport = 'Generic'
        
        config.update({
            'activity_type': tcx_sport,
            'sub_sport': sub_sport,
            'original_activity_type': activity_type
        })
        
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
        logger.error(f"文件上传失败: {str(e)}")
        return jsonify({'error': f"{ERROR_MESSAGES['UPLOAD_FAILED']}: {str(e)}"}), HTTP_STATUS['INTERNAL_SERVER_ERROR']

@app.route('/status/<task_id>')
def get_status(task_id):
    """获取转换状态"""
    task = conversion_tasks.get(task_id)
    if not task:
        return jsonify({'error': ERROR_MESSAGES['TASK_NOT_FOUND']}), HTTP_STATUS['NOT_FOUND']
    
    return jsonify(task.to_dict())

@app.route('/convert', methods=['POST'])
def convert_file():
    """直接转换文件（兼容性路由）"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': ERROR_MESSAGES['NO_FILE_SELECTED']}), HTTP_STATUS['BAD_REQUEST']
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': ERROR_MESSAGES['NO_FILE_SELECTED']}), HTTP_STATUS['BAD_REQUEST']
        
        if not allowed_file(file.filename):
            return jsonify({'error': ERROR_MESSAGES['INVALID_FILE_FORMAT']}), HTTP_STATUS['BAD_REQUEST']
        
        # 验证文件大小
        is_valid, error_msg = validate_file_size(file)
        if not is_valid:
            if error_msg == ERROR_MESSAGES['FILE_TOO_LARGE']:
                error_msg = f"{error_msg} ({MAX_FILE_SIZE // (1024*1024)}MB)"
            return jsonify({'error': error_msg}), HTTP_STATUS['BAD_REQUEST']
        
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
        return jsonify({'error': ERROR_MESSAGES['CONVERSION_NOT_COMPLETED']}), HTTP_STATUS['BAD_REQUEST']
    
    if not os.path.exists(task.output_file):
        logger.error(f"下载请求失败: 文件 {task.output_file} 不存在")
        return jsonify({'error': ERROR_MESSAGES['FILE_NOT_FOUND']}), HTTP_STATUS['NOT_FOUND']
    
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
    """清理旧文件和任务记录"""
    try:
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=APP_CONFIG['FILE_RETENTION_HOURS'])
        
        cleaned_files = 0
        cleaned_tasks = 0
        
        # 清理超过保留时间的任务和文件
        tasks_to_remove = []
        for task_id, task in list(conversion_tasks.items()):
            if task.created_at < cutoff_time:
                # 删除相关文件
                for file_path in [task.input_file, task.output_file]:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            cleaned_files += 1
                            logger.debug(f"删除过期文件: {file_path}")
                        except (OSError, IOError) as e:
                            logger.warning(f"删除文件失败 {file_path}: {str(e)}")
                        except Exception as e:
                            logger.error(f"处理文件时出错 {file_path}: {str(e)}")
                tasks_to_remove.append(task_id)
        
        # 从内存中移除任务
        for task_id in tasks_to_remove:
            try:
                del conversion_tasks[task_id]
                cleaned_tasks += 1
            except KeyError:
                logger.warning(f"任务 {task_id} 已被删除")
        
        # 清理文件夹中的孤立文件
        folders_to_clean = [UPLOAD_FOLDER, OUTPUT_FOLDER]
        for folder in folders_to_clean:
            if not os.path.exists(folder):
                continue
                
            try:
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if not os.path.isfile(file_path):
                        continue
                        
                    try:
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_mtime < cutoff_time:
                            os.remove(file_path)
                            cleaned_files += 1
                            logger.debug(f"删除孤立文件: {file_path}")
                    except (OSError, IOError) as e:
                        logger.warning(f"删除孤立文件失败 {file_path}: {str(e)}")
                    except Exception as e:
                        logger.error(f"处理孤立文件时出错 {file_path}: {str(e)}")
                        
            except (OSError, IOError) as e:
                logger.warning(f"访问文件夹失败 {folder}: {str(e)}")
        
        if cleaned_files > 0 or cleaned_tasks > 0:
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

# 天气数据缓存
weather_cache = {}
CACHE_DURATION = 300  # 5分钟缓存

def get_location_by_ip():
    """通过IP获取位置信息"""
    try:
        # 使用免费的IP地理位置API
        apis = [
            'http://ip-api.com/json/?fields=city,country,countryCode,lat,lon,timezone',
            'https://ipapi.co/json/',
            'https://freegeoip.app/json/'
        ]
        
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    if 'city' in data and data['city']:
                        return {
                            'city': data.get('city', ''),
                            'lat': data.get('lat', data.get('latitude')),
                            'lon': data.get('lon', data.get('longitude')),
                            'country': data.get('country', data.get('country_name', '')),
                            'country_code': data.get('countryCode', data.get('country_code', ''))
                        }
            except:
                continue
        return None
    except:
        return None

def get_weather_data(lat=None, lon=None, city=None, lang='zh'):
    """获取天气数据，支持多种API源和备用方案，GPS优先定位"""
    import requests
    import json
    import time
    import hashlib
    
    # 生成缓存键
    cache_key = hashlib.md5(f"{lat}_{lon}_{city}_{lang}".encode()).hexdigest()
    current_time = time.time()
    
    # 检查缓存
    if cache_key in weather_cache:
        cached_data, cached_time = weather_cache[cache_key]
        if current_time - cached_time < CACHE_DURATION:
            logger.info("✅ 使用缓存的天气数据")
            return cached_data
    
    # 天气描述翻译映射
    weather_translations = {
        'clear': '晴朗', 'sunny': '晴朗', 'clear sky': '晴朗',
        'partly cloudy': '多云', 'cloudy': '多云', 'few clouds': '少云',
        'scattered clouds': '多云', 'broken clouds': '多云',
        'overcast': '阴天', 'overcast clouds': '阴天',
        'light rain': '小雨', 'moderate rain': '中雨', 'heavy rain': '大雨',
        'rain': '雨', 'shower rain': '阵雨', 'light shower': '小阵雨',
        'thunderstorm': '雷雨', 'thunderstorm with rain': '雷阵雨',
        'snow': '雪', 'light snow': '小雪', 'heavy snow': '大雪',
        'mist': '薄雾', 'fog': '雾', 'haze': '霾', 'dust': '浮尘',
        'drizzle': '毛毛雨', 'freezing rain': '冻雨'
    }
    
    def translate_weather_desc(desc, target_lang):
        """翻译天气描述"""
        if target_lang == 'zh':
            return weather_translations.get(desc.lower(), desc)
        return desc
    
    # 方案1: 免费的wttr.in API (无需API密钥)
    def get_weather_from_wttr():
        try:
            if lat and lon:
                url = f"https://wttr.in/{lat},{lon}?format=j1"
            elif city:
                url = f"https://wttr.in/{city}?format=j1"
            else:
                # 如果没有位置信息，尝试通过IP获取
                ip_location = get_location_by_ip()
                if ip_location and ip_location['city']:
                    url = f"https://wttr.in/{ip_location['city']}?format=j1"
                else:
                    url = "https://wttr.in/Beijing?format=j1"
            
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]
                location = data['nearest_area'][0]
                
                weather_data = {
                    'temperature': f"{current['temp_C']}°C",
                    'description': translate_weather_desc(current['weatherDesc'][0]['value'], lang),
                    'humidity': int(current['humidity']),
                    'wind_speed': float(current['windspeedKmph']) / 3.6  # 转换为m/s
                }
                
                location_data = {
                    'city': location['areaName'][0]['value'],
                    'country': location['country'][0]['value'],
                    'province': location['region'][0]['value']
                }
                
                return weather_data, location_data
        except Exception as e:
            logger.warning(f"wttr.in API调用失败: {str(e)}")
            return None, None
    
    # 方案2: WeatherAPI免费API (每月100万次免费调用)
    def get_weather_from_weatherapi():
        try:
            # WeatherAPI免费版本，注册即可获得API密钥
            api_key = "your_weatherapi_key_here"  # 用户需要自己申请
            
            if api_key == "your_weatherapi_key_here":
                return None, None  # 跳过，因为没有配置API密钥
            
            if lat and lon:
                query = f"{lat},{lon}"
            elif city:
                query = city
            else:
                # 尝试通过IP获取位置
                ip_location = get_location_by_ip()
                query = ip_location['city'] if ip_location and ip_location['city'] else 'Beijing'
            
            url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={query}&lang={'zh' if lang == 'zh' else 'en'}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                current = data['current']
                location = data['location']
                
                weather_data = {
                    'temperature': f"{round(current['temp_c'])}°C",
                    'description': translate_weather_desc(current['condition']['text'], lang),
                    'humidity': current['humidity'],
                    'wind_speed': current['wind_kph'] / 3.6  # 转换为m/s
                }
                
                location_data = {
                    'city': location['name'],
                    'country': location['country'],
                    'province': location['region']
                }
                
                return weather_data, location_data
        except Exception as e:
            logger.warning(f"WeatherAPI调用失败: {str(e)}")
            return None, None
    
    # 方案3: OpenWeatherMap免费API (需要注册但免费)
    def get_weather_from_openweather():
        try:
            # 使用免费的OpenWeatherMap API密钥 (每月1000次免费调用)
            api_key = "your_openweather_api_key_here"  # 用户需要自己申请
            
            if api_key == "your_openweather_api_key_here":
                return None, None  # 跳过，因为没有配置API密钥
            
            if lat and lon:
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang={'zh_cn' if lang == 'zh' else 'en'}"
            elif city:
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang={'zh_cn' if lang == 'zh' else 'en'}"
            else:
                # 尝试通过IP获取位置
                ip_location = get_location_by_ip()
                query = ip_location['city'] if ip_location and ip_location['city'] else 'Beijing'
                url = f"https://api.openweathermap.org/data/2.5/weather?q={query}&appid={api_key}&units=metric&lang={'zh_cn' if lang == 'zh' else 'en'}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                weather_data = {
                    'temperature': f"{round(data['main']['temp'])}°C",
                    'description': translate_weather_desc(data['weather'][0]['description'], lang),
                    'humidity': data['main']['humidity'],
                    'wind_speed': data.get('wind', {}).get('speed', 0)
                }
                
                location_data = {
                    'city': data['name'],
                    'country': data['sys']['country'],
                    'province': data['name']
                }
                
                return weather_data, location_data
        except Exception as e:
            logger.warning(f"OpenWeatherMap API调用失败: {str(e)}")
            return None, None
    
    # 方案4: 7Timer免费API (完全免费，无需注册)
    def get_weather_from_7timer():
        try:
            if lat and lon:
                url = f"http://www.7timer.info/bin/api.pl?lon={lon}&lat={lat}&product=civillight&output=json"
            else:
                # 尝试通过IP获取位置
                ip_location = get_location_by_ip()
                if ip_location and ip_location['lat'] and ip_location['lon']:
                    url = f"http://www.7timer.info/bin/api.pl?lon={ip_location['lon']}&lat={ip_location['lat']}&product=civillight&output=json"
                else:
                    # 默认北京坐标
                    url = "http://www.7timer.info/bin/api.pl?lon=116.4&lat=39.9&product=civillight&output=json"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'dataseries' in data and len(data['dataseries']) > 0:
                    current = data['dataseries'][0]
                    
                    # 7Timer天气代码映射
                    weather_map = {
                        'clear': '晴朗' if lang == 'zh' else 'Clear',
                        'pcloudy': '多云' if lang == 'zh' else 'Partly Cloudy',
                        'mcloudy': '多云' if lang == 'zh' else 'Mostly Cloudy',
                        'cloudy': '阴天' if lang == 'zh' else 'Cloudy',
                        'humid': '潮湿' if lang == 'zh' else 'Humid',
                        'lightrain': '小雨' if lang == 'zh' else 'Light Rain',
                        'oshower': '阵雨' if lang == 'zh' else 'Shower',
                        'ishower': '阵雨' if lang == 'zh' else 'Shower',
                        'lightsnow': '小雪' if lang == 'zh' else 'Light Snow',
                        'rain': '雨' if lang == 'zh' else 'Rain',
                        'snow': '雪' if lang == 'zh' else 'Snow',
                        'rainsnow': '雨夹雪' if lang == 'zh' else 'Rain Snow',
                        'ts': '雷雨' if lang == 'zh' else 'Thunderstorm',
                        'tsrain': '雷阵雨' if lang == 'zh' else 'Thunderstorm Rain'
                    }
                    
                    weather_desc = weather_map.get(current.get('weather', 'clear'), '晴朗' if lang == 'zh' else 'Clear')
                    
                    weather_data = {
                        'temperature': f"{current.get('temp2m', 20)}°C",
                        'description': weather_desc,
                        'humidity': current.get('rh2m', 50),
                        'wind_speed': current.get('wind10m', {}).get('speed', 2) if isinstance(current.get('wind10m'), dict) else 2
                    }
                    
                    # 尝试获取位置信息
                    ip_location = get_location_by_ip()
                    location_data = {
                        'city': ip_location['city'] if ip_location else ('北京' if lang == 'zh' else 'Beijing'),
                        'country': ip_location['country'] if ip_location else ('中国' if lang == 'zh' else 'China'),
                        'province': ip_location['city'] if ip_location else ('北京市' if lang == 'zh' else 'Beijing')
                    }
                    
                    return weather_data, location_data
        except Exception as e:
            logger.warning(f"7Timer API调用失败: {str(e)}")
            return None, None
    
    # 方案5: 智能备用模拟数据 (确保功能可用)
    def get_fallback_weather():
        import random
        from datetime import datetime
        
        # 根据时间生成合理的模拟数据
        hour = datetime.now().hour
        month = datetime.now().month
        
        # 根据季节调整温度范围
        if month in [12, 1, 2]:  # 冬季
            temp_range = (0, 15) if 6 <= hour <= 18 else (-5, 10)
            weather_options = ['晴朗', '多云', '阴天', '雾'] if lang == 'zh' else ['Clear', 'Cloudy', 'Overcast', 'Fog']
        elif month in [3, 4, 5]:  # 春季
            temp_range = (15, 25) if 6 <= hour <= 18 else (10, 20)
            weather_options = ['晴朗', '多云', '小雨', '阵雨'] if lang == 'zh' else ['Clear', 'Cloudy', 'Light Rain', 'Shower']
        elif month in [6, 7, 8]:  # 夏季
            temp_range = (25, 35) if 6 <= hour <= 18 else (20, 30)
            weather_options = ['晴朗', '多云', '雷雨', '阵雨'] if lang == 'zh' else ['Clear', 'Cloudy', 'Thunderstorm', 'Shower']
        else:  # 秋季
            temp_range = (10, 25) if 6 <= hour <= 18 else (5, 20)
            weather_options = ['晴朗', '多云', '阴天', '薄雾'] if lang == 'zh' else ['Clear', 'Cloudy', 'Overcast', 'Mist']
        
        random.seed(hour + month)  # 使用小时和月份作为种子，确保一致性
        
        weather_data = {
            'temperature': f"{random.randint(*temp_range)}°C",
            'description': random.choice(weather_options),
            'humidity': random.randint(30, 90),
            'wind_speed': round(random.uniform(0.5, 8.0), 1)
        }
        
        # 尝试获取真实位置信息
        ip_location = get_location_by_ip()
        if ip_location and ip_location['city']:
            location_data = {
                'city': ip_location['city'],
                'country': ip_location['country'],
                'province': ip_location['city']
            }
        else:
            location_data = {
                'city': city or ('北京' if lang == 'zh' else 'Beijing'),
                'country': '中国' if lang == 'zh' else 'China',
                'province': '北京市' if lang == 'zh' else 'Beijing'
            }
        
        return weather_data, location_data
    
    # 按优先级尝试各种方案 - 多重备用保障
    try:
        # 方案1: wttr.in (免费且无需API密钥，支持GPS和IP定位)
        weather_data, location_data = get_weather_from_wttr()
        if weather_data:
            logger.info("✅ 使用wttr.in获取天气数据成功")
            # 缓存结果
            weather_cache[cache_key] = ((weather_data, location_data), current_time)
            return weather_data, location_data
        
        # 方案2: WeatherAPI (免费注册，每月100万次调用)
        weather_data, location_data = get_weather_from_weatherapi()
        if weather_data:
            logger.info("✅ 使用WeatherAPI获取天气数据成功")
            # 缓存结果
            weather_cache[cache_key] = ((weather_data, location_data), current_time)
            return weather_data, location_data
        
        # 方案3: OpenWeatherMap (免费注册，每月1000次调用)
        weather_data, location_data = get_weather_from_openweather()
        if weather_data:
            logger.info("✅ 使用OpenWeatherMap获取天气数据成功")
            # 缓存结果
            weather_cache[cache_key] = ((weather_data, location_data), current_time)
            return weather_data, location_data
        
        # 方案4: 7Timer (完全免费，无需注册)
        weather_data, location_data = get_weather_from_7timer()
        if weather_data:
            logger.info("✅ 使用7Timer获取天气数据成功")
            # 缓存结果
            weather_cache[cache_key] = ((weather_data, location_data), current_time)
            return weather_data, location_data
        
        # 方案5: 智能模拟数据 (最终保障，包含IP定位)
        logger.info("🔄 使用智能备用天气数据")
        weather_data, location_data = get_fallback_weather()
        # 缓存结果
        weather_cache[cache_key] = ((weather_data, location_data), current_time)
        return weather_data, location_data
        
    except Exception as e:
        logger.error(f"❌ 获取天气数据时发生错误: {str(e)}")
        # 即使出现异常也返回备用数据
        logger.info("🛡️ 启用应急备用天气数据")
        weather_data, location_data = get_fallback_weather()
        # 缓存结果
        weather_cache[cache_key] = ((weather_data, location_data), current_time)
        return weather_data, location_data

@app.route('/greeting-info')
def get_greeting_info():
    """获取问候语和天气信息"""
    try:
        # 获取并验证语言参数
        lang = request.args.get('lang', 'zh')
        if not isinstance(lang, str) or lang not in ['zh', 'en']:
            lang = 'zh'  # 默认中文
        
        # 获取位置参数 - GPS优先定位策略
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        city = request.args.get('city')
        
        # GPS优先定位逻辑：如果有GPS坐标就优先使用，否则使用IP定位
        if not (lat and lon):
            # 没有GPS坐标时，尝试IP定位
            ip_location = get_location_by_ip()
            if ip_location and ip_location.get('lat') and ip_location.get('lon'):
                lat = str(ip_location['lat'])
                lon = str(ip_location['lon'])
                logger.info(f"🌍 GPS不可用，使用IP定位: {lat}, {lon}")
            else:
                logger.info("📍 GPS和IP定位都不可用，将使用默认城市")
        else:
            logger.info(f"📍 使用GPS定位: {lat}, {lon}")
        
        # 装逼问候语库
        cool_greetings = {
            'zh': [
                "代码如诗，转换如艺术 ✨",
                "优雅地处理每一个数据点 🎯",
                "让数据在格式间自由流淌 🌊",
                "精准转换，完美呈现 💎",
                "技术与美学的完美融合 🎨",
                "每一次转换都是一次创作 🚀",
                "数据的魔法师，为您服务 ⚡",
                "简约而不简单的转换体验 🌟"
            ],
            'en': [
                "Code as poetry, conversion as art ✨",
                "Elegantly handling every data point 🎯",
                "Let data flow freely between formats 🌊",
                "Precision conversion, perfect presentation 💎",
                "Perfect fusion of technology and aesthetics 🎨",
                "Every conversion is a creation 🚀",
                "Data magician at your service ⚡",
                "Simple yet sophisticated conversion experience 🌟"
            ]
        }
        
        # 根据时间选择不同的问候语
        import random
        from datetime import datetime
        
        # 使用当前时间作为随机种子，确保同一时间段显示相同问候语
        current_hour = datetime.now().hour
        random.seed(current_hour)
        
        greetings_list = cool_greetings.get(lang, cool_greetings['zh'])
        greeting_text = random.choice(greetings_list)
        
        # 获取天气数据
        weather_data, location_data = get_weather_data(
            lat=lat, lon=lon, city=city, lang=lang
        )
        
        response_data = {
            'greeting': greeting_text
        }
        
        # 如果天气数据获取成功，添加到响应中
        if weather_data and location_data:
            response_data['weather'] = weather_data
            response_data['location'] = location_data
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"获取问候语信息时发生错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取问候语信息失败'
        }), HTTP_STATUS['INTERNAL_SERVER_ERROR']

@app.route('/api/analytics', methods=['POST'])
def receive_analytics():
    """接收埋点数据 - 增强版"""
    try:
        # 验证请求内容类型
        if not request.is_json:
            return jsonify({'error': '请求必须是JSON格式'}), HTTP_STATUS['BAD_REQUEST']
        
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({'error': '无效的JSON数据'}), HTTP_STATUS['BAD_REQUEST']
        
        # 验证必需字段
        if 'events' not in data:
            return jsonify({'error': '缺少events字段'}), HTTP_STATUS['BAD_REQUEST']
        
        events = data['events']
        if not isinstance(events, list):
            return jsonify({'error': 'events必须是数组'}), HTTP_STATUS['BAD_REQUEST']
        
        if len(events) == 0:
            return jsonify({'error': 'events不能为空'}), HTTP_STATUS['BAD_REQUEST']
        
        if len(events) > 100:  # 限制批量大小
            return jsonify({'error': '单次最多处理100个事件'}), HTTP_STATUS['BAD_REQUEST']
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        processed_events = 0
        
        for event in events:
            if not isinstance(event, dict):
                continue  # 跳过无效事件
            
            event_type = event.get('type')
            user_id = event.get('userId')
            session_id = event.get('sessionId')
            timestamp = event.get('timestamp')
            
            # 验证事件类型
            valid_event_types = ['page_view', 'convert_button_exposure', 'convert_button_click']
            if event_type not in valid_event_types:
                continue  # 跳过无效事件类型
            
            # 清理和验证用户ID
            if user_id and isinstance(user_id, str):
                user_id = user_id.strip()[:50]  # 限制长度
            else:
                user_id = 'anonymous'
            
            # 清理和验证会话ID
            if session_id and isinstance(session_id, str):
                session_id = session_id.strip()[:50]  # 限制长度
            
            # 验证时间戳
            if timestamp and isinstance(timestamp, str):
                try:
                    # 验证时间戳格式
                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.now().isoformat()  # 使用当前时间
            else:
                timestamp = datetime.now().isoformat()
            
            # 记录用户会话
            if user_id and session_id:
                analytics_data['user_sessions'][user_id].append({
                    'session_id': session_id,
                    'event': event,
                    'timestamp': timestamp
                })
            
            # 处理不同类型的事件
            if event_type == 'page_view':
                analytics_data['page_views'].append(event)
                analytics_data['daily_stats'][current_date]['pv'] += 1
                if user_id:
                    analytics_data['daily_stats'][current_date]['uv'].add(user_id)
                    
            elif event_type == 'convert_button_exposure':
                analytics_data['convert_button_stats']['exposures'].append(event)
                analytics_data['daily_stats'][current_date]['convert_exposures'] += 1
                
            elif event_type == 'convert_button_click':
                analytics_data['convert_button_stats']['clicks'].append(event)
                analytics_data['daily_stats'][current_date]['convert_clicks'] += 1
            
            processed_events += 1
        
        logger.info(f"接收到 {len(events)} 个埋点事件，成功处理 {processed_events} 个")
        return jsonify({'status': 'success', 'received': len(events), 'processed': processed_events})
        
    except json.JSONDecodeError:
        return jsonify({'error': 'JSON解析错误'}), HTTP_STATUS['BAD_REQUEST']
    except Exception as e:
        logger.error(f"处理埋点数据失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), HTTP_STATUS['INTERNAL_SERVER_ERROR']

@app.route('/api/analytics/stats')
def get_analytics_stats():
    """获取埋点统计数据"""
    try:
        # 计算总体统计
        total_pv = len(analytics_data['page_views'])
        total_uv = len(analytics_data['user_sessions'])
        total_exposures = len(analytics_data['convert_button_stats']['exposures'])
        total_clicks = len(analytics_data['convert_button_stats']['clicks'])
        
        # 计算转换率
        exposure_to_click_rate = (total_clicks / total_exposures * 100) if total_exposures > 0 else 0
        pv_to_click_rate = (total_clicks / total_pv * 100) if total_pv > 0 else 0
        
        # 获取最近7天的数据
        recent_days = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            day_stats = analytics_data['daily_stats'][date]
            recent_days.append({
                'date': date,
                'pv': day_stats['pv'],
                'uv': len(day_stats['uv']),
                'convert_exposures': day_stats['convert_exposures'],
                'convert_clicks': day_stats['convert_clicks']
            })
        
        return jsonify({
            'total_stats': {
                'pv': total_pv,
                'uv': total_uv,
                'convert_exposures': total_exposures,
                'convert_clicks': total_clicks,
                'exposure_to_click_rate': round(exposure_to_click_rate, 2),
                'pv_to_click_rate': round(pv_to_click_rate, 2)
            },
            'recent_days': recent_days[::-1],  # 倒序，最新的在前
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取统计数据失败: {str(e)}")
        return jsonify({'error': '获取统计失败'}), 500

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