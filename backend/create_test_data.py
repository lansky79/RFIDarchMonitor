#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试数据脚本
用于生成演示和测试所需的基础数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_database
from models.rfid import RfidDevice, RfidTag
from models.archive import Archive
from models.environment import EnvironmentData
from models.maintenance import MaintenanceRecord
from datetime import datetime, timedelta
import random

def create_test_data():
    """创建测试数据"""
    print("正在创建测试数据...")
    
    # 初始化数据库
    init_database()
    
    # 创建RFID设备
    print("创建RFID设备...")
    devices = [
        {
            'device_name': 'RFID_READER_001',
            'device_type': 'serial',
            'serial_port': 'COM3',
            'status': 'online',
            'location': '档案室入口'
        },
        {
            'device_name': 'RFID_READER_002',
            'device_type': 'serial',
            'serial_port': 'COM4',
            'status': 'online',
            'location': '档案室出口'
        },
        {
            'device_name': 'RFID_READER_003',
            'device_type': 'network',
            'ip_address': '192.168.1.100',
            'status': 'offline',
            'location': '档案室A区'
        }
    ]
    
    for device_data in devices:
        try:
            RfidDevice.create_with_validation(**device_data)
            print(f"  创建设备: {device_data['device_name']}")
        except Exception as e:
            print(f"  设备创建失败: {e}")
    
    # 创建RFID标签
    print("创建RFID标签...")
    tags = []
    for i in range(1, 21):  # 创建20个标签
        tag_id = f"E200{i:04d}"
        tags.append({
            'tag_id': tag_id,
            'tag_type': '档案标签',
            'status': 'active'
        })
    
    for tag_data in tags:
        try:
            RfidTag.create_with_validation(**tag_data)
            print(f"  创建标签: {tag_data['tag_id']}")
        except Exception as e:
            print(f"  标签创建失败: {e}")
    
    # 创建档案
    print("创建档案...")
    categories = ['文件档案', '照片档案', '视频档案', '音频档案', '电子档案']
    locations = ['档案室A区', '档案室B区', '档案室C区', '档案室入口', '档案室出口']
    
    archives = []
    for i in range(1, 16):  # 创建15个档案
        archive_code = f"ARCH{i:04d}"
        category = random.choice(categories)
        location = random.choice(locations)
        
        # 前10个档案分配RFID标签
        rfid_tag_id = f"E200{i:04d}" if i <= 10 else None
        
        archives.append({
            'archive_code': archive_code,
            'title': f'测试档案{i:02d} - {category}',
            'category': category,
            'description': f'这是第{i}个测试档案，用于系统功能演示',
            'rfid_tag_id': rfid_tag_id,
            'current_location': location,
            'created_by': 'system'
        })
    
    for archive_data in archives:
        try:
            Archive.create_with_validation(**archive_data)
            print(f"  创建档案: {archive_data['archive_code']}")
            
            # 如果有RFID标签，更新标签的档案关联
            if archive_data['rfid_tag_id']:
                tag = RfidTag.find_by_tag_id(archive_data['rfid_tag_id'])
                if tag:
                    tag.assign_to_archive(archive_data['archive_code'])
                    
        except Exception as e:
            print(f"  档案创建失败: {e}")
    
    # 创建历史环境数据
    print("创建历史环境数据...")
    sensors = ['SENSOR_001', 'SENSOR_002', 'SENSOR_003']
    sensor_locations = {
        'SENSOR_001': '档案室A区',
        'SENSOR_002': '档案室B区',
        'SENSOR_003': '档案室C区'
    }
    
    # 创建过去7天的数据
    for days_ago in range(7):
        date = datetime.now() - timedelta(days=days_ago)
        
        # 每天每小时创建一条数据
        for hour in range(0, 24, 2):  # 每2小时一条数据
            timestamp = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            for sensor_id in sensors:
                # 生成模拟数据
                base_temp = 22.0 + random.uniform(-1, 1)
                base_humidity = 50.0 + random.uniform(-5, 5)
                base_light = 300.0 + random.uniform(-50, 50)
                
                # 添加时间变化（白天光照强，夜晚光照弱）
                if 6 <= hour <= 18:  # 白天
                    light_multiplier = 1.0 + (hour - 12) * 0.1
                else:  # 夜晚
                    light_multiplier = 0.3
                
                env_data = {
                    'sensor_id': sensor_id,
                    'temperature': round(base_temp, 1),
                    'humidity': round(base_humidity, 1),
                    'light_intensity': round(base_light * light_multiplier, 0),
                    'location': sensor_locations[sensor_id],
                    'timestamp': timestamp.isoformat()
                }
                
                try:
                    EnvironmentData.create(**env_data)
                except Exception as e:
                    print(f"  环境数据创建失败: {e}")
    
    print(f"历史环境数据创建完成，共创建约 {7 * 12 * 3} 条记录")

