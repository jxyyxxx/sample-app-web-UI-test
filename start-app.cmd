@echo off
title Start SauceDemo App
cd /d "%~dp0..\sample-app-web"
if errorlevel 1 (
    echo [ERROR] Cannot find ..\sample-app-web
    pause
    exit /b 1
)
echo ================================================
echo   Starting app: http://localhost:3000
echo   Close this window to stop the server
echo ================================================
echo.
call npm.cmd run start -- --port 3000 --strictPort
pause
