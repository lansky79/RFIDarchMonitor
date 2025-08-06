#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集配置模型
管理传感器和RFID设备的采集频率配置
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .base import BaseModel, ValidationError, validate_required_fields, validate_numeric_range

logger = logging.getLogger(__name__)

class CollectionConfig(BaseModel):
    """数据采集配置模型"""
    
    table_name = 'collection_configs'
    
    # 默认配置值
    DEFAULT_SENSOR_INTERVAL = 30  # 传感器采集间隔(秒)
    DEFAULT_RFID_INTERVAL = 10    # RFID扫描间隔(秒)
    
    # 配置范围限制
    MIN_SENSOR_INTERVAL = 1       # 最小传感器间隔(秒)
    MAX_SENSOR_INTERVAL = 300     # 最大传感器间隔(秒)
    MIN_RFID_INTERVAL = 1         # 最小RFID间隔(秒)
    MAX_RFID_INTERVAL = 60        # 最大RFID间隔(秒)
    
    def __init__(self, **kwargs):
        """初始化采集配置"""
        # 设置默认值
        if 'sensor_interval' not in kwargs:
            kwargs['sensor_interval'] = self.DEFAULT_SENSOR_INTERVAL
        if 'rfid_interval' not in kwargs:
            kwargs['rfid_interval'] = self.DEFAULT_RFID_INTERVAL
        if 'is_paused' not in kwargs:
            kwargs['is_paused'] = True  # 默认暂停数据采集
        if 'updated_by' not in kwargs:
            kwargs['updated_by'] = 'system'
            
        super().__init__(**kwargs)
    
    def validate(self) -> None:
        """验证配置数据"""
        # 验证必填字段
        validate_required_fields(self.data, ['sensor_interval', 'rfid_interval'])
        
        # 验证数值范围
        validate_numeric_range(self.data, {
            'sensor_interval': (self.MIN_SENSOR_INTERVAL, self.MAX_SENSOR_INTERVAL),
            'rfid_interval': (self.MIN_RFID_INTERVAL, self.MAX_RFID_INTERVAL)
        })
        
        # 验证布尔值
        if 'is_paused' in self.data and not isinstance(self.data['is_paused'], bool):
            raise ValidationError("is_paused 必须是布尔值")
        
        # 验证操作者字段长度
        if 'updated_by' in self.data and len(str(self.data['updated_by'])) > 100:
            raise ValidationError("updated_by 字段长度不能超过100字符")
    
    def save(self) -> bool:
        """保存配置前进行验证"""
        self.validate()
        return super().save()
    
    @classmethod
    def create(cls, **kwargs) -> 'CollectionConfig':
        """创建新的采集配置"""
        instance = cls(**kwargs)
        instance.validate()
        return super().create(**kwargs)
    
    @classmethod
    def get_current_config(cls) -> Optional['CollectionConfig']:
        """获取当前有效的采集配置"""
        try:
            # 获取最新的配置记录
            configs = cls.find_all(order_by='updated_at DESC', limit=1)
            return configs[0] if configs else None
        except Exception as e:
            logger.error(f"获取当前采集配置失败: {e}")
            return None
    
    @classmethod
    def get_or_create_default(cls) -> 'CollectionConfig':
        """获取当前配置，如果不存在则创建默认配置"""
        current_config = cls.get_current_config()
        if current_config:
            return current_config
        
        # 创建默认配置
        logger.info("创建默认采集配置")
        return cls.create(
            sensor_interval=cls.DEFAULT_SENSOR_INTERVAL,
            rfid_interval=cls.DEFAULT_RFID_INTERVAL,
            is_paused=False,
            updated_by='system'
        )
    
    def update_config(self, sensor_interval: int = None, rfid_interval: int = None, 
                     is_paused: bool = None, updated_by: str = 'system') -> bool:
        """更新采集配置"""
        try:
            if sensor_interval is not None:
                self.sensor_interval = sensor_interval
            if rfid_interval is not None:
                self.rfid_interval = rfid_interval
            if is_paused is not None:
                self.is_paused = is_paused
            
            self.updated_by = updated_by
            self.updated_at = datetime.now().isoformat()
            
            return self.save()
            
        except Exception as e:
            logger.error(f"更新采集配置失败: {e}")
            raise
    
    def pause_collection(self, updated_by: str = 'system') -> bool:
        """暂停数据采集"""
        return self.update_config(is_paused=True, updated_by=updated_by)
    
    def resume_collection(self, updated_by: str = 'system') -> bool:
        """恢复数据采集"""
        return self.update_config(is_paused=False, updated_by=updated_by)
    
    def reset_to_default(self, updated_by: str = 'system') -> bool:
        """重置为默认配置"""
        return self.update_config(
            sensor_interval=self.DEFAULT_SENSOR_INTERVAL,
            rfid_interval=self.DEFAULT_RFID_INTERVAL,
            is_paused=False,
            updated_by=updated_by
        )
    
    def get_performance_impact(self) -> Dict[str, Any]:
        """计算配置对性能的影响"""
        # 基于采集频率估算性能影响
        sensor_load = 60 / self.sensor_interval  # 每分钟传感器采集次数
        rfid_load = 60 / self.rfid_interval       # 每分钟RFID扫描次数
        
        # 估算CPU使用率影响 (基于经验值)
        estimated_cpu_usage = (sensor_load * 0.5 + rfid_load * 1.0) / 100
        
        # 估算内存使用影响
        estimated_memory_mb = sensor_load * 0.1 + rfid_load * 0.2
        
        # 性能等级评估
        total_load = sensor_load + rfid_load
        if total_load > 20:
            performance_level = 'high'
            warning = '采集频率较高，可能影响系统性能'
        elif total_load > 10:
            performance_level = 'medium'
            warning = '采集频率适中，注意监控系统性能'
        else:
            performance_level = 'low'
            warning = None
        
        return {
            'sensorLoad': sensor_load,
            'rfidLoad': rfid_load,
            'totalLoad': total_load,
            'estimatedCpuUsage': min(estimated_cpu_usage, 100),  # 限制在100%以内
            'estimatedMemoryMB': estimated_memory_mb,
            'performanceLevel': performance_level,
            'warning': warning
        }
    
    def get_recommended_config(self) -> Dict[str, int]:
        """获取推荐的采集配置"""
        # 基于系统负载推荐配置
        # 这里可以根据实际硬件配置动态调整
        return {
            'sensorInterval': 30,  # 推荐传感器间隔
            'rfidInterval': 15,    # 推荐RFID间隔
            'reason': '基于系统性能平衡的推荐配置'
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = super().to_dict()
        
        # 添加性能影响信息
        result['performanceImpact'] = self.get_performance_impact()
        result['recommendedConfig'] = self.get_recommended_config()
        
        return result
    
    def to_api_dict(self) -> Dict[str, Any]:
        """转换为API响应格式"""
        return {
            'id': self.data.get('id'),
            'sensorInterval': self.sensor_interval,
            'rfidInterval': self.rfid_interval,
            'isPaused': self.is_paused,
            'updatedBy': self.updated_by,
            'createdAt': self.data.get('created_at'),
            'updatedAt': self.data.get('updated_at'),
            'performanceImpact': self.get_performance_impact()
        }
    
    @classmethod
    def get_config_history(cls, limit: int = 10) -> List['CollectionConfig']:
        """获取配置变更历史"""
        try:
            return cls.find_all(order_by='updated_at DESC', limit=limit)
        except Exception as e:
            logger.error(f"获取配置历史失败: {e}")
            return []
    
    def __repr__(self):
        """字符串表示"""
        return (f"<CollectionConfig(sensor_interval={self.sensor_interval}, "
                f"rfid_interval={self.rfid_interval}, is_paused={self.is_paused})>")


class CollectionStatus(BaseModel):
    """数据采集状态模型"""
    
    table_name = 'collection_status'
    
    def __init__(self, **kwargs):
        """初始化采集状态"""
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.now().isoformat()
        if 'is_running' not in kwargs:
            kwargs['is_running'] = False
            
        super().__init__(**kwargs)
    
    def validate(self) -> None:
        """验证状态数据"""
        # 验证必填字段
        validate_required_fields(self.data, ['is_running'])
        
        # 验证布尔值
        if not isinstance(self.data['is_running'], bool):
            raise ValidationError("is_running 必须是布尔值")
        
        # 验证数值范围
        if 'cpu_usage' in self.data and self.data['cpu_usage'] is not None:
            if not (0 <= self.data['cpu_usage'] <= 100):
                raise ValidationError("cpu_usage 必须在 0-100 范围内")
        
        if 'memory_usage' in self.data and self.data['memory_usage'] is not None:
            if self.data['memory_usage'] < 0:
                raise ValidationError("memory_usage 不能为负数")
    
    def save(self) -> bool:
        """保存状态前进行验证"""
        self.validate()
        return super().save()
    
    @classmethod
    def create(cls, **kwargs) -> 'CollectionStatus':
        """创建新的状态记录"""
        instance = cls(**kwargs)
        instance.validate()
        return super().create(**kwargs)
    
    @classmethod
    def get_latest_status(cls) -> Optional['CollectionStatus']:
        """获取最新的采集状态"""
        try:
            statuses = cls.find_all(order_by='timestamp DESC', limit=1)
            return statuses[0] if statuses else None
        except Exception as e:
            logger.error(f"获取最新采集状态失败: {e}")
            return None
    
    @classmethod
    def record_status(cls, is_running: bool, sensor_last_collection: datetime = None,
                     rfid_last_collection: datetime = None, cpu_usage: float = None,
                     memory_usage: float = None, error_message: str = None) -> 'CollectionStatus':
        """记录采集状态"""
        try:
            return cls.create(
                is_running=is_running,
                sensor_last_collection=sensor_last_collection.isoformat() if sensor_last_collection else None,
                rfid_last_collection=rfid_last_collection.isoformat() if rfid_last_collection else None,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"记录采集状态失败: {e}")
            raise
    
    @classmethod
    def get_status_history(cls, hours: int = 24, limit: int = 100) -> List['CollectionStatus']:
        """获取指定时间范围内的状态历史"""
        try:
            # 计算时间范围
            from datetime import timedelta
            start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            return cls.find_all(
                where_clause='timestamp >= ?',
                params=[start_time],
                order_by='timestamp DESC',
                limit=limit
            )
        except Exception as e:
            logger.error(f"获取状态历史失败: {e}")
            return []
    
    def to_api_dict(self) -> Dict[str, Any]:
        """转换为API响应格式"""
        return {
            'id': self.data.get('id'),
            'timestamp': self.data.get('timestamp'),
            'isRunning': self.is_running,
            'sensorLastCollection': self.data.get('sensor_last_collection'),
            'rfidLastCollection': self.data.get('rfid_last_collection'),
            'cpuUsage': self.data.get('cpu_usage'),
            'memoryUsage': self.data.get('memory_usage'),
            'errorMessage': self.data.get('error_message')
        }
    
    def get_uptime_info(self) -> Dict[str, Any]:
        """获取运行时间信息"""
        if not self.is_running:
            return {'uptime': 0, 'status': 'stopped'}
        
        # 查找最近一次启动的时间
        try:
            last_start = self.find_all(
                where_clause='is_running = ? AND timestamp <= ?',
                params=[True, self.data.get('timestamp')],
                order_by='timestamp DESC',
                limit=1
            )
            
            if last_start:
                start_time = datetime.fromisoformat(last_start[0].timestamp)
                current_time = datetime.fromisoformat(self.data.get('timestamp'))
                uptime_seconds = (current_time - start_time).total_seconds()
                
                return {
                    'uptime': uptime_seconds,
                    'uptimeFormatted': self._format_uptime(uptime_seconds),
                    'status': 'running',
                    'startTime': start_time.isoformat()
                }
            else:
                return {'uptime': 0, 'status': 'unknown'}
                
        except Exception as e:
            logger.error(f"计算运行时间失败: {e}")
            return {'uptime': 0, 'status': 'error'}
    
    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            return f"{int(seconds // 60)}分钟"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}小时{minutes}分钟"
        else:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            return f"{days}天{hours}小时"
    
    def __repr__(self):
        """字符串表示"""
        status = "运行中" if self.is_running else "已停止"
        return f"<CollectionStatus({status}, {self.data.get('timestamp')})>"