@echo off
echo 启动档案库房智能监测系统（带登录）...
echo.

echo 1. 启动后端服务...
start "Backend Server" cmd /k "cd /d %~dp0 && python backend/app.py"

echo 2. 等待服务启动...
timeout /t 3 /nobreak > nul

echo 3. 打开登录页面...
start "" "http://127.0.0.1:5000"

echo.
echo 系统已启动！
echo 登录页面: http://127.0.0.1:5000
echo 默认账户: admin / admin123
echo.
echo 按任意键退出...
pause > nul