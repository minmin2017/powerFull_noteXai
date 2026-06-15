@echo off
setlocal
cd /d "%~dp0"

rem ===== Make Powerfull Note auto-listen the MAIN chat on Windows startup =====
rem Drops a shortcut to claude-listen.cmd into the user's Startup folder, so on
rem every login Claude Code opens (skip permissions) and listens to the main chat.

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "TARGET=%~dp0claude-listen.cmd"
set "LNK=%STARTUP%\PowerfullNote-Listen.lnk"

powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%'); $s.TargetPath='%TARGET%'; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=1; $s.Description='Powerfull Note - auto listen main chat'; $s.Save()"

if exist "%LNK%" (
  echo Installed: %LNK%
  echo Claude Code will auto-open and listen to the MAIN chat on next login.
  echo To undo, run uninstall-autostart.cmd
) else (
  echo Failed to create the startup shortcut.
)
pause
endlocal
