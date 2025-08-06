@echo off
echo 启动档案库房智能监测系统...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 检查是否需要安装依赖
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo 安装依赖包...
    pip install -r requirements.txt
)

REM 创建必要的目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "exports" mkdir exports

REM 启动后端服务
echo.
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