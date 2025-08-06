#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备维护API
提供设备维护记录的增删改查功能
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from models.maintenance import MaintenanceRecord
from models.base import ValidationError

# 创建蓝图
maintenance_bp = Blueprint('maintenance', __name__)

# 配置日志
logger = logging.getLogger(__name__)

@maintenance_bp.route('/api/maintenance/records', methods=['GET'])
def get_maintenance_records():
    """获取维护记录列表"""
    try:
        maintenance = MaintenanceRecord()
        
        # 获取查询参数
        device_type = request.args.get('device_type')
        status = request.args.get('status')
        maintenance_type = request.args.get('maintenance_type')
        keyword = request.args.get('keyword')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 搜索记录
        records = maintenance.search(
            keyword=keyword,
            device_type=device_type,
            maintenance_type=maintenance_type,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        
        # 分页处理
        total = len(records)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_records = records[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'data': {
                'records': paginated_records,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取维护记录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取维护记录失败: {str(e)}'
        }), 500

@maintenance_bp.route('/api/maintenance/records', methods=['POST'])
def create_maintenance_record():
    """创建维护记录"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 创建维护记录
        record = MaintenanceRecord.create_with_validation(**data)
        
        return jsonify({
            'success': True,
            'message': '维护记录创建成功',
            'data': record
        })
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': f'数据验证失败: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"创建维护记录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'创建维护记录失败: {str(e)}'
        }), 500

@maintenance_bp.route('/api/maintenance/records/<int:record_id>', methods=['GET'])
def get_maintenance_record(record_id):
    """获取单个维护记录"""
    try:
        maintenance = MaintenanceRecord()
        record = maintenance.find_by_id(record_id)
        
        if not record:
            return jsonify({
                'success': False,
                'message': '维护记录不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': record
        })
        
    except Exception as e:
        logger.error(f"获取维护记录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取维护记录失败: {str(e)}'
        }), 500

@maintenance_bp.route('/api/maintenance/records/<int:record_id>', methods=['PUT'])
def update_maintenance_record(record_id):
    """更新维护记录"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        maintenance = MaintenanceRecord()
        
        # 检查记录是否存在
        if not maintenance.find_by_id(record_id):
            return jsonify({
                'success': False,
                'message': '维护记录不存在'
            }), 404
        
        # 更新记录
        success = maintenance.update(record_id, **data)
        
        if success:
            updated_record = maintenance.find_by_id(record_id)
            return jsonify({
                'success': True,
                'message': '维护记录更新成功',
                'data': updated_record
            })
        else:
            return jsonify({
                'success': False,
                'message': '维护记录更新失败'
            }), 500
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': f'数据验证失败: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"更新维护记录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新维护记录失败: {str(e)}'
        }), 500

@maintenance_bp.route('/api/maintenance/records/<int:record_id>', methods=['DELETE'])
def delete_maintenance_record(record_id):
    """删除维护记录"""
    try:
        maintenance = MaintenanceRecord()
        
        # 检查记录是否存在
        if not maintenance.find_by_id(record_id):
            return jsonify({
                'success': False,
                'message': '维护记录不存在'
            }), 404
        
        # 删除记录
        success = maintenance.delete(record_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '维护记录删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '维护记录删除失败'
            }), 500
        
    except Exception as e:
        logger.error(f"删除维护记录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'删除维护记录失败: {str(e)}'
        }), 500

@maintenance_bp.route('/api/maintenance/records/<int:record_id>/status', methods=['PUT'])
def update_maintenance_status(record_id):
    """更新维护记录状态"""
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'message': '状态参数不能为空'
            }), 400
        
        maintenance = MaintenanceRecord()
        
        # 检查记录是否存在
        if not maintenance.find_by_id(record_id):
            return jsonify({
                'success': False,
                'message': '维护记录不存在'
            }), 404
        
        # 更新状态
        success = maintenance.update_status(
            record_id, 
            data['status'], 
            data.get('notes')
        )
        
        if success:
            updated_record = maintenance.find_by_id(record_id)
            return jsonify({
                'success': True,
                'message': '维护状态更新成功',
                'data': updated_record
            })
        else:
            return jsonify({
                'success': False,
                'message': '维护状态更新失败'
            }), 500
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': f'数据验证失败: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"更新维护状态失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新维护状态失败: {str(e)}'
        }), 500

@maintenance_bp.route('/api/maintenance/statistics', methods=['GET'])
def get_maintenance_statistics():
    """获取维护统计信息"""
    try:
        maintenance = MaintenanceRecord()
        
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 获取统计信息
        stats = maintenance.get_statistics(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"获取维护统计失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取维护统计失败: {str(e)}'
        }), 500

@maintenance_bp.route('/api/maintenance/overdue', methods=['GET'])
def get_overdue_maintenance():
    """获取逾期维护记录"""
    try:
        maintenance = MaintenanceRecord()
        overdue_records = maintenance.find_overdue()
        
        return jsonify({
            'success': True,
            'data': overdue_records
        })
        
    except Exception as e:
        logger.error(f"获取逾期维护记录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取逾期维护记录失败: {str(e)}'
        }), 500

@maintenance_bp.route('/api/maintenance/upcoming', methods=['GET'])
def get_upcoming_maintenance():
    """获取即将到期的维护记录"""
    try:
        maintenance = MaintenanceRecord()
        days = int(request.args.get('days', 7))
        upcoming_records = maintenance.find_upcoming(days)
        
        return jsonify({
            'success': True,
            'data': upcoming_records
        })
        
    except Exception as e:
        logger.error(f"获取即将到期维护记录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取即将到期维护记录失败: {str(e)}'
        }), 500

@maintenance_bp.route('/api/maintenance/device/<device_type>', methods=['GET'])
def get_device_maintenance(device_type):
    """获取指定设备类型的维护记录"""
    try:
        maintenance = MaintenanceRecord()
        device_id = request.args.get('device_id', type=int)
        
        records = maintenance.find_by_device(device_type, device_id)
        
        return jsonify({
            'success': True,
            'data': records
        })
        
    except Exception as e:
        logger.error(f"获取设备维护记录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取设备维护记录失败: {str(e)}'
        }), 500