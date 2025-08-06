#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接和初始化模块
"""

import sqlite3
import os
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # 使查询结果可以像字典一样访问
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise

def init_database():
    """初始化数据库，创建所有必要的表"""
    try:
        # 确保数据目录存在
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 创建环境数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS environment_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                temperature REAL,
                humidity REAL,
                light_intensity REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                location TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建RFID设备表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rfid_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL,
                device_type TEXT NOT NULL,
                serial_port TEXT,
                ip_address TEXT,
                status TEXT DEFAULT 'offline',
                config_json TEXT,
                location TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建RFID标签表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rfid_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id TEXT UNIQUE NOT NULL,
                archive_id TEXT,
                tag_type TEXT DEFAULT '档案标签',
                status TEXT DEFAULT 'active',
                last_seen_location TEXT,
                last_seen_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建档案信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS archives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                archive_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                category TEXT,
                description TEXT,
                rfid_tag_id TEXT,
                current_location TEXT,
                status TEXT DEFAULT 'normal',
                created_by TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rfid_tag_id) REFERENCES rfid_tags (tag_id)
            )
        ''')
        
        # 创建位置记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS location_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                archive_id INTEGER,
                rfid_device_id INTEGER,
                location TEXT NOT NULL,
                action_type TEXT DEFAULT 'scan',
                signal_strength INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (archive_id) REFERENCES archives (id),
                FOREIGN KEY (rfid_device_id) REFERENCES rfid_devices (id)
            )
        ''')
        
        # 创建告警记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                level TEXT NOT NULL DEFAULT 'warning',
                title TEXT NOT NULL,
                message TEXT,
                source_id TEXT,
                source_type TEXT,
                status TEXT DEFAULT 'pending',
                handled_by TEXT,
                handled_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建盘点任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                area TEXT,
                status TEXT DEFAULT 'pending',
                total_expected INTEGER DEFAULT 0,
                total_found INTEGER DEFAULT 0,
                missing_count INTEGER DEFAULT 0,
                extra_count INTEGER DEFAULT 0,
                started_at DATETIME,
                completed_at DATETIME,
                created_by TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建盘点详情表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                archive_id INTEGER,
                expected_location TEXT,
                found_location TEXT,
                status TEXT DEFAULT 'missing',
                scanned_at DATETIME,
                notes TEXT,
                FOREIGN KEY (task_id) REFERENCES inventory_tasks (id),
                FOREIGN KEY (archive_id) REFERENCES archives (id)
            )
        ''')
        
        # 创建设备维护记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_type TEXT NOT NULL,
                device_id INTEGER,
                device_name TEXT,
                maintenance_type TEXT NOT NULL,
                description TEXT,
                cost REAL DEFAULT 0.0,
                technician TEXT,
                scheduled_date DATETIME,
                completed_date DATETIME,
                status TEXT DEFAULT 'scheduled',
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建系统配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                config_type TEXT DEFAULT 'string',
                description TEXT,
                category TEXT DEFAULT 'general',
                updated_by TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建系统日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_level TEXT NOT NULL,
                module TEXT,
                message TEXT NOT NULL,
                user_id TEXT,
                ip_address TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建数据采集配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_interval INTEGER NOT NULL DEFAULT 30,
                rfid_interval INTEGER NOT NULL DEFAULT 10,
                is_paused BOOLEAN NOT NULL DEFAULT 0,
                updated_by TEXT DEFAULT 'system',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建数据采集状态表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_running BOOLEAN NOT NULL DEFAULT 0,
                sensor_last_collection DATETIME,
                rfid_last_collection DATETIME,
                cpu_usage REAL,
                memory_usage REAL,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入默认系统配置
        default_configs = [
            ('temp_min_threshold', str(Config.DEFAULT_TEMP_MIN), 'float', '最低温度阈值(°C)', 'environment'),
            ('temp_max_threshold', str(Config.DEFAULT_TEMP_MAX), 'float', '最高温度阈值(°C)', 'environment'),
            ('humidity_min_threshold', str(Config.DEFAULT_HUMIDITY_MIN), 'float', '最低湿度阈值(%)', 'environment'),
            ('humidity_max_threshold', str(Config.DEFAULT_HUMIDITY_MAX), 'float', '最高湿度阈值(%)', 'environment'),
            ('light_min_threshold', str(Config.DEFAULT_LIGHT_MIN), 'float', '最低光照阈值(lux)', 'environment'),
            ('light_max_threshold', str(Config.DEFAULT_LIGHT_MAX), 'float', '最高光照阈值(lux)', 'environment'),
            ('sensor_scan_interval', str(Config.SENSOR_SCAN_INTERVAL), 'int', '传感器扫描间隔(秒)', 'hardware'),
            ('rfid_scan_interval', str(Config.RFID_SCAN_INTERVAL), 'int', 'RFID扫描间隔(秒)', 'hardware'),
            ('alert_sound_enabled', str(Config.ALERT_SOUND_ENABLED), 'bool', '启用声音告警', 'alert'),
            ('data_retention_days', str(Config.DATA_RETENTION_DAYS), 'int', '数据保留天数', 'system')
        ]
        
        for config_key, config_value, config_type, description, category in default_configs:
            cursor.execute('''
                INSERT OR IGNORE INTO system_config 
                (config_key, config_value, config_type, description, category, updated_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (config_key, config_value, config_type, description, category, 'system'))
        
        # 创建索引以提高查询性能
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_environment_timestamp ON environment_data(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_environment_sensor ON environment_data(sensor_id)',
            'CREATE INDEX IF NOT EXISTS idx_location_archive ON location_history(archive_id)',
            'CREATE INDEX IF NOT EXISTS idx_location_timestamp ON location_history(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)',
            'CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at)',
            'CREATE INDEX IF NOT EXISTS idx_rfid_tags_status ON rfid_tags(status)',
            'CREATE INDEX IF NOT EXISTS idx_archives_code ON archives(archive_code)',
            'CREATE INDEX IF NOT EXISTS idx_config_key ON system_config(config_key)',
            'CREATE INDEX IF NOT EXISTS idx_collection_configs_updated ON collection_configs(updated_at)',
            'CREATE INDEX IF NOT EXISTS idx_collection_status_timestamp ON collection_status(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_collection_status_running ON collection_status(is_running)'
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        conn.close()
        
        logger.info("数据库初始化成功")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise

def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """执行数据库查询的通用函数"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
        else:
            conn.commit()
            return cursor.lastrowid
            
    except Exception as e:
        logger.error(f"数据库查询失败: {query}, 错误: {e}")
        raise
    finally:
        if conn:
            conn.close()

def backup_database():
    """备份数据库"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"archive_system_backup_{timestamp}.db"
        backup_path = os.path.join(Config.DATABASE_BACKUP_PATH, backup_filename)
        
        # 确保备份目录存在
        os.makedirs(Config.DATABASE_BACKUP_PATH, exist_ok=True)
        
        # 复制数据库文件
        import shutil
        shutil.copy2(Config.DATABASE_PATH, backup_path)
        
        logger.info(f"数据库备份成功: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"数据库备份失败: {e}")
        raise