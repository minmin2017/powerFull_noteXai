@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem รอเซิร์ฟเวอร์ตอบ เช็คถี่ ๆ (ทุก ~200 ms) นานสุด 30 วิ
rem ใช้ 127.0.0.1 ไม่ใช่ localhost — วัดแล้วต่างกัน 204 ms vs 1.4 ms ต่อครั้ง
set "UP="
for /l %%i in (1,1,150) do (
  if not defined UP (
    curl -s -m 2 -o nul http://127.0.0.1:4321/api/state && set "UP=1"
    if not defined UP ping -n 1 -w 200 127.0.0.1 >nul
  )
)
if not defined UP (
  echo Server did not come up within 30s - helpers not started.
  exit /b 1
)

start "" http://127.0.0.1:4321

rem โหมด --lite: แค่แอปโน้ต ไม่เปิดตัวช่วยอะไรเลย (สำหรับเพื่อน)
echo %* | find /i "--lite" >nul && exit /b 0

rem ทยอยเปิด เว้นระยะ ~1.5 วิ กันแย่งดิสก์ตอนเครื่องเพิ่งบูต
rem หมายเหตุ: A4 (agy headless bridge) ยังไม่ทำ - ยังใช้ Antigravity Startup Helper ตัวเดิมไปก่อน
start "Antigravity Startup Helper" /min cmd /c "python tools/antigravity_startup_bot.py"
ping -n 2 -w 1000 127.0.0.1 >nul
start "PTT Listener (Alt+P)" /min cmd /c ptt-listen.cmd
ping -n 2 -w 1000 127.0.0.1 >nul
start "Desktop Notifications" /min cmd /c notify-listen.cmd
ping -n 2 -w 1000 127.0.0.1 >nul
start "Usage Guard (85%% handoff / auto-resume)" /min cmd /c "node usage-guard.js main"
ping -n 2 -w 1000 127.0.0.1 >nul
start "Flashcard Studio" /min cmd /c "node flashcard-app/server.js"
ping -n 2 -w 1000 127.0.0.1 >nul

rem Auto-open Claude Code bound to the "main" chat section and already listening.
rem It waits for this window's server to bind before connecting (see claude-listen.cmd).
rem Skip it with:  start.cmd --no-claude
echo %* | find /i "--no-claude" >nul || (
  start "Claude Code (main)" cmd /c claude-listen.cmd main
)
