@echo off
setlocal
rem ===== Put a "Powerfull Note" shortcut on the Desktop pointing at start.cmd =====
rem Run this once per machine so you don't have to hunt for start.cmd inside the
rem project folder - just double-click the Desktop icon.
rem
rem Custom icon: if branding\icon.ico exists (build it with
rem   python tools\make_icon.py   after saving branding\min_icon.png)
rem the shortcut uses it. Otherwise it falls back to the default cmd icon.

set "TARGET=%~dp0start.cmd"
set "LNK=%USERPROFILE%\Desktop\Powerfull Note.lnk"
set "ICON=%~dp0branding\icon.ico"

if exist "%ICON%" (
  powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%'); $s.TargetPath='%TARGET%'; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=1; $s.Description='Start Powerfull Note (mind-map app + Claude bridge)'; $s.IconLocation='%ICON%'; $s.Save()"
) else (
  powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%'); $s.TargetPath='%TARGET%'; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=1; $s.Description='Start Powerfull Note (mind-map app + Claude bridge)'; $s.Save()"
)

if exist "%LNK%" (
  echo Installed: %LNK%
  echo Double-click "Powerfull Note" on your Desktop to start the app.
) else (
  echo Failed to create the desktop shortcut.
)
pause
endlocal
