@echo off
REM Launch TradingView Desktop on Windows with Chrome DevTools Protocol enabled
REM Usage: scripts\launch_tv_debug.bat [port]

set PORT=%1
if "%PORT%"=="" set PORT=9222

REM Kill existing TradingView instances
taskkill /F /IM TradingView.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Auto-detect TradingView install location
set "TV_EXE="

set "TV_EXE=C:\Program Files\WindowsApps\31178TradingViewInc.TradingView_3.2.0.0_x64__q4jpyh43s5mv6\TradingView.exe"

start "" "%TV_EXE%" --remote-debugging-port=%PORT%
exit
