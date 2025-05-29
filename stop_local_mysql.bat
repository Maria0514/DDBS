@echo off
echo Stopping local MySQL service...

REM 停止MySQL服务
net stop MySQL80
if errorlevel 1 (
    echo MySQL80 service not found, trying MySQL...
    net stop MySQL
    if errorlevel 1 (
        echo No MySQL service found to stop
    ) else (
        echo MySQL service stopped
    )
) else (
    echo MySQL80 service stopped
)

echo.
echo Local MySQL service has been stopped.
echo You can now use Docker containers on ports 3306 and 3307.
echo.
echo To restart local MySQL later, run:
echo net start MySQL80
echo.
pause
