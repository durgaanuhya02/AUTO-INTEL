@echo off
echo Starting Agentic AI Business Decision System (No Docker Mode)...
echo.
echo NOTE: This runs without Redis/PostgreSQL. Some features may be limited.
echo For full functionality, please install Docker and use the full setup.
echo.

echo Starting backend...
cd backend
start cmd /k "venv\Scripts\python -c \"print('Starting backend server...'); import sys; sys.path.append('.'); from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)\""
cd ..

echo Starting frontend...
cd frontend
start cmd /k "npm run dev"
cd ..

echo.
echo System is starting up...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause
