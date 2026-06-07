@echo off
cd /d "%~dp0"
chcp 65001 > nul
echo ===================================
echo   Family Tree - Web UI
echo ===================================
echo   URL  : http://localhost:8888
echo   Admin: admin / admin1234
echo   กด Ctrl+C เพื่อปิด
echo ===================================
python web_ui.py
pause
