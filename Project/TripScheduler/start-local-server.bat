@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set PORT=8080

echo ============================================
echo  TripScheduler ローカルサーバー起動
echo  http://localhost:%PORT%/index.html を開きます
echo  （終了するには、開いたサーバー用の別ウィンドウを閉じてください）
echo ============================================
echo.

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  echo [python] を使ってサーバーを起動します...
  start "TripScheduler local server (python)" cmd /k python -m http.server %PORT%
  timeout /t 2 /nobreak >nul
  start "" "http://localhost:%PORT%/index.html"
  goto :eof
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  echo [py launcher] を使ってサーバーを起動します...
  start "TripScheduler local server (python)" cmd /k py -m http.server %PORT%
  timeout /t 2 /nobreak >nul
  start "" "http://localhost:%PORT%/index.html"
  goto :eof
)

where npx >nul 2>nul
if %ERRORLEVEL%==0 (
  echo [Node.js/npx serve] を使ってサーバーを起動します...
  start "TripScheduler local server (npx serve)" cmd /k npx --yes serve -l %PORT% .
  timeout /t 3 /nobreak >nul
  start "" "http://localhost:%PORT%/index.html"
  goto :eof
)

echo Python も Node.js(npx) も見つかりませんでした。
echo 下記のいずれかをインストールしてから、もう一度このファイルを実行してください。
echo   Python: https://www.python.org/downloads/
echo   Node.js: https://nodejs.org/
echo.
pause
