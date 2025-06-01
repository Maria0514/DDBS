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
echo 
echo 1. Complete System Setup
echo 2. Start Database Containers
echo 3. Initialize Databases
echo 4. Run System Tests
echo 5. Start Web Interface
echo 6. Check System Status
echo 7. Run Complete Flow
echo 8. Exit
echo.

set /p choice="Enter option (1-8): "

@REM if "%choice%"=="1" goto demo
if "%choice%"=="1" goto setup
if "%choice%"=="2" goto start_db
if "%choice%"=="3" goto init_db
if "%choice%"=="4" goto test
if "%choice%"=="5" goto web
if "%choice%"=="6" goto status
if "%choice%"=="7" goto all
if "%choice%"=="8" goto exit
goto invalid

@REM :demo
@REM echo.
@REM echo Starting system demo...
@REM python demo.py
@REM pause
@REM goto menu

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