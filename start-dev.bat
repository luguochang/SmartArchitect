@echo off
echo Starting SmartArchitect AI Development Environment...
echo.

:: 启动后端
echo [1/2] Starting Backend...
start "SmartArchitect Backend" cmd /k "cd backend && venv\Scripts\activate && python -m app.main"

:: 等待 2 秒
timeout /t 2 /nobreak >nul

:: 启动前端
echo [2/2] Starting Frontend...
start "SmartArchitect Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo SmartArchitect AI is starting!
echo ========================================
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8003
echo API Docs: http://localhost:8003/docs
echo ========================================
echo.
echo Press any key to exit this window...
pause >nul
