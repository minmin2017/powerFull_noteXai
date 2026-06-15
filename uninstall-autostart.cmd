@echo off
setlocal
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\PowerfullNote-Listen.lnk"
if exist "%LNK%" (
  del "%LNK%"
  echo Removed autostart shortcut. Claude Code will no longer auto-start on login.
) else (
  echo No autostart shortcut found - nothing to remove.
)
pause
endlocal
