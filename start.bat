@echo off
echo Starting Aman Safety Platform v1.0.0...
cd /d A:\EgyptianLicnesePlateDetector
start cmd /k "venv\Scripts\python.exe src\main.py"
timeout /t 3
start cmd /k "ngrok http 8000"
echo.
echo Server: http://localhost:8000
echo Docs:   http://localhost:8000/docs
echo ngrok:  http://127.0.0.1:4040
pause
