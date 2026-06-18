@echo off
setlocal
rem  spawn-agent.cmd <agent_id>
rem  Opens claude as a simulation agent. Agent reads inbox section via Monitor,
rem  posts responses back to sim_coordinator inbox via curl (NOT say_to_user).

set "AGENT_ID=%~1"
if "%AGENT_ID%"=="" (echo Usage: spawn-agent.cmd ^<agent_id^> && exit /b 1)

set "CHAT_SECTION=sim_%AGENT_ID%"
set "CLAUDE=%USERPROFILE%\.local\bin\claude.exe"
if not exist "%CLAUDE%" (echo ERROR: claude not found at %CLAUDE% && pause && exit /b 1)

cd /d "%~dp0.."
echo [agent %AGENT_ID%] Starting with CHAT_SECTION=%CHAT_SECTION%

"%CLAUDE%" --dangerously-skip-permissions "You are simulation agent %AGENT_ID%. Do these steps immediately: 1) Run: curl -s -X POST http://localhost:4321/api/inbox -H Content-Type:application/json -d {\"text\":\"{\\\"agent_id\\\":\\\"%AGENT_ID%\\\",\\\"status\\\":\\\"ready\\\"}\",\"section\":\"sim_coordinator\"} 2) Arm a persistent Monitor polling every 2s: curl -s -G http://localhost:4321/api/inbox --data-urlencode section=sim_%AGENT_ID% --data-urlencode drain=true 3) When you get a message with type=scenario in the monitor output, read the persona (first message) and scenario, then respond IN CHARACTER. Post your response by running curl: curl -s -X POST http://localhost:4321/api/inbox -H Content-Type:application/json -d {\"text\":\"{\\\"agent_id\\\":\\\"%AGENT_ID%\\\",\\\"action\\\":\\\"YOUR_ACTION\\\",\\\"speech\\\":\\\"YOUR_SPEECH\\\"}\",\"section\":\"sim_coordinator\"} Then go back to polling. Stay in character at all times."

endlocal
