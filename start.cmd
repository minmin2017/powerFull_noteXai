@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   Powerfull Note - starting...
echo   เปิดเบราว์เซอร์ที่ http://localhost:4321 (Chrome/Edge)
echo.
start "" http://localhost:4321
node server.js
