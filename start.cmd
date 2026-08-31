@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   Powerfull Note - starting (auto-restart on code changes)...
echo   Open http://localhost:4321 in Chrome/Edge
echo.

if not exist "node_modules" (
  echo   Installing npm dependencies ^(first run^)...
  call npm install
)
rem ---- Python deps: ข้ามถ้า requirements.txt ไม่เปลี่ยนตั้งแต่ลงครั้งล่าสุด ----
rem ของเดิมรัน pip ทุกครั้ง = เสียเปล่า 12 วินาทีต่อการเปิด 1 ครั้ง
where python >nul 2>nul && (
  if not exist ".setup" mkdir ".setup"
  set "REQHASH="
  for /f "skip=1 tokens=* delims=" %%h in ('certutil -hashfile requirements.txt SHA256') do (
    if not defined REQHASH set "REQHASH=%%h"
  )
  set "OLDHASH="
  if exist ".setup\deps.hash" set /p OLDHASH=<".setup\deps.hash"
  if not "!REQHASH!"=="!OLDHASH!" (
    echo   Installing/checking Python dependencies ^(requirements.txt changed^)...
    python -m pip install -q -r requirements.txt && >".setup\deps.hash" echo !REQHASH!
  )
)

rem ตัวช่วยทั้งหมดย้ายไป poststart.cmd ซึ่งจะรอให้เซิร์ฟเวอร์ตอบก่อนแล้วค่อยทยอยเปิด
rem ส่ง argument ต่อไปด้วย เพื่อให้ --no-claude / --lite ยังใช้ได้
start "Powerfull Note - startup helpers" /min cmd /c "poststart.cmd %*"

node --watch server.js
