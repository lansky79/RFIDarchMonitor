#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集频率控制服务
管理传感器和RFID设备的采集频率配置
"""

import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from models.collection_config import CollectionConfig, CollectionStatus
from models.base import ValidationError

logger = logging.getLogger(__name__)

class CollectionFrequencyService:
    """数据采集频率控制服务"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._current_config = None
        self._config_change_callbacks = []
        self._status_change_callbacks = []
        
        # 初始化当前配置
        self._load_current_config()
    
    def _load_current_config(self) -> None:
        """加载当前配置"""
        try:
            with self._lock:
                self._current_config = CollectionConfig.get_or_create_default()
                logger.info(f"加载采集配置: 传感器间隔={self._current_config.sensor_interval}秒, "
                          f"RFID间隔={self._current_config.rfid_interval}秒, "
                          f"暂停状态={self._current_config.is_paused}")
        except Exception as e:
            logger.error(f"加载当前配置失败: {e}")
            # 创建默认配置作为后备
            with self._lock:
                self._current_config = CollectionConfig()
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前采集配置"""
        try:
            with self._lock:
                if not self._current_config:
                    self._load_current_config()
                
                return self._current_config.to_api_dict()
                
        except Exception as e:
            logger.error(f"获取当前配置失败: {e}")
            # 返回默认配置
            return {
                'id': None,
                'sensorInterval': CollectionConfig.DEFAULT_SENSOR_INTERVAL,
                'rfidInterval': CollectionConfig.DEFAULT_RFID_INTERVAL,
                'isPaused': False,
                'updatedBy': 'system',
                'createdAt': None,
                'updatedAt': None,
                'performanceImpact': {
                    'sensorLoad': 2.0,
                    'rfidLoad': 6.0,
                    'totalLoad': 8.0,
                    'estimatedCpuUsage': 3.5,
                    'estimatedMemoryMB': 1.4,
                    'performanceLevel': 'low',
                    'warning': None
                }
            }
    
    def update_config(self, config_data: Dict[str, Any], updated_by: str = 'system') -> Dict[str, Any]:
        """更新采集配置"""
        try:
            # 验证配置数据
            sensor_interval = config_data.get('sensorInterval')
            rfid_interval = config_data.get('rfidInterval')
            is_paused = config_data.get('isPaused')
            
            if sensor_interval is not None:
                if not isinstance(sensor_interval, int) or sensor_interval < CollectionConfig.MIN_SENSOR_INTERVAL or sensor_interval > CollectionConfig.MAX_SENSOR_INTERVAL:
                    raise ValidationError(f"传感器采集间隔必须在 {CollectionConfig.MIN_SENSOR_INTERVAL}-{CollectionConfig.MAX_SENSOR_INTERVAL} 秒之间")
            
            if rfid_interval is not None:
                if not isinstance(rfid_interval, int) or rfid_interval < CollectionConfig.MIN_RFID_INTERVAL or rfid_interval > CollectionConfig.MAX_RFID_INTERVAL:
                    raise ValidationError(f"RFID扫描间隔必须在 {CollectionConfig.MIN_RFID_INTERVAL}-{CollectionConfig.MAX_RFID_INTERVAL} 秒之间")
            
            if is_paused is not None and not isinstance(is_paused, bool):
                raise ValidationError("暂停状态必须是布尔值")
            
            with self._lock:
                # 获取当前配置
                if not self._current_config:
                    self._load_current_config()
                
                # 记录变更前的配置
                old_config = self._current_config.to_api_dict()
                
                # 更新配置
                success = self._current_config.update_config(
                    sensor_interval=sensor_interval,
                    rfid_interval=rfid_interval,
                    is_paused=is_paused,
                    updated_by=updated_by
                )
                
                if success:
                    new_config = self._current_config.to_api_dict()
                    
                    # 记录配置变更日志
                    self._log_config_change(old_config, new_config, updated_by)
                    
                    # 通知配置变更回调
                    self._notify_config_change_callbacks(old_config, new_config)
                    
                    logger.info(f"采集配置更新成功: 用户={updated_by}, "
                              f"传感器间隔={self._current_config.sensor_interval}秒, "
                              f"RFID间隔={self._current_config.rfid_interval}秒, "
                              f"暂停状态={self._current_config.is_paused}")
                    
                    return {
                        'success': True,
                        'message': '配置更新成功',
                        'config': new_config
                    }
                else:
                    return {
                        'success': False,
                        'message': '配置更新失败',
                        'config': old_config
                    }
                    
        except ValidationError as e:
            logger.warning(f"配置验证失败: {e}")
            return {
                'success': False,
                'message': str(e),
                'config': self.get_current_config()
            }
        except Exception as e:
            logger.error(f"更新采集配置失败: {e}")
            return {
                'success': False,
                'message': f'配置更新失败: {str(e)}',
                'config': self.get_current_config()
            }
    
    def pause_collection(self, updated_by: str = 'system') -> Dict[str, Any]:
        """暂停数据采集"""
        try:
            with self._lock:
                if not self._current_config:
                    self._load_current_config()
                
                if self._current_config.is_paused:
                    return {
                        'success': True,
                        'message': '数据采集已处于暂停状态',
                        'status': 'paused'
                    }
                
                success = self._current_config.pause_collection(updated_by)
                
                if success:
                    # 记录状态变更
                    self._record_status_change('paused', updated_by)
                    
                    # 通知状态变更回调
                    self._notify_status_change_callbacks('paused', updated_by)
                    
                    logger.info(f"数据采集已暂停: 用户={updated_by}")
                    
                    return {
                        'success': True,
                        'message': '数据采集已暂停',
                        'status': 'paused'
                    }
                else:
                    return {
                        'success': False,
                        'message': '暂停数据采集失败',
                        'status': 'unknown'
                    }
                    
        except Exception as e:
            logger.error(f"暂停数据采集失败: {e}")
            return {
                'success': False,
                'message': f'暂停失败: {str(e)}',
                'status': 'error'
            }
    
    def resume_collection(self, updated_by: str = 'system') -> Dict[str, Any]:
        """恢复数据采集"""
        try:
            with self._lock:
                if not self._current_config:
                    self._load_current_config()
                
                if not self._current_config.is_paused:
                    return {
                        'success': True,
                        'message': '数据采集已在运行中',
                        'status': 'running'
                    }
                
                success = self._current_config.resume_collection(updated_by)
                
                if success:
                    # 记录状态变更
                    self._record_status_change('running', updated_by)
                    
                    # 通知状态变更回调
                    self._notify_status_change_callbacks('running', updated_by)
                    
                    logger.info(f"数据采集已恢复: 用户={updated_by}")
                    
                    return {
                        'success': True,
                        'message': '数据采集已恢复',
                        'status': 'running'
                    }
                else:
                    return {
                        'success': False,
                        'message': '恢复数据采集失败',
                        'status': 'unknown'
                    }
                    
        except Exception as e:
            logger.error(f"恢复数据采集失败: {e}")
            return {
                'success': False,
                'message': f'恢复失败: {str(e)}',
                'status': 'error'
            }
    
    def reset_to_default(self, updated_by: str = 'system') -> Dict[str, Any]:
        """重置为默认配置"""
        try:
            with self._lock:
                if not self._current_config:
                    self._load_current_config()
                
                # 记录重置前的配置
                old_config = self._current_config.to_api_dict()
                
                success = self._current_config.reset_to_default(updated_by)
                
                if success:
                    new_config = self._current_config.to_api_dict()
                    
                    # 记录配置变更日志
                    self._log_config_change(old_config, new_config, updated_by, action='reset')
                    
                    # 通知配置变更回调
                    self._notify_config_change_callbacks(old_config, new_config)
                    
                    logger.info(f"采集配置已重置为默认值: 用户={updated_by}")
                    
                    return {
                        'success': True,
                        'message': '配置已重置为默认值',
                        'config': new_config
                    }
                else:
                    return {
                        'success': False,
                        'message': '重置配置失败',
                        'config': old_config
                    }
                    
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            return {
                'success': False,
                'message': f'重置失败: {str(e)}',
                'config': self.get_current_config()
            }
    
    def validate_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置数据"""
        try:
            errors = []
            warnings = []
            
            # 验证传感器间隔
            sensor_interval = config_data.get('sensorInterval')
            if sensor_interval is not None:
                if not isinstance(sensor_interval, int):
                    errors.append("传感器采集间隔必须是整数")
                elif sensor_interval < CollectionConfig.MIN_SENSOR_INTERVAL:
                    errors.append(f"传感器采集间隔不能小于 {CollectionConfig.MIN_SENSOR_INTERVAL} 秒")
                elif sensor_interval > CollectionConfig.MAX_SENSOR_INTERVAL:
                    errors.append(f"传感器采集间隔不能大于 {CollectionConfig.MAX_SENSOR_INTERVAL} 秒")
                elif sensor_interval < 10:
                    warnings.append("传感器采集间隔过短可能影响系统性能")
            
            # 验证RFID间隔
            rfid_interval = config_data.get('rfidInterval')
            if rfid_interval is not None:
                if not isinstance(rfid_interval, int):
                    errors.append("RFID扫描间隔必须是整数")
                elif rfid_interval < CollectionConfig.MIN_RFID_INTERVAL:
                    errors.append(f"RFID扫描间隔不能小于 {CollectionConfig.MIN_RFID_INTERVAL} 秒")
                elif rfid_interval > CollectionConfig.MAX_RFID_INTERVAL:
                    errors.append(f"RFID扫描间隔不能大于 {CollectionConfig.MAX_RFID_INTERVAL} 秒")
                elif rfid_interval < 5:
                    warnings.append("RFID扫描间隔过短可能影响系统性能")
            
            # 验证暂停状态
            is_paused = config_data.get('isPaused')
            if is_paused is not None and not isinstance(is_paused, bool):
                errors.append("暂停状态必须是布尔值")
            
            # 计算性能影响
            performance_impact = None
            if sensor_interval and rfid_interval:
                temp_config = CollectionConfig(
                    sensor_interval=sensor_interval,
                    rfid_interval=rfid_interval
                )
                performance_impact = temp_config.get_performance_impact()
                
                # 添加性能警告
                if performance_impact['performanceLevel'] == 'high':
                    warnings.append(performance_impact.get('warning', '采集频率较高，可能影响系统性能'))
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'performanceImpact': performance_impact
            }
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return {
                'valid': False,
                'errors': [f'验证失败: {str(e)}'],
                'warnings': [],
                'performanceImpact': None
            }
    
    def get_config_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取配置变更历史"""
        try:
            history_configs = CollectionConfig.get_config_history(limit)
            return [config.to_api_dict() for config in history_configs]
        except Exception as e:
            logger.error(f"获取配置历史失败: {e}")
            return []
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            with self._lock:
                if not self._current_config:
                    self._load_current_config()
                
                # 获取当前配置的性能影响
                performance_impact = self._current_config.get_performance_impact()
                
                # 获取推荐配置
                recommended_config = self._current_config.get_recommended_config()
                
                # 获取最新的系统状态
                latest_status = CollectionStatus.get_latest_status()
                
                return {
                    'currentConfig': {
                        'sensorInterval': self._current_config.sensor_interval,
                        'rfidInterval': self._current_config.rfid_interval,
                        'isPaused': self._current_config.is_paused
                    },
                    'performanceImpact': performance_impact,
                    'recommendedConfig': recommended_config,
                    'systemStatus': latest_status.to_api_dict() if latest_status else None,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {
                'currentConfig': None,
                'performanceImpact': None,
                'recommendedConfig': None,
                'systemStatus': None,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def add_config_change_callback(self, callback: Callable[[Dict, Dict], None]) -> None:
        """添加配置变更回调函数"""
        with self._lock:
            self._config_change_callbacks.append(callback)
    
    def add_status_change_callback(self, callback: Callable[[str, str], None]) -> None:
        """添加状态变更回调函数"""
        with self._lock:
            self._status_change_callbacks.append(callback)
    
    def _notify_config_change_callbacks(self, old_config: Dict, new_config: Dict) -> None:
        """通知配置变更回调函数"""
        with self._lock:
            for callback in self._config_change_callbacks:
                try:
                    callback(old_config, new_config)
                except Exception as e:
                    logger.error(f"配置变更回调函数执行失败: {e}")
    
    def _notify_status_change_callbacks(self, status: str, updated_by: str) -> None:
        """通知状态变更回调函数"""
        with self._lock:
            for callback in self._status_change_callbacks:
                try:
                    callback(status, updated_by)
                except Exception as e:
                    logger.error(f"状态变更回调函数执行失败: {e}")
    
    def _log_config_change(self, old_config: Dict, new_config: Dict, 
                          updated_by: str, action: str = 'update') -> None:
        """记录配置变更日志"""
        try:
            from models.base import BaseModel
            
            # 构建变更详情
            changes = []
            if old_config['sensorInterval'] != new_config['sensorInterval']:
                changes.append(f"传感器间隔: {old_config['sensorInterval']}s → {new_config['sensorInterval']}s")
            if old_config['rfidInterval'] != new_config['rfidInterval']:
                changes.append(f"RFID间隔: {old_config['rfidInterval']}s → {new_config['rfidInterval']}s")
            if old_config['isPaused'] != new_config['isPaused']:
                status_text = "暂停" if new_config['isPaused'] else "运行"
                changes.append(f"采集状态: {status_text}")
            
            if changes or action == 'reset':
                change_message = f"采集配置{action}: {', '.join(changes) if changes else '重置为默认值'}"
                
                # 记录到系统日志
                BaseModel.execute_raw_sql(
                    "INSERT INTO system_logs (log_level, module, message, user_id) VALUES (?, ?, ?, ?)",
                    ['INFO', 'collection_frequency_service', change_message, updated_by]
                )
                
        except Exception as e:
            logger.error(f"记录配置变更日志失败: {e}")
    
    def _record_status_change(self, status: str, updated_by: str) -> None:
        """记录状态变更"""
        try:
            # 记录到采集状态表
            CollectionStatus.record_status(
                is_running=(status == 'running'),
                error_message=None if status in ['running', 'paused'] else f'状态变更为: {status}'
            )
            
            # 记录到系统日志
            from models.base import BaseModel
            BaseModel.execute_raw_sql(
                "INSERT INTO system_logs (log_level, module, message, user_id) VALUES (?, ?, ?, ?)",
                ['INFO', 'collection_frequency_service', f'数据采集状态变更为: {status}', updated_by]
            )
            
        except Exception as e:
            logger.error(f"记录状态变更失败: {e}")
    
    def export_config(self) -> str:
        """导出配置为JSON字符串"""
        try:
            import json
            config_data = self.get_current_config()
            return json.dumps(config_data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return "{}"
    
    def import_config(self, config_json: str, updated_by: str = 'system') -> Dict[str, Any]:
        """从JSON字符串导入配置"""
        try:
            import json
            config_data = json.loads(config_json)
            
            # 验证配置
            validation_result = self.validate_config(config_data)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': f"配置验证失败: {', '.join(validation_result['errors'])}",
                    'config': self.get_current_config()
                }
            
            # 更新配置
            return self.update_config(config_data, updated_by)
            
        except json.JSONDecodeError as e:
            logger.error(f"配置JSON解析失败: {e}")
            return {
                'success': False,
                'message': f'配置格式错误: {str(e)}',
                'config': self.get_current_config()
            }
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return {
                'success': False,
                'message': f'导入失败: {str(e)}',
                'config': self.get_current_config()
            }


# 全局采集频率控制服务实例
collection_frequency_service = CollectionFrequencyService()