#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集状态监控API
提供采集状态和性能监控接口
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime

from services.collection_frequency_service import collection_frequency_service
from services.collection_scheduler import collection_scheduler
from models.collection_config import CollectionStatus

logger = logging.getLogger(__name__)

# 创建蓝图
collection_status_bp = Blueprint('collection_status', __name__, url_prefix='/api/collection')

@collection_status_bp.route('/status', methods=['GET'])
def get_collection_status():
    """获取实时采集状态"""
    try:
        # 获取调度器状态
        scheduler_status = collection_scheduler.get_status()
        
        return jsonify({
            'success': True,
            'data': scheduler_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取采集状态失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取状态失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_status_bp.route('/performance', methods=['GET'])
def get_performance_metrics():
    """获取性能指标"""
    try:
        # 获取性能指标
        metrics = collection_frequency_service.get_performance_metrics()
        
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取性能指标失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_status_bp.route('/status/history', methods=['GET'])
def get_status_history():
    """获取状态历史记录"""
    try:
        # 获取查询参数
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # 限制参数范围
        hours = min(max(hours, 1), 168)  # 1小时到7天
        limit = min(max(limit, 1), 1000)  # 1到1000条记录
        
        # 获取状态历史
        history = CollectionStatus.get_status_history(hours, limit)
        history_data = [status.to_api_dict() for status in history]
        
        return jsonify({
            'success': True,
            'data': history_data,
            'count': len(history_data),
            'parameters': {
                'hours': hours,
                'limit': limit
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取状态历史失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取状态历史失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_status_bp.route('/scheduler/start', methods=['POST'])
def start_collection_scheduler():
    """启动采集调度器"""
    try:
        result = collection_scheduler.start_collection()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'status': result['status'],
                'config': result.get('config'),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': '启动失败',
                'message': result['message'],
                'status': result['status'],
                'timestamp': datetime.now().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"启动采集调度器失败: {e}")
        return jsonify({
            'success': False,
            'error': '启动失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_status_bp.route('/scheduler/stop', methods=['POST'])
def stop_collection_scheduler():
    """停止采集调度器"""
    try:
        result = collection_scheduler.stop_collection()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'status': result['status'],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': '停止失败',
                'message': result['message'],
                'status': result['status'],
                'timestamp': datetime.now().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"停止采集调度器失败: {e}")
        return jsonify({
            'success': False,
            'error': '停止失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_status_bp.route('/scheduler/intervals', methods=['PUT'])
def update_collection_intervals():
    """更新采集间隔"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空',
                'message': '请提供有效的JSON数据',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        sensor_interval = data.get('sensorInterval')
        rfid_interval = data.get('rfidInterval')
        
        if sensor_interval is None and rfid_interval is None:
            return jsonify({
                'success': False,
                'error': '缺少参数',
                'message': '请提供sensorInterval或rfidInterval参数',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 更新间隔
        result = collection_scheduler.update_intervals(sensor_interval, rfid_interval)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'status': result['status'],
                'config': result.get('config'),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': '更新失败',
                'message': result['message'],
                'status': result['status'],
                'timestamp': datetime.now().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"更新采集间隔失败: {e}")
        return jsonify({
            'success': False,
            'error': '更新失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_status_bp.route('/test/sensor', methods=['POST'])
def test_sensor_collection():
    """测试传感器数据采集"""
    try:
        result = collection_scheduler.force_collect_sensor_data()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'timestamp': result['timestamp']
            })
        else:
            return jsonify({
                'success': False,
                'error': '测试失败',
                'message': result['message'],
                'timestamp': result['timestamp']
            }), 400
            
    except Exception as e:
        logger.error(f"测试传感器采集失败: {e}")
        return jsonify({
            'success': False,
            'error': '测试失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_status_bp.route('/test/rfid', methods=['POST'])
def test_rfid_scanning():
    """测试RFID设备扫描"""
    try:
        result = collection_scheduler.force_scan_rfid_devices()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'timestamp': result['timestamp']
            })
        else:
            return jsonify({
                'success': False,
                'error': '测试失败',
                'message': result['message'],
                'timestamp': result['timestamp']
            }), 400
            
    except Exception as e:
        logger.error(f"测试RFID扫描失败: {e}")
        return jsonify({
            'success': False,
            'error': '测试失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_status_bp.route('/statistics', methods=['GET'])
def get_collection_statistics():
    """获取采集统计信息"""
    try:
        # 获取调度器状态（包含统计信息）
        status = collection_scheduler.get_status()
        statistics = status.get('statistics', {})
        
        return jsonify({
            'success': True,
            'data': statistics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取采集统计失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取统计失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# 错误处理
@collection_status_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': '请求错误',
        'message': '请求参数有误',
        'timestamp': datetime.now().isoformat()
    }), 400

@collection_status_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在',
        'message': '请求的接口不存在',
        'timestamp': datetime.now().isoformat()
    }), 404

@collection_status_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"状态监控API内部错误: {error}")
    return jsonify({
        'success': False,
        'error': '内部服务器错误',
        'message': '服务器处理请求时发生错误',
        'timestamp': datetime.now().isoformat()
    }), 500