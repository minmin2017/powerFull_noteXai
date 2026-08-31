@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo =====================================================================
echo    🧠 Powerfull Note — One-Click Setup Wizard for Windows
echo =====================================================================
echo.
echo  [1/4] Checking Node.js runtime...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo    ⚠️ Node.js is NOT installed.
    echo    Attempting automatic installation via winget...
    winget install OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo    ❌ Failed to auto-install Node.js.
        echo    Please download and install Node.js LTS from: https://nodejs.org/
        pause
        exit /b 1
    )
    echo    ✓ Node.js installed! Please restart this setup script if PATH is not updated.
) else (
    for /f "tokens=*" %%i in ('node -v') do set NODE_VER=%%i
    echo    ✓ Found Node.js !NODE_VER!
)

echo.
echo  [2/4] Checking Python runtime...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo    ⚠️ Python is NOT installed.
    echo    Attempting automatic installation via winget...
    winget install Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo    ❌ Failed to auto-install Python.
        echo    Please download and install Python from: https://www.python.org/
        pause
        exit /b 1
    )
    echo    ✓ Python installed!
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
    echo    ✓ Found !PY_VER!
)

echo.
echo  [3/4] Installing project dependencies (npm & pip)...
if exist "package.json" (
    echo    -> Installing Node.js packages...
    call npm install
)
if exist "requirements.txt" (
    echo    -> Installing Python packages...
    python -m pip install -q --upgrade pip
    python -m pip install -q -r requirements.txt
    if not exist ".setup" mkdir ".setup"
    set "REQHASH="
    for /f "skip=1 tokens=* delims=" %%h in ('certutil -hashfile requirements.txt SHA256') do (
        if not defined REQHASH set "REQHASH=%%h"
    )
    >".setup\deps.hash" echo !REQHASH!
)
echo    ✓ Dependencies are up to date!

if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul
        echo    ✓ Created .env from .env.example ^(edit it later to enable optional features^)
    )
)

echo.
echo  [4/4] Creating Desktop Shortcut...
set "TARGET=%~dp0start.cmd"
set "LNK=%USERPROFILE%\Desktop\Powerfull Note.lnk"
set "ICON=%~dp0branding\icon.ico"

if exist "%ICON%" (
    powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%'); $s.TargetPath='%TARGET%'; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=1; $s.Description='Start Powerfull Note (mind-map app + Claude/Gemini bridge)'; $s.IconLocation='%ICON%'; $s.Save()"
) else (
    powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%'); $s.TargetPath='%TARGET%'; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=1; $s.Description='Start Powerfull Note (mind-map app + Claude/Gemini bridge)'; $s.Save()"
)
echo    ✓ Desktop shortcut created: "Powerfull Note" on your Desktop!

echo.
echo =====================================================================
echo    🎉 Setup Complete! Ready to use.
echo =====================================================================
echo.
echo    To start the app:
echo    Double-click the "Powerfull Note" shortcut on your Desktop,
echo    or run start.cmd in this directory.
echo.
pause
endlocal
