@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   Powerfull Note - starting (auto-restart on code changes)...
echo   เปิดเบราว์เซอร์ที่ http://localhost:4321 (Chrome/Edge)
echo.
start "" http://localhost:4321
start "PTT Listener (Alt+P)" cmd /c ptt-listen.cmd
start "Desktop Notifications" cmd /c notify-listen.cmd
start "Usage Guard (85%% handoff / auto-resume)" cmd /c "node usage-guard.js main"

rem Auto-open Claude Code bound to the "main" chat section and already listening.
rem It waits for this window's server to bind before connecting (see claude-listen.cmd).
rem Skip it with:  start.cmd --no-claude
if /i not "%~1"=="--no-claude" (
  start "Claude Code (main)" cmd /c claude-listen.cmd main
)

node --watch server.js
