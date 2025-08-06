#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集调度器
管理采集任务的启动、停止和频率调整
"""

import logging
import threading
import time
import psutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from services.collection_frequency_service import collection_frequency_service
from models.collection_config import CollectionConfig, CollectionStatus
from models.environment import EnvironmentData
from models.rfid import RfidTag
from models.base import BaseModel

logger = logging.getLogger(__name__)

class CollectionScheduler:
    """数据采集调度器"""
    
    def __init__(self, frequency_service=None):
        self.frequency_service = frequency_service or collection_frequency_service
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self._lock = threading.Lock()
        
        # 采集状态
        self._sensor_last_collection = None
        self._rfid_last_collection = None
        self._collection_errors = []
        
        # 性能监控
        self._performance_monitor_thread = None
        self._stop_performance_monitor = False
        
        # 注册频率服务回调
        self.frequency_service.add_config_change_callback(self._on_config_change)
        self.frequency_service.add_status_change_callback(self._on_status_change)
        
        # 模拟传感器和RFID设备（用于演示）
        self._init_mock_devices()
    
    def _init_mock_devices(self):
        """初始化模拟设备"""
        self.mock_sensors = {
            'SENSOR_001': {'location': '档案室A区', 'base_temp': 22.0, 'base_humidity': 50.0, 'base_light': 300.0},
            'SENSOR_002': {'location': '档案室B区', 'base_temp': 21.5, 'base_humidity': 48.0, 'base_light': 280.0},
            'SENSOR_003': {'location': '档案室C区', 'base_temp': 23.0, 'base_humidity': 52.0, 'base_light': 320.0}
        }
        
        self.mock_rfid_devices = {
            1: {'name': 'RFID_READER_001', 'location': '档案室入口', 'status': 'online'},
            2: {'name': 'RFID_READER_002', 'location': '档案室出口', 'status': 'online'}
        }
    
    def start_collection(self) -> Dict[str, Any]:
        """启动数据采集"""
        try:
            with self._lock:
                if self.is_running:
                    return {
                        'success': True,
                        'message': '数据采集已在运行中',
                        'status': 'running'
                    }
                
                # 获取当前配置
                config = self.frequency_service.get_current_config()
                
                if config['isPaused']:
                    return {
                        'success': False,
                        'message': '数据采集已暂停，请先恢复采集',
                        'status': 'paused'
                    }
                
                # 启动调度器
                self.scheduler.start()
                
                # 添加采集任务
                self._schedule_collection_jobs(config)
                
                # 启动性能监控
                self._start_performance_monitor()
                
                self.is_running = True
                
                # 记录启动状态
                self._record_collection_status(True)
                
                logger.info(f"数据采集启动成功: 传感器间隔={config['sensorInterval']}秒, "
                          f"RFID间隔={config['rfidInterval']}秒")
                
                return {
                    'success': True,
                    'message': '数据采集启动成功',
                    'status': 'running',
                    'config': config
                }
                
        except Exception as e:
            logger.error(f"启动数据采集失败: {e}")
            return {
                'success': False,
                'message': f'启动失败: {str(e)}',
                'status': 'error'
            }
    
    def stop_collection(self) -> Dict[str, Any]:
        """停止数据采集"""
        try:
            with self._lock:
                if not self.is_running:
                    return {
                        'success': True,
                        'message': '数据采集已停止',
                        'status': 'stopped'
                    }
                
                # 停止性能监控
                self._stop_performance_monitor_flag = True
                if self._performance_monitor_thread:
                    self._performance_monitor_thread.join(timeout=5)
                
                # 停止调度器
                self.scheduler.shutdown(wait=False)
                
                self.is_running = False
                
                # 记录停止状态
                self._record_collection_status(False)
                
                logger.info("数据采集已停止")
                
                return {
                    'success': True,
                    'message': '数据采集已停止',
                    'status': 'stopped'
                }
                
        except Exception as e:
            logger.error(f"停止数据采集失败: {e}")
            return {
                'success': False,
                'message': f'停止失败: {str(e)}',
                'status': 'error'
            }
    
    def update_intervals(self, sensor_interval: int = None, rfid_interval: int = None) -> Dict[str, Any]:
        """更新采集间隔"""
        try:
            with self._lock:
                if not self.is_running:
                    return {
                        'success': False,
                        'message': '数据采集未运行，无法更新间隔',
                        'status': 'stopped'
                    }
                
                # 获取当前配置
                config = self.frequency_service.get_current_config()
                
                # 更新配置
                update_data = {}
                if sensor_interval is not None:
                    update_data['sensorInterval'] = sensor_interval
                if rfid_interval is not None:
                    update_data['rfidInterval'] = rfid_interval
                
                if update_data:
                    result = self.frequency_service.update_config(update_data, 'scheduler')
                    if not result['success']:
                        return result
                    
                    # 重新调度任务
                    self._reschedule_collection_jobs(result['config'])
                    
                    logger.info(f"采集间隔更新成功: {update_data}")
                    
                    return {
                        'success': True,
                        'message': '采集间隔更新成功',
                        'status': 'running',
                        'config': result['config']
                    }
                else:
                    return {
                        'success': True,
                        'message': '无需更新',
                        'status': 'running',
                        'config': config
                    }
                    
        except Exception as e:
            logger.error(f"更新采集间隔失败: {e}")
            return {
                'success': False,
                'message': f'更新失败: {str(e)}',
                'status': 'error'
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取采集状态"""
        try:
            with self._lock:
                config = self.frequency_service.get_current_config()
                
                # 获取系统性能信息
                cpu_usage = psutil.cpu_percent(interval=1)
                memory_info = psutil.virtual_memory()
                
                # 获取最新的采集状态记录
                latest_status = CollectionStatus.get_latest_status()
                
                status_info = {
                    'isRunning': self.is_running,
                    'isPaused': config['isPaused'],
                    'currentConfig': {
                        'sensorInterval': config['sensorInterval'],
                        'rfidInterval': config['rfidInterval']
                    },
                    'lastCollection': {
                        'sensor': self._sensor_last_collection.isoformat() if self._sensor_last_collection else None,
                        'rfid': self._rfid_last_collection.isoformat() if self._rfid_last_collection else None
                    },
                    'performance': {
                        'cpuUsage': cpu_usage,
                        'memoryUsage': memory_info.percent,
                        'memoryUsedMB': memory_info.used / (1024 * 1024)
                    },
                    'errors': self._collection_errors[-5:],  # 最近5个错误
                    'statistics': self._get_collection_statistics(),
                    'timestamp': datetime.now().isoformat()
                }
                
                return status_info
                
        except Exception as e:
            logger.error(f"获取采集状态失败: {e}")
            return {
                'isRunning': False,
                'isPaused': True,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _schedule_collection_jobs(self, config: Dict[str, Any]) -> None:
        """调度采集任务"""
        try:
            # 添加传感器采集任务
            self.scheduler.add_job(
                func=self._collect_sensor_data,
                trigger=IntervalTrigger(seconds=config['sensorInterval']),
                id='sensor_collection',
                replace_existing=True,
                max_instances=1
            )
            
            # 添加RFID扫描任务
            self.scheduler.add_job(
                func=self._scan_rfid_devices,
                trigger=IntervalTrigger(seconds=config['rfidInterval']),
                id='rfid_scanning',
                replace_existing=True,
                max_instances=1
            )
            
            logger.info(f"采集任务调度成功: 传感器{config['sensorInterval']}秒, RFID{config['rfidInterval']}秒")
            
        except Exception as e:
            logger.error(f"调度采集任务失败: {e}")
            raise
    
    def _reschedule_collection_jobs(self, config: Dict[str, Any]) -> None:
        """重新调度采集任务"""
        try:
            # 移除现有任务
            if self.scheduler.get_job('sensor_collection'):
                self.scheduler.remove_job('sensor_collection')
            if self.scheduler.get_job('rfid_scanning'):
                self.scheduler.remove_job('rfid_scanning')
            
            # 重新添加任务
            self._schedule_collection_jobs(config)
            
            logger.info("采集任务重新调度成功")
            
        except Exception as e:
            logger.error(f"重新调度采集任务失败: {e}")
            raise
    
    def _collect_sensor_data(self) -> None:
        """采集传感器数据"""
        try:
            import random
            
            for sensor_id, sensor_info in self.mock_sensors.items():
                # 生成模拟数据
                temperature = sensor_info['base_temp'] + random.uniform(-2.0, 2.0)
                humidity = sensor_info['base_humidity'] + random.uniform(-5.0, 5.0)
                light_intensity = sensor_info['base_light'] + random.uniform(-50.0, 50.0)
                
                # 确保数值在合理范围内
                temperature = max(15.0, min(30.0, temperature))
                humidity = max(30.0, min(70.0, humidity))
                light_intensity = max(50.0, min(600.0, light_intensity))
                
                sensor_data = {
                    'sensor_id': sensor_id,
                    'temperature': round(temperature, 1),
                    'humidity': round(humidity, 1),
                    'light_intensity': round(light_intensity, 0),
                    'location': sensor_info['location'],
                    'timestamp': datetime.now().isoformat()
                }
                
                # 保存到数据库
                EnvironmentData.create(**sensor_data)
                
                logger.debug(f"传感器数据采集成功: {sensor_id}")
            
            # 更新最后采集时间
            self._sensor_last_collection = datetime.now()
            
            # 清除传感器相关的错误
            self._collection_errors = [err for err in self._collection_errors 
                                     if not err.get('type') == 'sensor']
            
        except Exception as e:
            error_info = {
                'type': 'sensor',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self._collection_errors.append(error_info)
            logger.error(f"传感器数据采集失败: {e}")
    
    def _scan_rfid_devices(self) -> None:
        """扫描RFID设备"""
        try:
            import random
            
            # 模拟RFID标签扫描（随机扫描到一些标签）
            if random.random() < 0.3:  # 30%概率扫描到标签
                # 获取活跃的标签
                active_tags = RfidTag.get_active_tags()
                if active_tags:
                    # 随机选择一个标签
                    tag = random.choice(active_tags)
                    device_id = random.choice(list(self.mock_rfid_devices.keys()))
                    device_info = self.mock_rfid_devices[device_id]
                    
                    # 更新标签位置
                    tag.update_location(device_info['location'], device_id)
                    
                    logger.debug(f"RFID标签扫描: {tag.tag_id} 在 {device_info['location']}")
            
            # 更新最后扫描时间
            self._rfid_last_collection = datetime.now()
            
            # 清除RFID相关的错误
            self._collection_errors = [err for err in self._collection_errors 
                                     if not err.get('type') == 'rfid']
            
        except Exception as e:
            error_info = {
                'type': 'rfid',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self._collection_errors.append(error_info)
            logger.error(f"RFID设备扫描失败: {e}")
    
    def _start_performance_monitor(self) -> None:
        """启动性能监控"""
        self._stop_performance_monitor_flag = False
        self._performance_monitor_thread = threading.Thread(
            target=self._performance_monitor_worker,
            daemon=True
        )
        self._performance_monitor_thread.start()
    
    def _performance_monitor_worker(self) -> None:
        """性能监控工作线程"""
        while not getattr(self, '_stop_performance_monitor_flag', False):
            try:
                # 获取系统性能信息
                cpu_usage = psutil.cpu_percent(interval=1)
                memory_info = psutil.virtual_memory()
                
                # 记录性能状态
                CollectionStatus.record_status(
                    is_running=self.is_running,
                    sensor_last_collection=self._sensor_last_collection,
                    rfid_last_collection=self._rfid_last_collection,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_info.percent,
                    error_message=self._collection_errors[-1]['message'] if self._collection_errors else None
                )
                
                # 每30秒记录一次
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"性能监控失败: {e}")
                time.sleep(30)
    
    def _record_collection_status(self, is_running: bool, error_message: str = None) -> None:
        """记录采集状态"""
        try:
            CollectionStatus.record_status(
                is_running=is_running,
                sensor_last_collection=self._sensor_last_collection,
                rfid_last_collection=self._rfid_last_collection,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"记录采集状态失败: {e}")
    
    def _get_collection_statistics(self) -> Dict[str, Any]:
        """获取采集统计信息"""
        try:
            # 获取今日采集统计
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # 传感器数据统计
            sensor_count = EnvironmentData.count(
                "timestamp >= ?",
                [today_start.isoformat()]
            )
            
            # RFID扫描统计
            rfid_count = BaseModel.execute_raw_sql(
                "SELECT COUNT(*) as count FROM location_history WHERE timestamp >= ?",
                [today_start.isoformat()],
                fetch_one=True
            )
            
            return {
                'today': {
                    'sensorCollections': sensor_count,
                    'rfidScans': rfid_count['count'] if rfid_count else 0
                },
                'errors': {
                    'total': len(self._collection_errors),
                    'sensor': len([e for e in self._collection_errors if e.get('type') == 'sensor']),
                    'rfid': len([e for e in self._collection_errors if e.get('type') == 'rfid'])
                }
            }
            
        except Exception as e:
            logger.error(f"获取采集统计失败: {e}")
            return {
                'today': {'sensorCollections': 0, 'rfidScans': 0},
                'errors': {'total': 0, 'sensor': 0, 'rfid': 0}
            }
    
    def _on_config_change(self, old_config: Dict, new_config: Dict) -> None:
        """配置变更回调"""
        try:
            if self.is_running:
                # 检查是否需要重新调度
                if (old_config['sensorInterval'] != new_config['sensorInterval'] or
                    old_config['rfidInterval'] != new_config['rfidInterval']):
                    
                    logger.info("检测到配置变更，重新调度采集任务")
                    self._reschedule_collection_jobs(new_config)
                
                # 检查暂停状态变更
                if old_config['isPaused'] != new_config['isPaused']:
                    if new_config['isPaused']:
                        logger.info("配置变更：暂停数据采集")
                        self.stop_collection()
                    else:
                        logger.info("配置变更：恢复数据采集")
                        # 注意：这里不直接启动，因为可能需要外部控制
            
        except Exception as e:
            logger.error(f"处理配置变更失败: {e}")
    
    def _on_status_change(self, status: str, updated_by: str) -> None:
        """状态变更回调"""
        try:
            logger.info(f"采集状态变更: {status} (by {updated_by})")
            
            if status == 'paused' and self.is_running:
                self.stop_collection()
            elif status == 'running' and not self.is_running:
                # 检查配置是否允许启动
                config = self.frequency_service.get_current_config()
                if not config['isPaused']:
                    self.start_collection()
            
        except Exception as e:
            logger.error(f"处理状态变更失败: {e}")
    
    def force_collect_sensor_data(self) -> Dict[str, Any]:
        """强制执行一次传感器数据采集（用于测试）"""
        try:
            self._collect_sensor_data()
            return {
                'success': True,
                'message': '传感器数据采集完成',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'采集失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def force_scan_rfid_devices(self) -> Dict[str, Any]:
        """强制执行一次RFID设备扫描（用于测试）"""
        try:
            self._scan_rfid_devices()
            return {
                'success': True,
                'message': 'RFID设备扫描完成',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'扫描失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }


# 全局采集调度器实例
collection_scheduler = CollectionScheduler()