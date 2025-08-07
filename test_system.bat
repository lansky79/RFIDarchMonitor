@echo off
echo 启动档案库房智能监测系统测试...
echo.

echo 1. 启动后端服务...
start "Backend Server" cmd /k "cd /d %~dp0 && python backend/app.py"

echo 2. 等待服务启动...
timeout /t 5 /nobreak > nul

echo 3. 打开测试页面...
start "" "http://127.0.0.1:5000"
start "" "simple_test.html"

echo.
echo 测试页面已打开，请检查：
echo - 主系统页面: http://127.0.0.1:5000
echo - 简单测试页面: simple_test.html
echo.
echo 按任意键退出...
pause > nul