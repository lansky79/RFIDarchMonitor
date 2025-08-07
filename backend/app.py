#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
档案库房智能监测系统 - 主应用文件
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import logging
from datetime import datetime

# 导入配置和数据库
from config import Config
from database import init_database, get_db_connection

# 导入API蓝图
from api.environment_api import environment_bp
from api.collection_api import collection_bp
from api.collection_status_api import collection_status_bp
from api.system_performance_api import system_performance_bp
from api.maintenance_api import maintenance_bp
from api.auth_api import auth_bp

# 导入服务
from services.hardware_service import hardware_service

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 启用CORS支持前端跨域请求
CORS(app)

# 注册API蓝图
app.register_blueprint(environment_bp)
app.register_blueprint(collection_bp)
app.register_blueprint(collection_status_bp)
app.register_blueprint(system_performance_bp)
app.register_blueprint(maintenance_bp)
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# 配置日志
import os
log_dir = '../logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 静态文件服务 - 为前端提供静态文件
@app.route('/')
def index():
    return send_from_directory('..', 'login.html')

@app.route('/main')
def main():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('../frontend', filename)

# 健康检查接口
@app.route('/api/health')
def health_check():
    """系统健康检查"""
    try:
        # 检查数据库连接
        conn = get_db_connection()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

# 系统信息接口
@app.route('/api/system/info')
def system_info():
    """获取系统基本信息"""
    return jsonify({
        'name': '档案库房智能监测系统',
        'version': '1.0.0',
        'description': '集成环境监测、RFID管理、档案追踪等功能的综合管理系统',
        'timestamp': datetime.now().isoformat()
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在', 'code': 404}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"内部服务器错误: {error}")
    return jsonify({'error': '内部服务器错误', 'code': 500}), 500

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 初始化数据库
    logger.info("正在初始化数据库...")
    init_database()
    logger.info("数据库初始化完成")
    
    # 启动硬件服务
    logger.info("正在启动硬件服务...")
    hardware_service.start()
    logger.info("硬件服务启动完成")
    
    # 启动应用
    logger.info("启动档案库房智能监测系统...")
    try:
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG']
        )
    finally:
        # 停止硬件服务
        logger.info("正在停止硬件服务...")
        hardware_service.stop()
        logger.info("硬件服务已停止")