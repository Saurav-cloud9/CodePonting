@echo off
echo Launching TradingView with CDP enabled on port 9222...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%LOCALAPPDATA%\TradingView-CDP" ^
  "https://www.tradingview.com/chart/"
echo Done. Chrome opening TradingView...
