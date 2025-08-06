#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集频率控制服务单元测试
"""

import unittest
import os
import sys
import tempfile
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.collection_frequency_service import CollectionFrequencyService
from models.collection_config import CollectionConfig, CollectionStatus
from models.base import ValidationError
from database import init_database
from config import Config

class TestCollectionFrequencyService(unittest.TestCase):
    """数据采集频率控制服务测试"""
    
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
        
        # 创建新的服务实例
        self.service = CollectionFrequencyService()
    
    def test_get_current_config_default(self):
        """测试获取默认配置"""
        config = self.service.get_current_config()
        
        self.assertIsInstance(config, dict)
        self.assertEqual(config['sensorInterval'], CollectionConfig.DEFAULT_SENSOR_INTERVAL)
        self.assertEqual(config['rfidInterval'], CollectionConfig.DEFAULT_RFID_INTERVAL)
        self.assertFalse(config['isPaused'])
        self.assertIn('performanceImpact', config)
    
    def test_update_config_valid(self):
        """测试更新有效配置"""
        config_data = {
            'sensorInterval': 60,
            'rfidInterval': 20,
            'isPaused': False
        }
        
        result = self.service.update_config(config_data, 'test_user')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '配置更新成功')
        self.assertEqual(result['config']['sensorInterval'], 60)
        self.assertEqual(result['config']['rfidInterval'], 20)
        self.assertFalse(result['config']['isPaused'])
    
    def test_update_config_invalid_sensor_interval(self):
        """测试更新无效的传感器间隔"""
        config_data = {
            'sensorInterval': 0  # 无效值
        }
        
        result = self.service.update_config(config_data, 'test_user')
        
        self.assertFalse(result['success'])
        self.assertIn('传感器采集间隔必须在', result['message'])
    
    def test_update_config_invalid_rfid_interval(self):
        """测试更新无效的RFID间隔"""
        config_data = {
            'rfidInterval': 100  # 超出范围
        }
        
        result = self.service.update_config(config_data, 'test_user')
        
        self.assertFalse(result['success'])
        self.assertIn('RFID扫描间隔必须在', result['message'])
    
    def test_update_config_invalid_pause_status(self):
        """测试更新无效的暂停状态"""
        config_data = {
            'isPaused': 'invalid'  # 非布尔值
        }
        
        result = self.service.update_config(config_data, 'test_user')
        
        self.assertFalse(result['success'])
        self.assertIn('暂停状态必须是布尔值', result['message'])
    
    def test_pause_collection(self):
        """测试暂停数据采集"""
        # 确保初始状态为运行中
        self.service.resume_collection('test_user')
        
        # 暂停采集
        result = self.service.pause_collection('test_user')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '数据采集已暂停')
        self.assertEqual(result['status'], 'paused')
        
        # 验证配置已更新
        config = self.service.get_current_config()
        self.assertTrue(config['isPaused'])
    
    def test_pause_collection_already_paused(self):
        """测试暂停已暂停的采集"""
        # 先暂停
        self.service.pause_collection('test_user')
        
        # 再次暂停
        result = self.service.pause_collection('test_user')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '数据采集已处于暂停状态')
        self.assertEqual(result['status'], 'paused')
    
    def test_resume_collection(self):
        """测试恢复数据采集"""
        # 先暂停
        self.service.pause_collection('test_user')
        
        # 恢复采集
        result = self.service.resume_collection('test_user')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '数据采集已恢复')
        self.assertEqual(result['status'], 'running')
        
        # 验证配置已更新
        config = self.service.get_current_config()
        self.assertFalse(config['isPaused'])
    
    def test_resume_collection_already_running(self):
        """测试恢复已运行的采集"""
        # 确保初始状态为运行中
        self.service.resume_collection('test_user')
        
        # 再次恢复
        result = self.service.resume_collection('test_user')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '数据采集已在运行中')
        self.assertEqual(result['status'], 'running')
    
    def test_reset_to_default(self):
        """测试重置为默认配置"""
        # 先修改配置
        self.service.update_config({
            'sensorInterval': 120,
            'rfidInterval': 30,
            'isPaused': True
        }, 'test_user')
        
        # 重置为默认配置
        result = self.service.reset_to_default('test_user')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '配置已重置为默认值')
        self.assertEqual(result['config']['sensorInterval'], CollectionConfig.DEFAULT_SENSOR_INTERVAL)
        self.assertEqual(result['config']['rfidInterval'], CollectionConfig.DEFAULT_RFID_INTERVAL)
        self.assertFalse(result['config']['isPaused'])
    
    def test_validate_config_valid(self):
        """测试验证有效配置"""
        config_data = {
            'sensorInterval': 30,
            'rfidInterval': 10,
            'isPaused': False
        }
        
        result = self.service.validate_config(config_data)
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertIn('performanceImpact', result)
    
    def test_validate_config_invalid(self):
        """测试验证无效配置"""
        config_data = {
            'sensorInterval': 'invalid',  # 非整数
            'rfidInterval': 0,            # 超出范围
            'isPaused': 'not_bool'        # 非布尔值
        }
        
        result = self.service.validate_config(config_data)
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)
        self.assertIn('传感器采集间隔必须是整数', result['errors'])
        self.assertIn('RFID扫描间隔不能小于', result['errors'])
        self.assertIn('暂停状态必须是布尔值', result['errors'])
    
    def test_validate_config_warnings(self):
        """测试配置验证警告"""
        config_data = {
            'sensorInterval': 5,  # 过短，应该有警告
            'rfidInterval': 3     # 过短，应该有警告
        }
        
        result = self.service.validate_config(config_data)
        
        self.assertTrue(result['valid'])  # 仍然有效，但有警告
        self.assertGreater(len(result['warnings']), 0)
        self.assertTrue(any('传感器采集间隔过短' in warning for warning in result['warnings']))
        self.assertTrue(any('RFID扫描间隔过短' in warning for warning in result['warnings']))
    
    def test_get_config_history(self):
        """测试获取配置历史"""
        # 创建多个配置记录
        self.service.update_config({'sensorInterval': 30}, 'user1')
        self.service.update_config({'sensorInterval': 60}, 'user2')
        self.service.update_config({'sensorInterval': 90}, 'user3')
        
        # 获取配置历史
        history = self.service.get_config_history(limit=5)
        
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 3)
        
        # 验证历史记录按时间倒序排列
        if len(history) >= 2:
            first_time = datetime.fromisoformat(history[0]['updatedAt'])
            second_time = datetime.fromisoformat(history[1]['updatedAt'])
            self.assertGreaterEqual(first_time, second_time)
    
    def test_get_performance_metrics(self):
        """测试获取性能指标"""
        metrics = self.service.get_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('currentConfig', metrics)
        self.assertIn('performanceImpact', metrics)
        self.assertIn('recommendedConfig', metrics)
        self.assertIn('timestamp', metrics)
        
        # 验证当前配置信息
        current_config = metrics['currentConfig']
        self.assertIn('sensorInterval', current_config)
        self.assertIn('rfidInterval', current_config)
        self.assertIn('isPaused', current_config)
    
    def test_export_config(self):
        """测试导出配置"""
        # 设置特定配置
        self.service.update_config({
            'sensorInterval': 45,
            'rfidInterval': 15
        }, 'test_user')
        
        # 导出配置
        config_json = self.service.export_config()
        
        self.assertIsInstance(config_json, str)
        
        # 验证JSON格式
        config_data = json.loads(config_json)
        self.assertEqual(config_data['sensorInterval'], 45)
        self.assertEqual(config_data['rfidInterval'], 15)
    
    def test_import_config_valid(self):
        """测试导入有效配置"""
        config_data = {
            'sensorInterval': 75,
            'rfidInterval': 25,
            'isPaused': False
        }
        config_json = json.dumps(config_data)
        
        result = self.service.import_config(config_json, 'test_user')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['config']['sensorInterval'], 75)
        self.assertEqual(result['config']['rfidInterval'], 25)
    
    def test_import_config_invalid_json(self):
        """测试导入无效JSON"""
        invalid_json = "{ invalid json }"
        
        result = self.service.import_config(invalid_json, 'test_user')
        
        self.assertFalse(result['success'])
        self.assertIn('配置格式错误', result['message'])
    
    def test_import_config_invalid_data(self):
        """测试导入无效配置数据"""
        config_data = {
            'sensorInterval': 0,  # 无效值
            'rfidInterval': 100   # 超出范围
        }
        config_json = json.dumps(config_data)
        
        result = self.service.import_config(config_json, 'test_user')
        
        self.assertFalse(result['success'])
        self.assertIn('配置验证失败', result['message'])
    
    def test_callback_registration(self):
        """测试回调函数注册"""
        config_change_called = False
        status_change_called = False
        
        def config_change_callback(old_config, new_config):
            nonlocal config_change_called
            config_change_called = True
        
        def status_change_callback(status, updated_by):
            nonlocal status_change_called
            status_change_called = True
        
        # 注册回调函数
        self.service.add_config_change_callback(config_change_callback)
        self.service.add_status_change_callback(status_change_callback)
        
        # 触发配置变更
        self.service.update_config({'sensorInterval': 45}, 'test_user')
        
        # 触发状态变更
        self.service.pause_collection('test_user')
        
        # 验证回调函数被调用
        self.assertTrue(config_change_called)
        self.assertTrue(status_change_called)
    
    def test_concurrent_access(self):
        """测试并发访问"""
        import threading
        import time
        
        results = []
        
        def update_config_worker(interval):
            result = self.service.update_config({
                'sensorInterval': interval
            }, f'worker_{interval}')
            results.append(result)
        
        # 创建多个线程同时更新配置
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_config_worker, args=(30 + i * 10,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有操作都成功
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertTrue(result['success'])
        
        # 验证最终配置是有效的
        final_config = self.service.get_current_config()
        self.assertIn(final_config['sensorInterval'], [30, 40, 50, 60, 70])


if __name__ == '__main__':
    unittest.main()