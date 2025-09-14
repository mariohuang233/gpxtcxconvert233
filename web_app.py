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

@app.route('/ip-info')
def get_ip_info():
    """获取用户IP地址信息"""
    try:
        # 获取用户真实IP地址
        if request.headers.get('X-Forwarded-For'):
            user_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            user_ip = request.headers.get('X-Real-IP')
        else:
            user_ip = request.remote_addr
        
        # 如果是本地IP，使用一个示例IP进行演示
        if user_ip in ['127.0.0.1', '::1', 'localhost']:
            user_ip = '8.8.8.8'  # 使用Google DNS作为示例
        
        # 调用ipstack API
        api_key = 'a67f3911868f6c642b949296b6f6ef6a'
        api_url = f'http://api.ipstack.com/{user_ip}?access_key={api_key}'
        
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            ip_data = response.json()
            
            # 检查API响应是否有错误
            if 'error' in ip_data:
                return jsonify({
                    'success': False,
                    'error': ip_data['error']['info']
                })
            
            return jsonify({
                'success': True,
                'ip': user_ip,
                'data': {
                    'country': ip_data.get('country_name', 'Unknown'),
                    'country_code': ip_data.get('country_code', 'Unknown'),
                    'region': ip_data.get('region_name', 'Unknown'),
                    'city': ip_data.get('city', 'Unknown'),
                    'latitude': ip_data.get('latitude', 0),
                    'longitude': ip_data.get('longitude', 0),
                    'timezone': ip_data.get('time_zone', {}).get('id', 'Unknown'),
                    'isp': ip_data.get('connection', {}).get('isp', 'Unknown'),
                    'continent': ip_data.get('continent_name', 'Unknown')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'API请求失败: {response.status_code}'
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
    # 确保必要的目录存在
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    print("🌐 GPX转TCX Web应用启动中...")
    print("📁 本地访问: http://localhost:8080")
    print("🌍 网络访问: http://你的IP地址:8080")
    print("🔧 支持功能: 文件上传、实时转换、配置自定义")
    print("👥 同事可通过网络地址访问此应用")
    print("⚠️  仅用于测试场景，不能作为比赛作弊用途")

    app.run(debug=True, host='0.0.0.0', port=8080)