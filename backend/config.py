#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置文件
"""

import os
from datetime import timedelta

class Config:
    """应用配置类"""
    
    # Flask基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'archive-rfid-monitoring-system-2024'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # 服务器配置
    HOST = os.environ.get('FLASK_HOST', '127.0.0.1')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # 数据库配置
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'data/archive_system.db')
    DATABASE_BACKUP_PATH = os.environ.get('DATABASE_BACKUP_PATH', 'data/backups/')
    
    # 硬件设备配置
    SERIAL_TIMEOUT = int(os.environ.get('SERIAL_TIMEOUT', 5))  # 串口超时时间(秒)
    SENSOR_SCAN_INTERVAL = int(os.environ.get('SENSOR_SCAN_INTERVAL', 30))  # 传感器扫描间隔(秒)
    RFID_SCAN_INTERVAL = int(os.environ.get('RFID_SCAN_INTERVAL', 5))  # RFID扫描间隔(秒)
    
    # 告警配置
    ALERT_EMAIL_ENABLED = os.environ.get('ALERT_EMAIL_ENABLED', 'False').lower() == 'true'
    ALERT_SOUND_ENABLED = os.environ.get('ALERT_SOUND_ENABLED', 'True').lower() == 'true'
    
    # 默认环境阈值配置
    DEFAULT_TEMP_MIN = float(os.environ.get('DEFAULT_TEMP_MIN', 18.0))  # 最低温度
    DEFAULT_TEMP_MAX = float(os.environ.get('DEFAULT_TEMP_MAX', 25.0))  # 最高温度
    DEFAULT_HUMIDITY_MIN = float(os.environ.get('DEFAULT_HUMIDITY_MIN', 40.0))  # 最低湿度
    DEFAULT_HUMIDITY_MAX = float(os.environ.get('DEFAULT_HUMIDITY_MAX', 60.0))  # 最高湿度
    DEFAULT_LIGHT_MIN = float(os.environ.get('DEFAULT_LIGHT_MIN', 100.0))  # 最低光照
    DEFAULT_LIGHT_MAX = float(os.environ.get('DEFAULT_LIGHT_MAX', 500.0))  # 最高光照
    
    # 数据保留配置
    DATA_RETENTION_DAYS = int(os.environ.get('DATA_RETENTION_DAYS', 365))  # 数据保留天数
    LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', 30))  # 日志保留天数
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads/')
    ALLOWED_EXTENSIONS = {'txt', 'csv', 'xlsx', 'xls'}
    
    # 报表导出配置
    EXPORT_FOLDER = os.environ.get('EXPORT_FOLDER', 'exports/')
    REPORT_FORMATS = ['csv', 'xlsx', 'pdf']
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保必要的目录存在
        directories = [
            os.path.dirname(Config.DATABASE_PATH),
            Config.DATABASE_BACKUP_PATH,
            Config.UPLOAD_FOLDER,
            Config.EXPORT_FOLDER,
            'logs'
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DATABASE_PATH = ':memory:'  # 使用内存数据库进行测试

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}