@echo off
echo.
echo ===============================================
echo        Distributed Database System
echo      Based on 2PC Two-Phase Commit
echo ===============================================
echo.

:menu
echo Please select an option:
echo.
echo 1. Watch System Demo
echo 2. Complete System Setup
echo 3. Start Database Containers
echo 4. Initialize Databases
echo 5. Run System Tests
echo 6. Start Web Interface
echo 7. Check System Status
echo 8. Run Complete Flow
echo 9. Exit
echo.

set /p choice="Enter option (1-9): "

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto setup
if "%choice%"=="3" goto start_db
if "%choice%"=="4" goto init_db
if "%choice%"=="5" goto test
if "%choice%"=="6" goto web
if "%choice%"=="7" goto status
if "%choice%"=="8" goto all
if "%choice%"=="9" goto exit
goto invalid

:demo
echo.
echo Starting system demo...
python demo.py
pause
goto menu

:setup
echo.
echo Running complete system setup...
python main.py setup
pause
goto menu

:start_db
echo.
echo Starting database containers...
python main.py start-db
pause
goto menu

:init_db
echo.
echo Initializing databases...
python main.py init-db
pause
goto menu

:test
echo.
echo Running system tests...
python main.py test
pause
goto menu

:web
echo.
echo Starting Web interface...
echo Browser will open http://localhost:5000
start http://localhost:5000
python main.py web
pause
goto menu

:status
echo.
echo Checking system status...
python main.py status
pause
goto menu

:all
echo.
echo Running complete flow...
python main.py all
pause
goto menu

:invalid
echo.
echo Invalid option, please try again
pause
goto menu

:exit
echo.
echo Thank you for using Distributed Database System!
pause
exit