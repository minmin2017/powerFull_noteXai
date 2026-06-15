@echo off
setlocal
cd /d "%~dp0"

rem ===== Open Claude Code (skip permissions) + auto-listen ONE chat section =====
rem Usage:
rem   claude-listen.cmd            -> listen to the MAIN chat only (default)
rem   claude-listen.cmd "chat2"    -> bind to another chat section (multi instance)

set "CHAT_SECTION=%~1"
if "%CHAT_SECTION%"=="" set "CHAT_SECTION=main"

rem --- make sure the note server (port 4321) is up; start it if not ---
curl -s -m 3 -o nul http://localhost:4321/api/state
if errorlevel 1 (
  echo Note server not running - starting it...
  start "Powerfull Note server" cmd /c "node --watch server.js"
  timeout /t 3 /nobreak >nul
)

echo Opening Claude Code - listening to chat section: %CHAT_SECTION%
claude --dangerously-skip-permissions "Read CLAUDE.md. You are bound to chat section '%CHAT_SECTION%' (also in env CHAT_SECTION). Arm a persistent background Monitor that polls ONLY this section: curl -s -G http://localhost:4321/api/inbox --data-urlencode section=%CHAT_SECTION% --data-urlencode drain=true  every ~3s, and act on each message. Reply ONLY via the say_to_user MCP tool (it auto-targets this section from env). Reply in Thai. Do not drain the shared inbox and do not touch other sections."

endlocal
