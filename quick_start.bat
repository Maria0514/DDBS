@echo off
echo ===============================================
echo           分布式数据库系统
echo       基于2PC(二阶段提交)协议
echo ===============================================
echo.
echo 选择启动方式:
echo 1. 观看系统演示
echo 2. 直接启动Web界面
echo 3. 退出
echo.
set /p choice="请输入选项 (1-3): "

if "%choice%"=="1" (
    echo.
    echo 启动系统演示...
    python demo.py
    pause
) else if "%choice%"=="2" (
    echo.
    echo 正在安装依赖...
    pip install -r requirements.txt
    echo.
    echo 启动Web界面...
    echo 请在浏览器中访问: http://localhost:5000
    start http://localhost:5000
    python main.py web
) else (
    echo 退出程序
    exit
)

pause
