#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境监测API接口
提供环境数据的REST API服务
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from models.environment import EnvironmentData
from models.base import ValidationError

logger = logging.getLogger(__name__)

# 创建蓝图
environment_bp = Blueprint('environment', __name__, url_prefix='/api/environment')

def handle_api_error(func):
    """API错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"验证错误: {e}")
            return jsonify({'error': str(e), 'code': 400}), 400
        except Exception as e:
            logger.error(f"API错误: {e}")
            return jsonify({'error': '服务器内部错误', 'code': 500}), 500
    wrapper.__name__ = func.__name__
    return wrapper

@environment_bp.route('/data', methods=['GET'])
@handle_api_error
def get_current_environment_data():
    """获取当前环境数据"""
    sensor_id = request.args.get('sensor_id')
    limit = int(request.args.get('limit', 10))
    
    # 获取最新数据
    data_list = EnvironmentData.get_latest_data(sensor_id, limit)
    
    # 转换为JSON格式
    result = [data.to_json_dict() for data in data_list]
    
    return jsonify({
        'success': True,
        'data': result,
        'count': len(result),
        'timestamp': datetime.now().isoformat()
    })

@environment_bp.route('/data/current', methods=['GET'])
@handle_api_error
def get_latest_environment_data():
    """获取最新的环境数据（单条）"""
    sensor_id = request.args.get('sensor_id')
    
    # 获取当前最新数据
    current_data = EnvironmentData.get_current_data(sensor_id)
    
    if current_data:
        return jsonify({
            'success': True,
            'data': current_data.to_json_dict(),
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'success': True,
            'data': None,
            'message': '暂无环境数据',
            'timestamp': datetime.now().isoformat()
        })

@environment_bp.route('/data', methods=['POST'])
@handle_api_error
def add_environment_data():
    """添加环境数据"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空', 'code': 400}), 400
    
    # 创建环境数据记录
    env_data = EnvironmentData.create_with_validation(**data)
    
    logger.info(f"添加环境数据成功: 传感器{env_data.sensor_id}")
    
    return jsonify({
        'success': True,
        'data': env_data.to_json_dict(),
        'message': '环境数据添加成功'
    }), 201

@environment_bp.route('/data/batch', methods=['POST'])
@handle_api_error
def add_batch_environment_data():
    """批量添加环境数据"""
    data_list = request.get_json()
    
    if not data_list or not isinstance(data_list, list):
        return jsonify({'error': '请求数据必须是数组格式', 'code': 400}), 400
    
    success_count = 0
    error_count = 0
    errors = []
    
    for i, data in enumerate(data_list):
        try:
            EnvironmentData.create_with_validation(**data)
            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append(f"第{i+1}条数据: {str(e)}")
    
    return jsonify({
        'success': True,
        'success_count': success_count,
        'error_count': error_count,
        'errors': errors,
        'total_count': len(data_list),
        'message': f'批量添加完成，成功{success_count}条，失败{error_count}条'
    }), 201

@environment_bp.route('/history', methods=['GET'])
@handle_api_error
def get_environment_history():
    """获取环境历史数据"""
    # 获取查询参数
    sensor_id = request.args.get('sensor_id')
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')
    
    # 默认查询最近24小时的数据
    if not start_time_str:
        start_time = datetime.now() - timedelta(hours=24)
    else:
        try:
            start_time = datetime.fromisoformat(start_time_str)
        except ValueError:
            return jsonify({'error': '开始时间格式不正确', 'code': 400}), 400
    
    if not end_time_str:
        end_time = datetime.now()
    else:
        try:
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            return jsonify({'error': '结束时间格式不正确', 'code': 400}), 400
    
    # 验证时间范围
    if start_time >= end_time:
        return jsonify({'error': '开始时间必须早于结束时间', 'code': 400}), 400
    
    # 获取历史数据
    history_data = EnvironmentData.get_history_data(start_time, end_time, sensor_id)
    
    # 转换为JSON格式
    result = [data.to_json_dict() for data in history_data]
    
    return jsonify({
        'success': True,
        'data': result,
        'count': len(result),
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'sensor_id': sensor_id
    })

@environment_bp.route('/statistics', methods=['GET'])
@handle_api_error
def get_environment_statistics():
    """获取环境数据统计信息"""
    # 获取查询参数
    sensor_id = request.args.get('sensor_id')
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')
    
    # 默认查询最近24小时的数据
    if not start_time_str:
        start_time = datetime.now() - timedelta(hours=24)
    else:
        try:
            start_time = datetime.fromisoformat(start_time_str)
        except ValueError:
            return jsonify({'error': '开始时间格式不正确', 'code': 400}), 400
    
    if not end_time_str:
        end_time = datetime.now()
    else:
        try:
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            return jsonify({'error': '结束时间格式不正确', 'code': 400}), 400
    
    # 获取统计数据
    statistics = EnvironmentData.get_statistics(start_time, end_time, sensor_id)
    
    return jsonify({
        'success': True,
        'data': statistics,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'sensor_id': sensor_id
    })

@environment_bp.route('/averages/hourly', methods=['GET'])
@handle_api_error
def get_hourly_averages():
    """获取按小时统计的平均值"""
    # 获取查询参数
    sensor_id = request.args.get('sensor_id')
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')
    
    # 默认查询最近7天的数据
    if not start_time_str:
        start_time = datetime.now() - timedelta(days=7)
    else:
        try:
            start_time = datetime.fromisoformat(start_time_str)
        except ValueError:
            return jsonify({'error': '开始时间格式不正确', 'code': 400}), 400
    
    if not end_time_str:
        end_time = datetime.now()
    else:
        try:
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            return jsonify({'error': '结束时间格式不正确', 'code': 400}), 400
    
    # 获取小时平均值
    hourly_data = EnvironmentData.get_hourly_averages(start_time, end_time, sensor_id)
    
    return jsonify({
        'success': True,
        'data': hourly_data,
        'count': len(hourly_data),
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'sensor_id': sensor_id
    })

