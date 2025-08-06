#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集调度器单元测试
"""

import unittest
import os
import sys
import tempfile
import time
from datetime import datetime
from unittest.mock import Mock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.collection_scheduler import CollectionScheduler
from services.collection_frequency_service import CollectionFrequencyService
from models.collection_config import CollectionConfig, CollectionStatus
from models.environment import EnvironmentData
from database import init_database
from config import Config

class TestCollectionScheduler(unittest.TestCase):
    """数据采集调度器测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        # 创建临时数据库
        cls.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.temp_db.close()
        
        # 设置测试数据库路径
        Config.DATABASE_PATH = cls.temp_db.name
        
        # 初始化测试数据库
        init_database()
    
    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        # 删除临时数据库文件
        if os.path.exists(cls.temp_db.name):
            os.unlink(cls.temp_db.name)
    
    def setUp(self):
        """每个测试前的准备"""
        # 清空相关表
        CollectionConfig.execute_raw_sql("DELETE FROM collection_configs")
        CollectionStatus.execute_raw_sql("DELETE FROM collection_status")
        EnvironmentData.execute_raw_sql("DELETE FROM environment_data")
        
        # 创建新的服务实例
        self.frequency_service = CollectionFrequencyService()
        self.scheduler = CollectionScheduler(self.frequency_service)
    
    def tearDown(self):
        """每个测试后的清理"""
        # 确保调度器停止
        if self.scheduler.is_running:
            self.scheduler.stop_collection()
        time.sleep(0.1)  # 等待停止完成
    
    def test_start_collection_success(self):
        """测试成功启动数据采集"""
        result = self.scheduler.start_collection()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '数据采集启动成功')
        self.assertEqual(result['status'], 'running')
        self.assertTrue(self.scheduler.is_running)
        
        # 验证配置信息
        self.assertIn('config', result)
        config = result['config']
        self.assertIn('sensorInterval', config)
        self.assertIn('rfidInterval', config)
    
    def test_start_collection_already_running(self):
        """测试启动已运行的采集"""
        # 先启动
        self.scheduler.start_collection()
        
        # 再次启动
        result = self.scheduler.start_collection()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '数据采集已在运行中')
        self.assertEqual(result['status'], 'running')
    
    def test_start_collection_when_paused(self):
        """测试在暂停状态下启动采集"""
        # 暂停采集
        self.frequency_service.pause_collection('test_user')
        
        # 尝试启动
        result = self.scheduler.start_collection()
        
        self.assertFalse(result['success'])
        self.assertIn('数据采集已暂停', result['message'])
        self.assertEqual(result['status'], 'paused')
        self.assertFalse(self.scheduler.is_running)
    
    def test_stop_collection_success(self):
        """测试成功停止数据采集"""
        # 先启动
        self.scheduler.start_collection()
        
        # 停止采集
        result = self.scheduler.stop_collection()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '数据采集已停止')
        self.assertEqual(result['status'], 'stopped')
        self.assertFalse(self.scheduler.is_running)
    
    def test_stop_collection_already_stopped(self):
        """测试停止已停止的采集"""
        result = self.scheduler.stop_collection()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '数据采集已停止')
        self.assertEqual(result['status'], 'stopped')
    
    def test_update_intervals_success(self):
        """测试成功更新采集间隔"""
        # 先启动采集
        self.scheduler.start_collection()
        
        # 更新间隔
        result = self.scheduler.update_intervals(sensor_interval=60, rfid_interval=20)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '采集间隔更新成功')
        self.assertEqual(result['status'], 'running')
        
        # 验证配置已更新
        config = result['config']
        self.assertEqual(config['sensorInterval'], 60)
        self.assertEqual(config['rfidInterval'], 20)
    
    def test_update_intervals_not_running(self):
        """测试在未运行状态下更新间隔"""
        result = self.scheduler.update_intervals(sensor_interval=60)
        
        self.assertFalse(result['success'])
        self.assertIn('数据采集未运行', result['message'])
        self.assertEqual(result['status'], 'stopped')
    
    def test_update_intervals_invalid_values(self):
        """测试更新无效的间隔值"""
        # 先启动采集
        self.scheduler.start_collection()
        
        # 尝试设置无效值
        result = self.scheduler.update_intervals(sensor_interval=0)
        
        self.assertFalse(result['success'])
        self.assertIn('传感器采集间隔必须在', result['message'])
    
    def test_get_status(self):
        """测试获取采集状态"""
        # 启动采集
        self.scheduler.start_collection()
        
        # 获取状态
        status = self.scheduler.get_status()
        
        self.assertIsInstance(status, dict)
        self.assertTrue(status['isRunning'])
        self.assertFalse(status['isPaused'])
        
        # 验证状态信息结构
        self.assertIn('currentConfig', status)
        self.assertIn('lastCollection', status)
        self.assertIn('performance', status)
        self.assertIn('errors', status)
        self.assertIn('statistics', status)
        self.assertIn('timestamp', status)
        
        # 验证配置信息
        config = status['currentConfig']
        self.assertIn('sensorInterval', config)
        self.assertIn('rfidInterval', config)
        
        # 验证性能信息
        performance = status['performance']
        self.assertIn('cpuUsage', performance)
        self.assertIn('memoryUsage', performance)
        self.assertIn('memoryUsedMB', performance)
    
    def test_get_status_when_stopped(self):
        """测试获取停止状态"""
        status = self.scheduler.get_status()
        
        self.assertFalse(status['isRunning'])
        self.assertIn('timestamp', status)
    
    @patch('services.collection_scheduler.psutil.cpu_percent')
    @patch('services.collection_scheduler.psutil.virtual_memory')
    def test_performance_monitoring(self, mock_memory, mock_cpu):
        """测试性能监控"""
        # 模拟系统性能数据
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(percent=60.0, used=1024*1024*512)  # 512MB
        
        # 启动采集
        self.scheduler.start_collection()
        
        # 等待性能监控运行
        time.sleep(0.1)
        
        # 获取状态
        status = self.scheduler.get_status()
        
        # 验证性能数据
        performance = status['performance']
        self.assertEqual(performance['cpuUsage'], 25.5)
        self.assertEqual(performance['memoryUsage'], 60.0)
        self.assertEqual(performance['memoryUsedMB'], 512.0)
    
    def test_force_collect_sensor_data(self):
        """测试强制采集传感器数据"""
        result = self.scheduler.force_collect_sensor_data()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '传感器数据采集完成')
        self.assertIn('timestamp', result)
        
        # 验证数据已保存到数据库
        sensor_data = EnvironmentData.find_all(limit=1)
        self.assertGreater(len(sensor_data), 0)
    
    def test_force_scan_rfid_devices(self):
        """测试强制扫描RFID设备"""
        result = self.scheduler.force_scan_rfid_devices()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'RFID设备扫描完成')
        self.assertIn('timestamp', result)
    
    def test_config_change_callback(self):
        """测试配置变更回调"""
        # 启动采集
        self.scheduler.start_collection()
        
        # 获取初始配置
        initial_status = self.scheduler.get_status()
        initial_sensor_interval = initial_status['currentConfig']['sensorInterval']
        
        # 通过频率服务更新配置
        self.frequency_service.update_config({
            'sensorInterval': initial_sensor_interval + 30
        }, 'test_user')
        
        # 等待回调处理
        time.sleep(0.1)
        
        # 验证配置已更新
        updated_status = self.scheduler.get_status()
        updated_sensor_interval = updated_status['currentConfig']['sensorInterval']
        
        self.assertEqual(updated_sensor_interval, initial_sensor_interval + 30)
    
    def test_status_change_callback_pause(self):
        """测试状态变更回调 - 暂停"""
        # 启动采集
        self.scheduler.start_collection()
        self.assertTrue(self.scheduler.is_running)
        
        # 通过频率服务暂停采集
        self.frequency_service.pause_collection('test_user')
        
        # 等待回调处理
        time.sleep(0.1)
        
        # 验证采集已停止
        self.assertFalse(self.scheduler.is_running)
    
    def test_status_change_callback_resume(self):
        """测试状态变更回调 - 恢复"""
        # 先暂停采集
        self.frequency_service.pause_collection('test_user')
        
        # 确保调度器未运行
        self.assertFalse(self.scheduler.is_running)
        
        # 通过频率服务恢复采集
        self.frequency_service.resume_collection('test_user')
        
        # 等待回调处理
        time.sleep(0.1)
        
        # 验证采集已启动
        self.assertTrue(self.scheduler.is_running)
    
    def test_collection_statistics(self):
        """测试采集统计信息"""
        # 强制采集一些数据
        self.scheduler.force_collect_sensor_data()
        self.scheduler.force_scan_rfid_devices()
        
        # 获取状态
        status = self.scheduler.get_status()
        
        # 验证统计信息
        statistics = status['statistics']
        self.assertIn('today', statistics)
        self.assertIn('errors', statistics)
        
        today_stats = statistics['today']
        self.assertIn('sensorCollections', today_stats)
        self.assertIn('rfidScans', today_stats)
        
        error_stats = statistics['errors']
        self.assertIn('total', error_stats)
        self.assertIn('sensor', error_stats)
        self.assertIn('rfid', error_stats)
    
    def test_error_handling_sensor_collection(self):
        """测试传感器采集错误处理"""
        # 模拟传感器采集错误
        with patch.object(self.scheduler, 'mock_sensors', {}):
            # 这会导致采集时没有传感器数据
            result = self.scheduler.force_collect_sensor_data()
            
            # 验证仍然返回成功（因为没有传感器不算错误）
            self.assertTrue(result['success'])
    
    def test_error_handling_rfid_scanning(self):
        """测试RFID扫描错误处理"""
        # 模拟RFID扫描错误
        with patch('models.rfid.RfidTag.get_active_tags', side_effect=Exception('模拟错误')):
            result = self.scheduler.force_scan_rfid_devices()
            
            # 验证错误被正确处理
            self.assertFalse(result['success'])
            self.assertIn('扫描失败', result['message'])
    
    def test_concurrent_operations(self):
        """测试并发操作"""
        import threading
        
        results = []
        
        def start_stop_worker():
            # 启动和停止采集
            start_result = self.scheduler.start_collection()
            time.sleep(0.05)
            stop_result = self.scheduler.stop_collection()
            results.append((start_result, stop_result))
        
        def update_config_worker():
            # 更新配置
            time.sleep(0.02)
            if self.scheduler.is_running:
                update_result = self.scheduler.update_intervals(sensor_interval=45)
                results.append(update_result)
        
        # 创建多个线程
        threads = []
        for i in range(3):
            if i == 0:
                thread = threading.Thread(target=start_stop_worker)
            else:
                thread = threading.Thread(target=update_config_worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有崩溃
        self.assertGreater(len(results), 0)


if __name__ == '__main__':
    unittest.main()