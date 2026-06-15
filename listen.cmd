@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   👂 Powerfull Note Inbox Listener
echo   คอยฟังข้อความที่คุณพิมพ์หรือพูดจากในแอป...
echo.
node listen.js
