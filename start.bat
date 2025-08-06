@echo off
echo 启动档案库房智能监测系统...
echo.

REM 清除虚拟环境相关的环境变量
set VIRTUAL_ENV=
set PYTHONHOME=

REM 创建必要的目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "exports" mkdir exports

REM 启动后端服务
echo 正在启动后端服务...
echo 系统地址：http://127.0.0.1:5000
echo.
echo 按 Ctrl+C 停止服务
echo.

REM 延迟2秒后自动打开浏览器
start /min cmd /c "timeout /t 2 >nul && start http://127.0.0.1:5000"

cd backend
python app.py

pause