#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统性能监控API接口
提供系统性能数据的REST API服务
"""

import logging
import psutil
import time
from datetime import datetime
from flask import Blueprint, jsonify
from database import get_db_connection

logger = logging.getLogger(__name__)

# 创建蓝图
system_performance_bp = Blueprint('system_performance', __name__, url_prefix='/api/system')

def handle_api_error(func):
    """API错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"系统性能API错误: {e}")
            return jsonify({'error': '服务器内部错误', 'code': 500}), 500
    wrapper.__name__ = func.__name__
    return wrapper

@system_performance_bp.route('/performance', methods=['GET'])
@handle_api_error
def get_system_performance():
    """获取系统性能数据"""
    try:
        # CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        memory_total = round(memory.total / (1024**3), 2)  # GB
        memory_used = round(memory.used / (1024**3), 2)    # GB
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_usage = round((disk.used / disk.total) * 100, 1)
        disk_total = round(disk.total / (1024**3), 2)      # GB
        disk_used = round(disk.used / (1024**3), 2)        # GB
        
        # 网络状态
        network_io = psutil.net_io_counters()
        network_connections = len(psutil.net_connections())
        
        # 进程信息
        process_count = len(psutil.pids())
        
        # 系统负载（Windows上使用CPU使用率作为替代）
        try:
            load_average = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else cpu_usage / 100
        except:
            load_average = cpu_usage / 100
        
        # 数据库连接状态
        try:
            conn = get_db_connection()
            conn.close()
            db_connections = 1  # 简化的连接数统计
            db_status = "connected"
        except:
            db_connections = 0
            db_status = "disconnected"
        
        performance_data = {
            'cpu_usage': round(cpu_usage, 1),
            'memory_usage': round(memory_usage, 1),
            'memory_total': memory_total,
            'memory_used': memory_used,
            'disk_usage': disk_usage,
            'disk_total': disk_total,
            'disk_used': disk_used,
            'network_connections': network_connections,
            'network_rx_bytes': network_io.bytes_recv,
            'network_tx_bytes': network_io.bytes_sent,
            'process_count': process_count,
            'load_average': round(load_average, 2),
            'db_connections': db_connections,
            'db_status': db_status,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': performance_data
        })
        
    except Exception as e:
        logger.error(f"获取系统性能数据失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取性能数据失败',
            'data': {
                'cpu_usage': 0,
                'memory_usage': 0,
                'memory_total': 0,
                'memory_used': 0,
                'disk_usage': 0,
                'disk_total': 0,
                'disk_used': 0,
                'network_connections': 0,
                'network_rx_bytes': 0,
                'network_tx_bytes': 0,
                'process_count': 0,
                'load_average': 0,
                'db_connections': 0,
                'db_status': 'unknown',
                'timestamp': datetime.now().isoformat()
            }
        })

@system_performance_bp.route('/performance/history', methods=['GET'])
@handle_api_error
def get_performance_history():
    """获取性能历史数据（简化版本）"""
    # 这里可以实现性能数据的历史记录功能
    # 目前返回当前数据作为示例
    current_data = get_system_performance()
    return jsonify({
        'success': True,
        'data': [current_data.get_json()['data']],
        'count': 1
    })

# 错误处理
@system_performance_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在', 'code': 404}), 404

@system_performance_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': '请求方法不允许', 'code': 405}), 405