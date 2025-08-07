# -*- coding: utf-8 -*-
"""
用户认证API
提供登录、注册、密码重置等功能
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# 简单的用户数据存储（实际项目中应使用数据库）
USERS = {
    'admin': {
        'password': 'admin123',  # 实际项目中应该加密存储
        'email': 'admin@example.com',
        'role': 'administrator',
        'created_at': '2024-01-01T00:00:00'
    }
}

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        # 验证用户
        if username in USERS and USERS[username]['password'] == password:
            # 登录成功，设置会话
            session['user_id'] = username
            session['login_time'] = datetime.now().isoformat()
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'data': {
                    'username': username,
                    'role': USERS[username]['role'],
                    'login_time': session['login_time']
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401
            
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return jsonify({
            'success': False,
            'message': '登录过程中发生错误'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户登出"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': '已成功登出'
        })
    except Exception as e:
        logger.error(f"登出失败: {e}")
        return jsonify({
            'success': False,
            'message': '登出过程中发生错误'
        }), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        if not username or not password or not email:
            return jsonify({
                'success': False,
                'message': '用户名、密码和邮箱不能为空'
            }), 400
        
        if username in USERS:
            return jsonify({
                'success': False,
                'message': '用户名已存在'
            }), 400
        
        # 创建新用户
        USERS[username] = {
            'password': password,  # 实际项目中应该加密
            'email': email,
            'role': 'user',
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': '注册成功'
        })
        
    except Exception as e:
        logger.error(f"注册失败: {e}")
        return jsonify({
            'success': False,
            'message': '注册过程中发生错误'
        }), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """忘记密码"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({
                'success': False,
                'message': '邮箱地址不能为空'
            }), 400
        
        # 模拟发送重置邮件
        return jsonify({
            'success': True,
            'message': f'密码重置链接已发送到 {email}'
        })
        
    except Exception as e:
        logger.error(f"密码重置失败: {e}")
        return jsonify({
            'success': False,
            'message': '密码重置过程中发生错误'
        }), 500

@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    """检查用户会话状态"""
    try:
        if 'user_id' in session:
            return jsonify({
                'success': True,
                'authenticated': True,
                'data': {
                    'username': session['user_id'],
                    'login_time': session.get('login_time')
                }
            })
        else:
            return jsonify({
                'success': True,
                'authenticated': False
            })
    except Exception as e:
        logger.error(f"会话检查失败: {e}")
        return jsonify({
            'success': False,
            'message': '会话检查失败'
        }), 500