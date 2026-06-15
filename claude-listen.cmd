@echo off
setlocal
cd /d "%~dp0"

rem ===== Open Claude Code (skip permissions) + auto-listen the inbox =====
rem Usage:
rem   claude-listen.cmd              -> listen to ALL messages (single instance)
rem   claude-listen.cmd "chat2"      -> bind to ONE chat section (multi instance)
rem Open several cmd windows, give each a different section name, and you get
rem several Claude Code instances working in parallel.

set "CHAT_SECTION=%~1"

if "%CHAT_SECTION%"=="" (
  echo Opening Claude Code - listening to ALL inbox messages...
  claude --dangerously-skip-permissions "Read CLAUDE.md, then immediately arm a persistent background Monitor that polls http://localhost:4321/api/inbox?drain=true every ~3s and act on each message. Reply to the user in Thai via the say_to_user MCP tool. Do not wait for me to ask."
) else (
  echo Opening Claude Code - bound to chat section: %CHAT_SECTION%
  claude --dangerously-skip-permissions "Read CLAUDE.md. You are bound to chat section '%CHAT_SECTION%' (also in env CHAT_SECTION). Arm a persistent background Monitor that polls ONLY this section, using: curl -s -G http://localhost:4321/api/inbox --data-urlencode section=%CHAT_SECTION% --data-urlencode drain=true  every ~3s, and act on each message. Reply ONLY via the say_to_user MCP tool (it auto-targets this section from env). Reply in Thai. Do not drain the shared inbox and do not touch other sections."
)

endlocal
