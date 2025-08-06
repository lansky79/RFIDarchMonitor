#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境监测数据模型
处理传感器数据的存储和查询
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .base import BaseModel, ValidationError, validate_required_fields, validate_numeric_range

logger = logging.getLogger(__name__)

class EnvironmentData(BaseModel):
    """环境数据模型"""
    
    table_name = 'environment_data'
    
    # 字段验证规则
    REQUIRED_FIELDS = ['sensor_id']
    NUMERIC_RANGES = {
        'temperature': (-50.0, 100.0),  # 温度范围：-50°C 到 100°C
        'humidity': (0.0, 100.0),       # 湿度范围：0% 到 100%
        'light_intensity': (0.0, 100000.0)  # 光照范围：0 到 100000 lux
    }
    
    def __init__(self, **kwargs):
        """初始化环境数据"""
        # 设置默认值
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.now().isoformat()
        
        super().__init__(**kwargs)
    
    @classmethod
    def create_with_validation(cls, **kwargs) -> 'EnvironmentData':
        """创建环境数据记录（带验证）"""
        # 验证必填字段
        validate_required_fields(kwargs, cls.REQUIRED_FIELDS)
        
        # 验证数值范围
        validate_numeric_range(kwargs, cls.NUMERIC_RANGES)
        
        # 验证传感器ID格式
        if 'sensor_id' in kwargs:
            sensor_id = kwargs['sensor_id'].strip()
            if not sensor_id:
                raise ValidationError("传感器ID不能为空")
            kwargs['sensor_id'] = sensor_id
        
        return cls.create(**kwargs)
    
    @classmethod
    def get_latest_data(cls, sensor_id: str = None, limit: int = 10) -> List['EnvironmentData']:
        """获取最新的环境数据"""
        where_clause = None
        params = []
        
        if sensor_id:
            where_clause = "sensor_id = ?"
            params = [sensor_id]
        
        return cls.find_all(
            where_clause=where_clause,
            params=params,
            order_by="timestamp DESC",
            limit=limit
        )
    
    @classmethod
    def get_current_data(cls, sensor_id: str = None) -> Optional['EnvironmentData']:
        """获取当前最新的环境数据"""
        results = cls.get_latest_data(sensor_id, limit=1)
        return results[0] if results else None
    
    @classmethod
    def get_history_data(cls, start_time: datetime, end_time: datetime, 
                        sensor_id: str = None) -> List['EnvironmentData']:
        """获取历史环境数据"""
        where_clause = "timestamp BETWEEN ? AND ?"
        params = [start_time.isoformat(), end_time.isoformat()]
        
        if sensor_id:
            where_clause += " AND sensor_id = ?"
            params.append(sensor_id)
        
        return cls.find_all(
            where_clause=where_clause,
            params=params,
            order_by="timestamp ASC"
        )
    
    @classmethod
    def get_statistics(cls, start_time: datetime, end_time: datetime, 
                      sensor_id: str = None) -> Dict[str, Any]:
        """获取环境数据统计信息"""
        where_clause = "timestamp BETWEEN ? AND ?"
        params = [start_time.isoformat(), end_time.isoformat()]
        
        if sensor_id:
            where_clause += " AND sensor_id = ?"
            params.append(sensor_id)
        
        sql = f"""
            SELECT 
                COUNT(*) as total_records,
                AVG(temperature) as avg_temperature,
                MIN(temperature) as min_temperature,
                MAX(temperature) as max_temperature,
                AVG(humidity) as avg_humidity,
                MIN(humidity) as min_humidity,
                MAX(humidity) as max_humidity,
                AVG(light_intensity) as avg_light_intensity,
                MIN(light_intensity) as min_light_intensity,
                MAX(light_intensity) as max_light_intensity
            FROM {cls.table_name}
            WHERE {where_clause}
        """
        
        try:
            result = cls.execute_raw_sql(sql, params, fetch_one=True, fetch_all=False)
            return result if result else {}
        except Exception as e:
            logger.error(f"获取环境数据统计失败: {e}")
            raise
    
    @classmethod
    def get_hourly_averages(cls, start_time: datetime, end_time: datetime, 
                           sensor_id: str = None) -> List[Dict[str, Any]]:
        """获取按小时统计的平均值"""
        where_clause = "timestamp BETWEEN ? AND ?"
        params = [start_time.isoformat(), end_time.isoformat()]
        
        if sensor_id:
            where_clause += " AND sensor_id = ?"
            params.append(sensor_id)
        
        sql = f"""
            SELECT 
                strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                sensor_id,
                location,
                AVG(temperature) as avg_temperature,
                AVG(humidity) as avg_humidity,
                AVG(light_intensity) as avg_light_intensity,
                COUNT(*) as record_count
            FROM {cls.table_name}
            WHERE {where_clause}
            GROUP BY strftime('%Y-%m-%d %H:00:00', timestamp), sensor_id, location
            ORDER BY hour ASC
        """
        
        try:
            return cls.execute_raw_sql(sql, params, fetch_one=False, fetch_all=True)
        except Exception as e:
            logger.error(f"获取小时平均值失败: {e}")
            raise
    
    @classmethod
    def get_daily_averages(cls, start_time: datetime, end_time: datetime, 
                          sensor_id: str = None) -> List[Dict[str, Any]]:
        """获取按天统计的平均值"""
        where_clause = "timestamp BETWEEN ? AND ?"
        params = [start_time.isoformat(), end_time.isoformat()]
        
        if sensor_id:
            where_clause += " AND sensor_id = ?"
            params.append(sensor_id)
        
        sql = f"""
            SELECT 
                strftime('%Y-%m-%d', timestamp) as date,
                sensor_id,
                location,
                AVG(temperature) as avg_temperature,
                MIN(temperature) as min_temperature,
                MAX(temperature) as max_temperature,
                AVG(humidity) as avg_humidity,
                MIN(humidity) as min_humidity,
                MAX(humidity) as max_humidity,
                AVG(light_intensity) as avg_light_intensity,
                MIN(light_intensity) as min_light_intensity,
                MAX(light_intensity) as max_light_intensity,
                COUNT(*) as record_count
            FROM {cls.table_name}
            WHERE {where_clause}
            GROUP BY strftime('%Y-%m-%d', timestamp), sensor_id, location
            ORDER BY date ASC
        """
        
        try:
            return cls.execute_raw_sql(sql, params, fetch_one=False, fetch_all=True)
        except Exception as e:
            logger.error(f"获取日平均值失败: {e}")
            raise
    
    @classmethod
    def get_sensor_list(cls) -> List[Dict[str, Any]]:
        """获取传感器列表"""
        sql = f"""
            SELECT 
                sensor_id,
                location,
                COUNT(*) as record_count,
                MAX(timestamp) as last_update,
                AVG(temperature) as avg_temperature,
                AVG(humidity) as avg_humidity,
                AVG(light_intensity) as avg_light_intensity
            FROM {cls.table_name}
            GROUP BY sensor_id, location
            ORDER BY last_update DESC
        """
        
        try:
            return cls.execute_raw_sql(sql, [], fetch_one=False, fetch_all=True)
        except Exception as e:
            logger.error(f"获取传感器列表失败: {e}")
            raise
    
    @classmethod
    def cleanup_old_data(cls, days_to_keep: int = 365) -> int:
        """清理旧数据"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        sql = f"DELETE FROM {cls.table_name} WHERE timestamp < ?"
        
        try:
            # 先统计要删除的记录数
            count_sql = f"SELECT COUNT(*) as count FROM {cls.table_name} WHERE timestamp < ?"
            result = cls.execute_raw_sql(count_sql, [cutoff_date.isoformat()], 
                                       fetch_one=True, fetch_all=False)
            delete_count = result['count'] if result else 0
            
            # 执行删除
            if delete_count > 0:
                cls.execute_raw_sql(sql, [cutoff_date.isoformat()], 
                                  fetch_one=False, fetch_all=False)
                logger.info(f"清理了 {delete_count} 条环境数据记录")
            
            return delete_count
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            raise
    
    def is_temperature_normal(self, min_temp: float = 18.0, max_temp: float = 25.0) -> bool:
        """检查温度是否正常"""
        if self.temperature is None:
            return True
        return min_temp <= self.temperature <= max_temp
    
    def is_humidity_normal(self, min_humidity: float = 40.0, max_humidity: float = 60.0) -> bool:
        """检查湿度是否正常"""
        if self.humidity is None:
            return True
        return min_humidity <= self.humidity <= max_humidity
    
    def is_light_normal(self, min_light: float = 100.0, max_light: float = 500.0) -> bool:
        """检查光照是否正常"""
        if self.light_intensity is None:
            return True
        return min_light <= self.light_intensity <= max_light
    
    def check_all_thresholds(self, thresholds: Dict[str, Dict[str, float]]) -> List[str]:
        """检查所有阈值，返回异常项目列表"""
        alerts = []
        
        # 检查温度
        if 'temperature' in thresholds and self.temperature is not None:
            temp_config = thresholds['temperature']
            if not self.is_temperature_normal(temp_config.get('min', 18.0), 
                                            temp_config.get('max', 25.0)):
                alerts.append(f"温度异常: {self.temperature}°C")
        
        # 检查湿度
        if 'humidity' in thresholds and self.humidity is not None:
            humidity_config = thresholds['humidity']
            if not self.is_humidity_normal(humidity_config.get('min', 40.0), 
                                         humidity_config.get('max', 60.0)):
                alerts.append(f"湿度异常: {self.humidity}%")
        
        # 检查光照
        if 'light_intensity' in thresholds and self.light_intensity is not None:
            light_config = thresholds['light_intensity']
            if not self.is_light_normal(light_config.get('min', 100.0), 
                                      light_config.get('max', 500.0)):
                alerts.append(f"光照异常: {self.light_intensity} lux")
        
        return alerts
    
    def to_json_dict(self) -> Dict[str, Any]:
        """转换为JSON兼容的字典"""
        result = super().to_json_dict()
        
        # 格式化数值显示
        if 'temperature' in result and result['temperature'] is not None:
            result['temperature'] = round(float(result['temperature']), 1)
        
        if 'humidity' in result and result['humidity'] is not None:
            result['humidity'] = round(float(result['humidity']), 1)
        
        if 'light_intensity' in result and result['light_intensity'] is not None:
            result['light_intensity'] = round(float(result['light_intensity']), 0)
        
        return result