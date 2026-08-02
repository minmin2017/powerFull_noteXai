@echo off
cd /d "%~dp0"
echo Desktop notifications: shows a toast when Claude/Gemini reply in Powerfull Note.
python notify_daemon.py
pause
