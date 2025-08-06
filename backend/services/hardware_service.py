#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硬件通信服务
处理传感器和RFID设备的通信
"""

import json
import logging
import random
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from models.environment import EnvironmentData
from models.rfid import RfidDevice, RfidTag
from models.archive import Archive, LocationHistory
from config import Config

logger = logging.getLogger(__name__)

class HardwareService:
    """硬件通信服务类"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.sensor_callbacks = []
        self.rfid_callbacks = []
        self._lock = threading.Lock()
        
        # 模拟传感器数据（用于演示）
        self.mock_sensors = {
            'SENSOR_001': {'location': '档案室A区', 'base_temp': 22.0, 'base_humidity': 50.0, 'base_light': 300.0},
            'SENSOR_002': {'location': '档案室B区', 'base_temp': 21.5, 'base_humidity': 48.0, 'base_light': 280.0},
            'SENSOR_003': {'location': '档案室C区', 'base_temp': 23.0, 'base_humidity': 52.0, 'base_light': 320.0}
        }
        
        # 模拟RFID设备
        self.mock_rfid_devices = {
            1: {'name': 'RFID_READER_001', 'location': '档案室入口', 'status': 'online'},
            2: {'name': 'RFID_READER_002', 'location': '档案室出口', 'status': 'online'}
        }
    
    def start(self):
        """启动硬件服务"""
        if self.is_running:
            logger.warning("硬件服务已在运行中")
            return
        
        try:
            # 检查采集配置是否暂停
            from models.collection_config import CollectionConfig
            config = CollectionConfig.get_or_create_default()
            
            if config.is_paused:
                logger.info("数据采集已暂停，硬件服务启动但不执行采集任务")
                self.scheduler.start()
                self.is_running = True
                return
            
            # 启动传感器数据采集
            self.scheduler.add_job(
                func=self._collect_sensor_data,
                trigger="interval",
                seconds=Config.SENSOR_SCAN_INTERVAL,
                id='sensor_collection',
                replace_existing=True
            )
            
            # 启动RFID设备扫描
            self.scheduler.add_job(
                func=self._scan_rfid_devices,
                trigger="interval",
                seconds=Config.RFID_SCAN_INTERVAL,
                id='rfid_scanning',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info("硬件服务启动成功")
            
        except Exception as e:
            logger.error(f"硬件服务启动失败: {e}")
            raise
    
    def stop(self):
        """停止硬件服务"""
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("硬件服务已停止")
            
        except Exception as e:
            logger.error(f"硬件服务停止失败: {e}")
    
    def add_sensor_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """添加传感器数据回调函数"""
        with self._lock:
            self.sensor_callbacks.append(callback)
    
    def add_rfid_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """添加RFID扫描回调函数"""
        with self._lock:
            self.rfid_callbacks.append(callback)
    
    def _collect_sensor_data(self):
        """采集传感器数据"""
        try:
            # 检查采集是否暂停
            from models.collection_config import CollectionConfig
            config = CollectionConfig.get_or_create_default()
            if config.is_paused:
                logger.debug("数据采集已暂停，跳过传感器数据采集")
                return
            for sensor_id, sensor_info in self.mock_sensors.items():
                # 生成模拟数据（在基础值附近波动）
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
                try:
                    EnvironmentData.create(**sensor_data)
                    logger.debug(f"传感器数据采集成功: {sensor_id}")
                    
                    # 调用回调函数
                    self._notify_sensor_callbacks(sensor_data)
                    
                    # 检查阈值告警
                    self._check_environment_alerts(sensor_data)
                    
                except Exception as e:
                    logger.error(f"保存传感器数据失败: {e}")
            
        except Exception as e:
            logger.error(f"传感器数据采集失败: {e}")
    
    def _scan_rfid_devices(self):
        """扫描RFID设备"""
        try:
            # 检查采集是否暂停
            from models.collection_config import CollectionConfig
            config = CollectionConfig.get_or_create_default()
            if config.is_paused:
                logger.debug("数据采集已暂停，跳过RFID设备扫描")
                return
            # 模拟RFID标签扫描（随机扫描到一些标签）
            if random.random() < 0.3:  # 30%概率扫描到标签
                # 获取活跃的标签
                active_tags = RfidTag.get_active_tags()
                if active_tags:
                    # 随机选择一个标签
                    tag = random.choice(active_tags)
                    device_id = random.choice(list(self.mock_rfid_devices.keys()))
                    device_info = self.mock_rfid_devices[device_id]
                    
                    scan_data = {
                        'tag_id': tag.tag_id,
                        'device_id': device_id,
                        'device_name': device_info['name'],
                        'location': device_info['location'],
                        'timestamp': datetime.now().isoformat(),
                        'signal_strength': random.randint(-60, -30)  # dBm
                    }
                    
                    # 更新标签位置
                    try:
                        tag.update_location(device_info['location'], device_id)
                        logger.debug(f"RFID标签扫描: {tag.tag_id} 在 {device_info['location']}")
                        
                        # 调用回调函数
                        self._notify_rfid_callbacks(scan_data)
                        
                        # 检查异常移动
                        self._check_movement_alerts(tag, scan_data)
                        
                    except Exception as e:
                        logger.error(f"更新RFID标签位置失败: {e}")
            
        except Exception as e:
            logger.error(f"RFID设备扫描失败: {e}")
    
    def _notify_sensor_callbacks(self, sensor_data: Dict[str, Any]):
        """通知传感器数据回调函数"""
        with self._lock:
            for callback in self.sensor_callbacks:
                try:
                    callback(sensor_data)
                except Exception as e:
                    logger.error(f"传感器回调函数执行失败: {e}")
    
    def _notify_rfid_callbacks(self, scan_data: Dict[str, Any]):
        """通知RFID扫描回调函数"""
        with self._lock:
            for callback in self.rfid_callbacks:
                try:
                    callback(scan_data)
                except Exception as e:
                    logger.error(f"RFID回调函数执行失败: {e}")
    
    def _check_environment_alerts(self, sensor_data: Dict[str, Any]):
        """检查环境告警"""
        try:
            # 获取阈值配置
            from models.base import BaseModel
            
            config_sql = """
                SELECT config_key, config_value 
                FROM system_config 
                WHERE config_key IN (
                    'temp_min_threshold', 'temp_max_threshold',
                    'humidity_min_threshold', 'humidity_max_threshold',
                    'light_min_threshold', 'light_max_threshold'
                )
            """
            
            config_data = BaseModel.execute_raw_sql(config_sql, [], fetch_one=False, fetch_all=True)
            
            # 构建阈值字典
            thresholds = {}
            for config in config_data:
                key = config['config_key']
                value = float(config['config_value'])
                
                if 'temp_' in key:
                    if 'temperature' not in thresholds:
                        thresholds['temperature'] = {}
                    if 'min' in key:
                        thresholds['temperature']['min'] = value
                    else:
                        thresholds['temperature']['max'] = value
                elif 'humidity_' in key:
                    if 'humidity' not in thresholds:
                        thresholds['humidity'] = {}
                    if 'min' in key:
                        thresholds['humidity']['min'] = value
                    else:
                        thresholds['humidity']['max'] = value
                elif 'light_' in key:
                    if 'light_intensity' not in thresholds:
                        thresholds['light_intensity'] = {}
                    if 'min' in key:
                        thresholds['light_intensity']['min'] = value
                    else:
                        thresholds['light_intensity']['max'] = value
            
            # 创建临时环境数据对象进行检查
            temp_data = EnvironmentData(**sensor_data)
            alerts = temp_data.check_all_thresholds(thresholds)
            
            # 如果有告警，创建告警记录
            if alerts:
                from models.alert import Alert
                for alert_message in alerts:
                    Alert.create(
                        alert_type='environment',
                        level='warning',
                        title=f'环境异常告警 - {sensor_data["sensor_id"]}',
                        message=alert_message,
                        source_id=sensor_data['sensor_id'],
                        source_type='sensor'
                    )
                    logger.warning(f"环境告警: {alert_message}")
            
        except Exception as e:
            logger.error(f"环境告警检查失败: {e}")
    
    def _check_movement_alerts(self, tag: RfidTag, scan_data: Dict[str, Any]):
        """检查移动告警"""
        try:
            # 检查是否是异常时间的移动（例如非工作时间）
            current_hour = datetime.now().hour
            if current_hour < 8 or current_hour > 18:  # 非工作时间
                # 如果标签关联了档案，创建异常移动告警
                if tag.archive_id:
                    archive = Archive.find_one("archive_code = ?", [tag.archive_id])
                    if archive:
                        from models.alert import Alert
                        Alert.create(
                            alert_type='movement',
                            level='warning',
                            title=f'非工作时间档案移动 - {archive.archive_code}',
                            message=f'档案"{archive.title}"在非工作时间({current_hour}:00)被扫描到，位置：{scan_data["location"]}',
                            source_id=str(archive.id),
                            source_type='archive'
                        )
                        logger.warning(f"异常移动告警: 档案{archive.archive_code}在非工作时间移动")
            
        except Exception as e:
            logger.error(f"移动告警检查失败: {e}")
    
    def get_sensor_status(self) -> Dict[str, Any]:
        """获取传感器状态"""
        try:
            sensor_status = {}
            
            for sensor_id, sensor_info in self.mock_sensors.items():
                # 获取最新数据
                latest_data = EnvironmentData.get_current_data(sensor_id)
                
                if latest_data:
                    # 检查数据是否新鲜（5分钟内）
                    data_time = datetime.fromisoformat(latest_data.timestamp)
                    time_diff = datetime.now() - data_time
                    is_online = time_diff.total_seconds() < 300  # 5分钟
                    
                    sensor_status[sensor_id] = {
                        'location': sensor_info['location'],
                        'status': 'online' if is_online else 'offline',
                        'last_update': latest_data.timestamp,
                        'temperature': latest_data.temperature,
                        'humidity': latest_data.humidity,
                        'light_intensity': latest_data.light_intensity
                    }
                else:
                    sensor_status[sensor_id] = {
                        'location': sensor_info['location'],
                        'status': 'offline',
                        'last_update': None,
                        'temperature': None,
                        'humidity': None,
                        'light_intensity': None
                    }
            
            return sensor_status
            
        except Exception as e:
            logger.error(f"获取传感器状态失败: {e}")
            return {}
    
    def get_rfid_device_status(self) -> Dict[str, Any]:
        """获取RFID设备状态"""
        try:
            device_status = {}
            
            for device_id, device_info in self.mock_rfid_devices.items():
                # 获取设备最近的扫描记录
                recent_scans = LocationHistory.get_device_activities(device_id, limit=1)
                
                if recent_scans:
                    last_scan = recent_scans[0]
                    scan_time = datetime.fromisoformat(last_scan.timestamp)
                    time_diff = datetime.now() - scan_time
                    is_online = time_diff.total_seconds() < 600  # 10分钟内有扫描记录
                    
                    device_status[device_id] = {
                        'name': device_info['name'],
                        'location': device_info['location'],
                        'status': 'online' if is_online else 'offline',
                        'last_scan': last_scan.timestamp,
                        'scan_count_today': self._get_today_scan_count(device_id)
                    }
                else:
                    device_status[device_id] = {
                        'name': device_info['name'],
                        'location': device_info['location'],
                        'status': 'offline',
                        'last_scan': None,
                        'scan_count_today': 0
                    }
            
            return device_status
            
        except Exception as e:
            logger.error(f"获取RFID设备状态失败: {e}")
            return {}
    
    def _get_today_scan_count(self, device_id: int) -> int:
        """获取今日扫描次数"""
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            count = LocationHistory.count(
                "rfid_device_id = ? AND timestamp >= ?",
                [device_id, today_start.isoformat()]
            )
            return count
        except Exception as e:
            logger.error(f"获取今日扫描次数失败: {e}")
            return 0
    
    def simulate_tag_scan(self, tag_id: str, device_id: int) -> bool:
        """模拟标签扫描（用于测试）"""
        try:
            tag = RfidTag.find_by_tag_id(tag_id)
            if not tag:
                logger.error(f"标签 {tag_id} 不存在")
                return False
            
            if device_id not in self.mock_rfid_devices:
                logger.error(f"设备 {device_id} 不存在")
                return False
            
            device_info = self.mock_rfid_devices[device_id]
            
            # 更新标签位置
            tag.update_location(device_info['location'], device_id)
            
            scan_data = {
                'tag_id': tag_id,
                'device_id': device_id,
                'device_name': device_info['name'],
                'location': device_info['location'],
                'timestamp': datetime.now().isoformat(),
                'signal_strength': random.randint(-60, -30)
            }
            
            # 通知回调函数
            self._notify_rfid_callbacks(scan_data)
            
            logger.info(f"模拟标签扫描成功: {tag_id} 在 {device_info['location']}")
            return True
            
        except Exception as e:
            logger.error(f"模拟标签扫描失败: {e}")
            return False
    
    def add_mock_sensor_data(self, sensor_id: str, temperature: float, 
                           humidity: float, light_intensity: float, location: str = None) -> bool:
        """添加模拟传感器数据（用于测试）"""
        try:
            sensor_data = {
                'sensor_id': sensor_id,
                'temperature': temperature,
                'humidity': humidity,
                'light_intensity': light_intensity,
                'location': location or f'{sensor_id}_位置',
                'timestamp': datetime.now().isoformat()
            }
            
            EnvironmentData.create(**sensor_data)
            
            # 通知回调函数
            self._notify_sensor_callbacks(sensor_data)
            
            logger.info(f"添加模拟传感器数据成功: {sensor_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加模拟传感器数据失败: {e}")
            return False


# 全局硬件服务实例
hardware_service = HardwareService()