def create_maintenance_records():
    """创建维护记录测试数据"""
    maintenance_records = [
        # RFID设备维护记录
        {
            'device_type': 'rfid',
            'device_id': 1,
            'device_name': 'RFID_READER_001',
            'maintenance_type': 'routine',
            'description': '定期检查RFID读写器001，检查天线连接和读取性能',
            'scheduled_date': (datetime.now() - timedelta(days=2)).isoformat(),
            'status': 'completed',
            'completed_date': (datetime.now() - timedelta(days=1)).isoformat(),
            'technician': '张工程师',
            'cost': 150.0,
            'notes': '设备运行正常，天线连接良好，读取距离正常'
        },
        {
            'device_type': 'rfid',
            'device_id': 2,
            'device_name': 'RFID_READER_002',
            'maintenance_type': 'preventive',
            'description': '预防性维护RFID读写器002，清洁设备并更新固件',
            'scheduled_date': (datetime.now() + timedelta(days=3)).isoformat(),
            'status': 'scheduled',
            'technician': '李技术员',
            'cost': 200.0,
            'notes': '需要准备固件更新包'
        },
        {
            'device_type': 'rfid',
            'device_id': 3,
            'device_name': 'RFID_READER_003',
            'maintenance_type': 'corrective',
            'description': '修复RFID读写器003网络连接问题',
            'scheduled_date': (datetime.now() - timedelta(days=1)).isoformat(),
            'status': 'in_progress',
            'technician': '王工程师',
            'cost': 300.0,
            'notes': '网络模块故障，需要更换网络适配器'
        },
        # 传感器维护记录
        {
            'device_type': 'sensor',
            'device_id': 1,
            'device_name': 'SENSOR_001',
            'maintenance_type': 'calibration',
            'description': '校准温湿度传感器SENSOR_001',
            'scheduled_date': (datetime.now() - timedelta(days=5)).isoformat(),
            'status': 'completed',
            'completed_date': (datetime.now() - timedelta(days=4)).isoformat(),
            'technician': '陈工程师',
            'cost': 100.0,
            'notes': '校准完成，精度恢复正常'
        },
        {
            'device_type': 'sensor',
            'device_id': 2,
            'device_name': 'SENSOR_002',
            'maintenance_type': 'routine',
            'description': '定期检查光照传感器SENSOR_002',
            'scheduled_date': (datetime.now() + timedelta(days=1)).isoformat(),
            'status': 'scheduled',
            'technician': '刘技术员',
            'cost': 80.0,
            'notes': '检查传感器表面清洁度和响应速度'
        },
        {
            'device_type': 'sensor',
            'device_id': 3,
            'device_name': 'SENSOR_003',
            'maintenance_type': 'upgrade',
            'description': '升级传感器SENSOR_003固件版本',
            'scheduled_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'status': 'scheduled',
            'technician': '张工程师',
            'cost': 0.0,
            'notes': '固件升级，增加新的数据采集功能'
        },
        # 网络设备维护记录
        {
            'device_type': 'network',
            'device_id': 1,
            'device_name': '核心交换机',
            'maintenance_type': 'preventive',
            'description': '核心交换机预防性维护，清理灰尘和检查端口',
            'scheduled_date': (datetime.now() - timedelta(days=10)).isoformat(),
            'status': 'completed',
            'completed_date': (datetime.now() - timedelta(days=9)).isoformat(),
            'technician': '网络管理员',
            'cost': 120.0,
            'notes': '设备运行正常，所有端口工作正常'
        },
        {
            'device_type': 'network',
            'device_id': 2,
            'device_name': '无线AP',
            'maintenance_type': 'corrective',
            'description': '修复无线AP信号覆盖问题',
            'scheduled_date': (datetime.now() - timedelta(days=3)).isoformat(),
            'status': 'overdue',
            'technician': '网络技术员',
            'cost': 250.0,
            'notes': '需要调整天线位置和功率设置'
        },
        # 服务器维护记录
        {
            'device_type': 'server',
            'device_id': 1,
            'device_name': '数据库服务器',
            'maintenance_type': 'routine',
            'description': '数据库服务器定期维护，检查硬盘和内存状态',
            'scheduled_date': (datetime.now() + timedelta(days=5)).isoformat(),
            'status': 'scheduled',
            'technician': '系统管理员',
            'cost': 0.0,
            'notes': '定期检查系统性能和数据备份状态'
        },
        {
            'device_type': 'server',
            'device_id': 2,
            'device_name': '应用服务器',
            'maintenance_type': 'upgrade',
            'description': '应用服务器系统升级',
            'scheduled_date': (datetime.now() + timedelta(days=14)).isoformat(),
            'status': 'scheduled',
            'technician': '系统工程师',
            'cost': 500.0,
            'notes': '升级操作系统和应用程序版本'
        },
        # 其他设备维护记录
        {
            'device_type': 'other',
            'device_id': 1,
            'device_name': 'UPS电源',
            'maintenance_type': 'routine',
            'description': 'UPS电源定期检查，测试电池容量',
            'scheduled_date': (datetime.now() - timedelta(days=7)).isoformat(),
            'status': 'completed',
            'completed_date': (datetime.now() - timedelta(days=6)).isoformat(),
            'technician': '电气工程师',
            'cost': 180.0,
            'notes': '电池容量正常，备电时间符合要求'
        },
        {
            'device_type': 'other',
            'device_id': 2,
            'device_name': '空调系统',
            'maintenance_type': 'preventive',
            'description': '档案室空调系统预防性维护',
            'scheduled_date': (datetime.now() + timedelta(days=10)).isoformat(),
            'status': 'scheduled',
            'technician': '空调维修工',
            'cost': 400.0,
            'notes': '清洁过滤器，检查制冷剂和压缩机'
        }
    ]
    
    for record_data in maintenance_records:
        try:
            MaintenanceRecord.create_with_validation(**record_data)
            print(f"  创建维护记录: {record_data['device_name']} - {record_data['maintenance_type']}")
        except Exception as e:
            print(f"  维护记录创建失败: {e}")
    
    print(f"维护记录创建完成，共创建 {len(maintenance_records)} 条记录")
    
    # 创建维护记录
    print("创建维护记录...")
    create_maintenance_records()
    
    print("\n测试数据创建完成！")
    print("=" * 50)
    print("创建的测试数据包括:")
    print("- 3个RFID设备")
    print("- 20个RFID标签")
    print("- 15个档案（前10个已分配RFID标签）")
    print("- 过去7天的环境监测数据")
    print("- 设备维护记录")
    print("=" * 50)

if __name__ == '__main__':
    create_test_data()