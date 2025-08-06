#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_database, get_db_connection
from models.collection_config import CollectionConfig

def test_database():
    """测试数据库连接和操作"""
    try:
        print("1. 初始化数据库...")
        init_database()
        print("   ✓ 数据库初始化成功")
        
        print("2. 测试数据库连接...")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   ✓ 数据库连接成功，共有 {len(tables)} 个表")
        conn.close()
        
        print("3. 测试采集配置表...")
        cursor = get_db_connection().cursor()
        cursor.execute("SELECT * FROM collection_configs LIMIT 1")
        result = cursor.fetchone()
        print(f"   ✓ 采集配置表查询成功，结果: {result}")
        cursor.connection.close()
        
        print("4. 测试创建默认配置...")
        config = CollectionConfig.get_or_create_default()
        print(f"   ✓ 默认配置创建成功: {config.to_api_dict()}")
        
        print("5. 测试更新配置...")
        success = config.update_config(sensor_interval=60, updated_by='test')
        print(f"   ✓ 配置更新成功: {success}")
        
        print("\n所有测试通过！")
        return True
        
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_database()