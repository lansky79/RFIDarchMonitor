#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据采集配置模型单元测试
"""

import unittest
import os
import sys
import tempfile
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.collection_config import CollectionConfig, CollectionStatus
from models.base import ValidationError
from database import init_database
from config import Config

class TestCollectionConfig(unittest.TestCase):
    """数据采集配置模型测试"""
    
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
        # 清空配置表
        CollectionConfig.execute_raw_sql("DELETE FROM collection_configs")
        CollectionStatus.execute_raw_sql("DELETE FROM collection_status")
    
    def test_create_default_config(self):
        """测试创建默认配置"""
        config = CollectionConfig()
        
        self.assertEqual(config.sensor_interval, CollectionConfig.DEFAULT_SENSOR_INTERVAL)
        self.assertEqual(config.rfid_interval, CollectionConfig.DEFAULT_RFID_INTERVAL)
        self.assertFalse(config.is_paused)
        self.assertEqual(config.updated_by, 'system')
    
    def test_create_custom_config(self):
        """测试创建自定义配置"""
        config = CollectionConfig(
            sensor_interval=60,
            rfid_interval=20,
            is_paused=True,
            updated_by='admin'
        )
        
        self.assertEqual(config.sensor_interval, 60)
        self.assertEqual(config.rfid_interval, 20)
        self.assertTrue(config.is_paused)
        self.assertEqual(config.updated_by, 'admin')
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试有效配置
        config = CollectionConfig(sensor_interval=30, rfid_interval=10)
        config.validate()  # 应该不抛出异常
        
        # 测试传感器间隔超出范围
        config = CollectionConfig(sensor_interval=0)
        with self.assertRaises(ValidationError):
            config.validate()
        
        config = CollectionConfig(sensor_interval=400)
        with self.assertRaises(ValidationError):
            config.validate()
        
        # 测试RFID间隔超出范围
        config = CollectionConfig(rfid_interval=0)
        with self.assertRaises(ValidationError):
            config.validate()
        
        config = CollectionConfig(rfid_interval=100)
        with self.assertRaises(ValidationError):
            config.validate()
        
        # 测试无效的布尔值
        config = CollectionConfig(is_paused="invalid")
        with self.assertRaises(ValidationError):
            config.validate()
    
    def test_save_and_retrieve_config(self):
        """测试保存和检索配置"""
        # 创建并保存配置
        config = CollectionConfig.create(
            sensor_interval=45,
            rfid_interval=15,
            is_paused=False,
            updated_by='test_user'
        )
        
        self.assertIsNotNone(config.id)
        
        # 根据ID检索配置
        retrieved_config = CollectionConfig.find_by_id(config.id)
        self.assertIsNotNone(retrieved_config)
        self.assertEqual(retrieved_config.sensor_interval, 45)
        self.assertEqual(retrieved_config.rfid_interval, 15)
        self.assertFalse(retrieved_config.is_paused)
        self.assertEqual(retrieved_config.updated_by, 'test_user')
    
    def test_get_current_config(self):
        """测试获取当前配置"""
        # 初始状态应该没有配置
        current_config = CollectionConfig.get_current_config()
        self.assertIsNone(current_config)
        
        # 创建配置
        config1 = CollectionConfig.create(sensor_interval=30, updated_by='user1')
        
        # 获取当前配置
        current_config = CollectionConfig.get_current_config()
        self.assertIsNotNone(current_config)
        self.assertEqual(current_config.id, config1.id)
        
        # 创建更新的配置
        config2 = CollectionConfig.create(sensor_interval=60, updated_by='user2')
        
        # 获取当前配置应该是最新的
        current_config = CollectionConfig.get_current_config()
        self.assertEqual(current_config.id, config2.id)
        self.assertEqual(current_config.sensor_interval, 60)
    
    def test_get_or_create_default(self):
        """测试获取或创建默认配置"""
        # 第一次调用应该创建默认配置
        config = CollectionConfig.get_or_create_default()
        self.assertIsNotNone(config)
        self.assertEqual(config.sensor_interval, CollectionConfig.DEFAULT_SENSOR_INTERVAL)
        self.assertEqual(config.rfid_interval, CollectionConfig.DEFAULT_RFID_INTERVAL)
        
        # 第二次调用应该返回相同的配置
        config2 = CollectionConfig.get_or_create_default()
        self.assertEqual(config.id, config2.id)
    
    def test_update_config(self):
        """测试更新配置"""
        config = CollectionConfig.create(sensor_interval=30, rfid_interval=10)
        original_id = config.id
        
        # 更新配置
        success = config.update_config(
            sensor_interval=60,
            rfid_interval=20,
            updated_by='admin'
        )
        
        self.assertTrue(success)
        self.assertEqual(config.id, original_id)  # ID不应该改变
        self.assertEqual(config.sensor_interval, 60)
        self.assertEqual(config.rfid_interval, 20)
        self.assertEqual(config.updated_by, 'admin')
    
    def test_pause_resume_collection(self):
        """测试暂停和恢复采集"""
        config = CollectionConfig.create(is_paused=False)
        
        # 暂停采集
        success = config.pause_collection('admin')
        self.assertTrue(success)
        self.assertTrue(config.is_paused)
        self.assertEqual(config.updated_by, 'admin')
        
        # 恢复采集
        success = config.resume_collection('admin')
        self.assertTrue(success)
        self.assertFalse(config.is_paused)
    
    def test_reset_to_default(self):
        """测试重置为默认配置"""
        config = CollectionConfig.create(
            sensor_interval=120,
            rfid_interval=30,
            is_paused=True
        )
        
        # 重置为默认配置
        success = config.reset_to_default('admin')
        self.assertTrue(success)
        self.assertEqual(config.sensor_interval, CollectionConfig.DEFAULT_SENSOR_INTERVAL)
        self.assertEqual(config.rfid_interval, CollectionConfig.DEFAULT_RFID_INTERVAL)
        self.assertFalse(config.is_paused)
        self.assertEqual(config.updated_by, 'admin')
    
    def test_performance_impact(self):
        """测试性能影响计算"""
        config = CollectionConfig(sensor_interval=30, rfid_interval=10)
        impact = config.get_performance_impact()
        
        self.assertIn('sensorLoad', impact)
        self.assertIn('rfidLoad', impact)
        self.assertIn('totalLoad', impact)
        self.assertIn('estimatedCpuUsage', impact)
        self.assertIn('estimatedMemoryMB', impact)
        self.assertIn('performanceLevel', impact)
        
        # 验证计算结果
        expected_sensor_load = 60 / 30  # 2次/分钟
        expected_rfid_load = 60 / 10    # 6次/分钟
        
        self.assertEqual(impact['sensorLoad'], expected_sensor_load)
        self.assertEqual(impact['rfidLoad'], expected_rfid_load)
        self.assertEqual(impact['totalLoad'], expected_sensor_load + expected_rfid_load)
    
    def test_recommended_config(self):
        """测试推荐配置"""
        config = CollectionConfig()
        recommended = config.get_recommended_config()
        
        self.assertIn('sensorInterval', recommended)
        self.assertIn('rfidInterval', recommended)
        self.assertIn('reason', recommended)
        
        # 推荐值应该在有效范围内
        self.assertGreaterEqual(recommended['sensorInterval'], CollectionConfig.MIN_SENSOR_INTERVAL)
        self.assertLessEqual(recommended['sensorInterval'], CollectionConfig.MAX_SENSOR_INTERVAL)
        self.assertGreaterEqual(recommended['rfidInterval'], CollectionConfig.MIN_RFID_INTERVAL)
        self.assertLessEqual(recommended['rfidInterval'], CollectionConfig.MAX_RFID_INTERVAL)
    
    def test_to_api_dict(self):
        """测试API字典转换"""
        config = CollectionConfig.create(
            sensor_interval=45,
            rfid_interval=15,
            is_paused=True,
            updated_by='test_user'
        )
        
        api_dict = config.to_api_dict()
        
        self.assertEqual(api_dict['sensorInterval'], 45)
        self.assertEqual(api_dict['rfidInterval'], 15)
        self.assertTrue(api_dict['isPaused'])
        self.assertEqual(api_dict['updatedBy'], 'test_user')
        self.assertIn('performanceImpact', api_dict)
    
    def test_config_history(self):
        """测试配置历史"""
        # 创建多个配置记录
        config1 = CollectionConfig.create(sensor_interval=30, updated_by='user1')
        config2 = CollectionConfig.create(sensor_interval=60, updated_by='user2')
        config3 = CollectionConfig.create(sensor_interval=90, updated_by='user3')
        
        # 获取配置历史
        history = CollectionConfig.get_config_history(limit=5)
        
        self.assertEqual(len(history), 3)
        # 应该按更新时间倒序排列
        self.assertEqual(history[0].id, config3.id)
        self.assertEqual(history[1].id, config2.id)
        self.assertEqual(history[2].id, config1.id)


class TestCollectionStatus(unittest.TestCase):
    """数据采集状态模型测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        # 使用与配置测试相同的数据库
        pass
    
    def setUp(self):
        """每个测试前的准备"""
        # 清空状态表（如果表存在的话）
        try:
            CollectionStatus.execute_raw_sql("DELETE FROM collection_status")
        except Exception:
            # 如果表不存在，重新初始化数据库
            init_database()
    
    def test_create_default_status(self):
        """测试创建默认状态"""
        status = CollectionStatus()
        
        self.assertFalse(status.is_running)
        self.assertIsNotNone(status.data.get('timestamp'))
    
    def test_create_custom_status(self):
        """测试创建自定义状态"""
        now = datetime.now()
        status = CollectionStatus(
            is_running=True,
            sensor_last_collection=now.isoformat(),
            rfid_last_collection=now.isoformat(),
            cpu_usage=25.5,
            memory_usage=128.0,
            error_message="测试错误"
        )
        
        self.assertTrue(status.is_running)
        self.assertEqual(status.data.get('sensor_last_collection'), now.isoformat())
        self.assertEqual(status.data.get('rfid_last_collection'), now.isoformat())
        self.assertEqual(status.data.get('cpu_usage'), 25.5)
        self.assertEqual(status.data.get('memory_usage'), 128.0)
        self.assertEqual(status.data.get('error_message'), "测试错误")
    
    def test_status_validation(self):
        """测试状态验证"""
        # 测试有效状态
        status = CollectionStatus(is_running=True, cpu_usage=50.0)
        status.validate()  # 应该不抛出异常
        
        # 测试无效的布尔值
        status = CollectionStatus(is_running="invalid")
        with self.assertRaises(ValidationError):
            status.validate()
        
        # 测试CPU使用率超出范围
        status = CollectionStatus(is_running=True, cpu_usage=150.0)
        with self.assertRaises(ValidationError):
            status.validate()
        
        status = CollectionStatus(is_running=True, cpu_usage=-10.0)
        with self.assertRaises(ValidationError):
            status.validate()
        
        # 测试内存使用量为负数
        status = CollectionStatus(is_running=True, memory_usage=-50.0)
        with self.assertRaises(ValidationError):
            status.validate()
    
    def test_save_and_retrieve_status(self):
        """测试保存和检索状态"""
        # 创建并保存状态
        status = CollectionStatus.create(
            is_running=True,
            cpu_usage=30.0,
            memory_usage=256.0
        )
        
        self.assertIsNotNone(status.id)
        
        # 根据ID检索状态
        retrieved_status = CollectionStatus.find_by_id(status.id)
        self.assertIsNotNone(retrieved_status)
        self.assertTrue(retrieved_status.is_running)
        self.assertEqual(retrieved_status.data.get('cpu_usage'), 30.0)
        self.assertEqual(retrieved_status.data.get('memory_usage'), 256.0)
    
    def test_get_latest_status(self):
        """测试获取最新状态"""
        # 初始状态应该没有记录
        latest_status = CollectionStatus.get_latest_status()
        self.assertIsNone(latest_status)
        
        # 创建状态记录
        status1 = CollectionStatus.create(is_running=False)
        status2 = CollectionStatus.create(is_running=True)
        
        # 获取最新状态
        latest_status = CollectionStatus.get_latest_status()
        self.assertIsNotNone(latest_status)
        self.assertEqual(latest_status.id, status2.id)
        self.assertTrue(latest_status.is_running)
    
    def test_record_status(self):
        """测试记录状态"""
        now = datetime.now()
        
        status = CollectionStatus.record_status(
            is_running=True,
            sensor_last_collection=now,
            rfid_last_collection=now,
            cpu_usage=45.0,
            memory_usage=512.0,
            error_message=None
        )
        
        self.assertIsNotNone(status.id)
        self.assertTrue(status.is_running)
        self.assertEqual(status.data.get('cpu_usage'), 45.0)
        self.assertEqual(status.data.get('memory_usage'), 512.0)
    
    def test_get_status_history(self):
        """测试获取状态历史"""
        # 创建多个状态记录
        status1 = CollectionStatus.create(is_running=False)
        status2 = CollectionStatus.create(is_running=True)
        status3 = CollectionStatus.create(is_running=True, cpu_usage=60.0)
        
        # 获取状态历史
        history = CollectionStatus.get_status_history(hours=24, limit=10)
        
        self.assertEqual(len(history), 3)
        # 应该按时间倒序排列
        self.assertEqual(history[0].id, status3.id)
        self.assertEqual(history[1].id, status2.id)
        self.assertEqual(history[2].id, status1.id)
    
    def test_to_api_dict(self):
        """测试API字典转换"""
        now = datetime.now()
        status = CollectionStatus.create(
            is_running=True,
            sensor_last_collection=now.isoformat(),
            cpu_usage=35.0,
            memory_usage=128.0,
            error_message="测试消息"
        )
        
        api_dict = status.to_api_dict()
        
        self.assertTrue(api_dict['isRunning'])
        self.assertEqual(api_dict['sensorLastCollection'], now.isoformat())
        self.assertEqual(api_dict['cpuUsage'], 35.0)
        self.assertEqual(api_dict['memoryUsage'], 128.0)
        self.assertEqual(api_dict['errorMessage'], "测试消息")


if __name__ == '__main__':
    unittest.main()