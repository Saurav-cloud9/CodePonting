@echo off
REM Launch TradingView Desktop on Windows with Chrome DevTools Protocol enabled
REM Usage: scripts\launch_tv_debug.bat [port]

set PORT=%1
if "%PORT%"=="" set PORT=9222

REM Kill existing TradingView instances
taskkill /F /IM TradingView.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM TradingView is installed as a Windows Store (MSIX) package. The version
REM folder under WindowsApps changes on every auto-update, and Windows blocks
REM launching that exe directly by path entirely now (spawns and immediately
REM self-terminates, with or without args). The only way to both launch it
REM AND pass --remote-debugging-port through is proper package activation via
REM IApplicationActivationManager::ActivateApplication, which explorer.exe
REM shell:AppsFolder does NOT expose (no arg passthrough). tv_activate.exe
REM (scripts\tv_activate_helper\) calls that COM API directly with the AUMID
REM (auto-detected each run so it survives future re-publishes) and the debug
REM port argument.

for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "(Get-StartApps | Where-Object { $_.Name -eq 'TradingView' } | Select-Object -First 1 -ExpandProperty AppID)"`) do set "TV_AUMID=%%A"

if "%TV_AUMID%"=="" (
    echo ERROR: Could not find TradingView AUMID via Get-StartApps.
    exit /b 1
)

"%~dp0tv_activate_helper\tv_activate.exe" "%TV_AUMID%" "--remote-debugging-port=%PORT%"
exit
