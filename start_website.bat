@echo off
cd /d C:\Users\Riadh\RAG-FastAPI-Assistant

start "FastAPI Assistant Server" cmd /k ".\.venv\Scripts\python.exe -m uvicorn main:app --reload"

echo Starting FastAPI Assistant...
timeout /t 10 /nobreak >nul

start "" http://127.0.0.1:8000

exit
