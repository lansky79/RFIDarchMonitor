#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集配置管理API
提供采集频率配置和控制接口
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime

from services.collection_frequency_service import collection_frequency_service
from services.collection_scheduler import collection_scheduler
from models.base import ValidationError

logger = logging.getLogger(__name__)

# 创建蓝图
collection_bp = Blueprint('collection', __name__, url_prefix='/api/collection')

@collection_bp.route('/config', methods=['GET'])
def get_collection_config():
    """获取当前采集配置"""
    try:
        config = collection_frequency_service.get_current_config()
        
        return jsonify({
            'success': True,
            'data': config,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取采集配置失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取配置失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_bp.route('/config', methods=['POST'])
def update_collection_config():
    """更新采集配置"""
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
        
        # 获取更新者信息
        updated_by = data.get('updatedBy', 'api_user')
        
        # 验证配置数据
        validation_result = collection_frequency_service.validate_config(data)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': '配置验证失败',
                'message': ', '.join(validation_result['errors']),
                'errors': validation_result['errors'],
                'warnings': validation_result['warnings'],
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 更新配置
        result = collection_frequency_service.update_config(data, updated_by)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result['config'],
                'warnings': validation_result.get('warnings', []),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': '配置更新失败',
                'message': result['message'],
                'data': result['config'],
                'timestamp': datetime.now().isoformat()
            }), 400
            
    except ValidationError as e:
        logger.warning(f"配置验证失败: {e}")
        return jsonify({
            'success': False,
            'error': '配置验证失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 400
        
    except Exception as e:
        logger.error(f"更新采集配置失败: {e}")
        return jsonify({
            'success': False,
            'error': '更新配置失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_bp.route('/control', methods=['POST'])
def control_collection():
    """控制采集的暂停和恢复"""
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
        
        # 获取操作类型
        action = data.get('action')
        if not action:
            return jsonify({
                'success': False,
                'error': '缺少操作类型',
                'message': '请指定action参数（pause或resume）',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 获取操作者信息
        updated_by = data.get('updatedBy', 'api_user')
        
        # 执行操作
        if action == 'pause':
            result = collection_frequency_service.pause_collection(updated_by)
        elif action == 'resume':
            result = collection_frequency_service.resume_collection(updated_by)
        else:
            return jsonify({
                'success': False,
                'error': '无效的操作类型',
                'message': f'不支持的操作: {action}，支持的操作: pause, resume',
                'timestamp': datetime.now().isoformat()
            }), 400
        
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
                'error': '操作失败',
                'message': result['message'],
                'status': result['status'],
                'timestamp': datetime.now().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"控制采集失败: {e}")
        return jsonify({
            'success': False,
            'error': '控制操作失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_bp.route('/config/validate', methods=['POST'])
def validate_collection_config():
    """验证采集配置"""
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
        
        # 验证配置
        validation_result = collection_frequency_service.validate_config(data)
        
        return jsonify({
            'success': True,
            'data': validation_result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"验证配置失败: {e}")
        return jsonify({
            'success': False,
            'error': '验证失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_bp.route('/config/reset', methods=['POST'])
def reset_collection_config():
    """重置为默认配置"""
    try:
        # 获取请求数据
        data = request.get_json() or {}
        updated_by = data.get('updatedBy', 'api_user')
        
        # 重置配置
        result = collection_frequency_service.reset_to_default(updated_by)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result['config'],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': '重置失败',
                'message': result['message'],
                'data': result['config'],
                'timestamp': datetime.now().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"重置配置失败: {e}")
        return jsonify({
            'success': False,
            'error': '重置失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_bp.route('/config/history', methods=['GET'])
def get_config_history():
    """获取配置变更历史"""
    try:
        # 获取查询参数
        limit = request.args.get('limit', 10, type=int)
        limit = min(max(limit, 1), 100)  # 限制在1-100之间
        
        # 获取配置历史
        history = collection_frequency_service.get_config_history(limit)
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取配置历史失败: {e}")
        return jsonify({
            'success': False,
            'error': '获取历史失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_bp.route('/config/export', methods=['GET'])
def export_collection_config():
    """导出配置"""
    try:
        config_json = collection_frequency_service.export_config()
        
        return jsonify({
            'success': True,
            'data': config_json,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        return jsonify({
            'success': False,
            'error': '导出失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@collection_bp.route('/config/import', methods=['POST'])
def import_collection_config():
    """导入配置"""
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
        
        config_json = data.get('config')
        if not config_json:
            return jsonify({
                'success': False,
                'error': '缺少配置数据',
                'message': '请提供config参数',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        updated_by = data.get('updatedBy', 'api_user')
        
        # 导入配置
        result = collection_frequency_service.import_config(config_json, updated_by)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result['config'],
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': '导入失败',
                'message': result['message'],
                'data': result['config'],
                'timestamp': datetime.now().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        return jsonify({
            'success': False,
            'error': '导入失败',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# 错误处理
@collection_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': '请求错误',
        'message': '请求参数有误',
        'timestamp': datetime.now().isoformat()
    }), 400

@collection_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在',
        'message': '请求的接口不存在',
        'timestamp': datetime.now().isoformat()
    }), 404

@collection_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"采集API内部错误: {error}")
    return jsonify({
        'success': False,
        'error': '内部服务器错误',
        'message': '服务器处理请求时发生错误',
        'timestamp': datetime.now().isoformat()
    }), 500