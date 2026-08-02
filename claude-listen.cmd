@echo off
setlocal
cd /d "%~dp0"

rem ===== Open Claude Code (skip permissions) + auto-listen ONE chat section =====
rem Usage:
rem   claude-listen.cmd            -> listen to the MAIN chat only (default)
rem   claude-listen.cmd "chat2"    -> bind to another chat section (multi instance)

set "CHAT_SECTION=%~1"
if "%CHAT_SECTION%"=="" set "CHAT_SECTION=main"

rem --- wait for the note server (port 4321); start it only if it never shows up ---
rem start.cmd launches this script *alongside* the server, so give the server a
rem grace period to bind before assuming it's down - otherwise both would race to
rem spawn `node --watch server.js` and the second one dies on EADDRINUSE.
set "SERVER_UP="
for /l %%i in (1,1,15) do (
  if not defined SERVER_UP (
    curl -s -m 2 -o nul http://localhost:4321/api/state && set "SERVER_UP=1"
    if not defined SERVER_UP timeout /t 1 /nobreak >nul
  )
)
if not defined SERVER_UP (
  echo Note server not running - starting it...
  start "Powerfull Note server" cmd /c "node --watch server.js"
  timeout /t 3 /nobreak >nul
)

echo Opening Claude Code - listening to chat section: %CHAT_SECTION%
claude --dangerously-skip-permissions "Read CLAUDE.md. You are bound to chat section '%CHAT_SECTION%' (also in env CHAT_SECTION). Arm a persistent background Monitor that polls ONLY this section: curl -s -G http://localhost:4321/api/inbox --data-urlencode section=%CHAT_SECTION% --data-urlencode drain=true --data-urlencode agent=claude  every ~3s, and act on each message. The agent=claude parameter is REQUIRED - without it the server replies 'who are you?' and returns nothing. Reply ONLY via the say_to_user MCP tool (it auto-targets this section from env). Reply in Thai. Do not drain the shared inbox and do not touch other sections."

endlocal
