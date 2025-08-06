#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试系统启动脚本
"""

import sys
import os
sys.path.append('backend')

from backend.app import app

if __name__ == '__main__':
    print("启动档案库房智能监测系统...")
    print("访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务")
    
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False  # 关闭调试模式减少错误输出
        )
    except KeyboardInterrupt:
        print("\n系统已停止")