@environment_bp.route('/averages/daily', methods=['GET'])
@handle_api_error
def get_daily_averages():
    """获取按天统计的平均值"""
    # 获取查询参数
    sensor_id = request.args.get('sensor_id')
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')
    
    # 默认查询最近30天的数据
    if not start_time_str:
        start_time = datetime.now() - timedelta(days=30)
    else:
        try:
            start_time = datetime.fromisoformat(start_time_str)
        except ValueError:
            return jsonify({'error': '开始时间格式不正确', 'code': 400}), 400
    
    if not end_time_str:
        end_time = datetime.now()
    else:
        try:
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            return jsonify({'error': '结束时间格式不正确', 'code': 400}), 400
    
    # 获取日平均值
    daily_data = EnvironmentData.get_daily_averages(start_time, end_time, sensor_id)
    
    return jsonify({
        'success': True,
        'data': daily_data,
        'count': len(daily_data),
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'sensor_id': sensor_id
    })

@environment_bp.route('/sensors', methods=['GET'])
@handle_api_error
def get_sensor_list():
    """获取传感器列表"""
    sensor_list = EnvironmentData.get_sensor_list()
    
    return jsonify({
        'success': True,
        'data': sensor_list,
        'count': len(sensor_list)
    })

@environment_bp.route('/thresholds', methods=['GET'])
@handle_api_error
def get_environment_thresholds():
    """获取环境阈值配置"""
    from models.base import BaseModel
    
    # 从系统配置表获取阈值设置
    config_keys = [
        'temp_min_threshold', 'temp_max_threshold',
        'humidity_min_threshold', 'humidity_max_threshold',
        'light_min_threshold', 'light_max_threshold'
    ]
    
    sql = "SELECT config_key, config_value, config_type FROM system_config WHERE config_key IN ({})".format(
        ','.join(['?' for _ in config_keys])
    )
    
    config_data = BaseModel.execute_raw_sql(sql, config_keys, fetch_one=False, fetch_all=True)
    
    # 构建阈值配置
    thresholds = {
        'temperature': {'min': 18.0, 'max': 25.0},
        'humidity': {'min': 40.0, 'max': 60.0},
        'light_intensity': {'min': 100.0, 'max': 500.0}
    }
    
    for config in config_data:
        key = config['config_key']
        value = float(config['config_value'])
        
        if key == 'temp_min_threshold':
            thresholds['temperature']['min'] = value
        elif key == 'temp_max_threshold':
            thresholds['temperature']['max'] = value
        elif key == 'humidity_min_threshold':
            thresholds['humidity']['min'] = value
        elif key == 'humidity_max_threshold':
            thresholds['humidity']['max'] = value
        elif key == 'light_min_threshold':
            thresholds['light_intensity']['min'] = value
        elif key == 'light_max_threshold':
            thresholds['light_intensity']['max'] = value
    
    return jsonify({
        'success': True,
        'data': thresholds
    })

@environment_bp.route('/thresholds', methods=['POST'])
@handle_api_error
def set_environment_thresholds():
    """设置环境阈值配置"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空', 'code': 400}), 400
    
    from models.base import BaseModel
    
    # 更新阈值配置
    config_updates = []
    
    if 'temperature' in data:
        temp_config = data['temperature']
        if 'min' in temp_config:
            config_updates.append(('temp_min_threshold', str(temp_config['min'])))
        if 'max' in temp_config:
            config_updates.append(('temp_max_threshold', str(temp_config['max'])))
    
    if 'humidity' in data:
        humidity_config = data['humidity']
        if 'min' in humidity_config:
            config_updates.append(('humidity_min_threshold', str(humidity_config['min'])))
        if 'max' in humidity_config:
            config_updates.append(('humidity_max_threshold', str(humidity_config['max'])))
    
    if 'light_intensity' in data:
        light_config = data['light_intensity']
        if 'min' in light_config:
            config_updates.append(('light_min_threshold', str(light_config['min'])))
        if 'max' in light_config:
            config_updates.append(('light_max_threshold', str(light_config['max'])))
    
    # 执行更新
    for config_key, config_value in config_updates:
        sql = """
            UPDATE system_config 
            SET config_value = ?, updated_at = ? 
            WHERE config_key = ?
        """
        BaseModel.execute_raw_sql(sql, [config_value, datetime.now().isoformat(), config_key],
                                fetch_one=False, fetch_all=False)
    
    logger.info(f"环境阈值配置更新成功，更新了{len(config_updates)}个配置项")
    
    return jsonify({
        'success': True,
        'message': '环境阈值配置更新成功',
        'updated_count': len(config_updates)
    })

@environment_bp.route('/data/cleanup', methods=['POST'])
@handle_api_error
def cleanup_old_environment_data():
    """清理旧的环境数据"""
    data = request.get_json() or {}
    days_to_keep = data.get('days_to_keep', 365)
    
    if days_to_keep < 1:
        return jsonify({'error': '保留天数必须大于0', 'code': 400}), 400
    
    # 执行清理
    deleted_count = EnvironmentData.cleanup_old_data(days_to_keep)
    
    return jsonify({
        'success': True,
        'deleted_count': deleted_count,
        'days_to_keep': days_to_keep,
        'message': f'清理完成，删除了{deleted_count}条记录'
    })

# 错误处理
@environment_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在', 'code': 404}), 404

@environment_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': '请求方法不允许', 'code': 405}), 405