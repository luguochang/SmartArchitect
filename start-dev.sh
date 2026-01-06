#!/bin/bash

echo "Starting SmartArchitect AI Development Environment..."
echo ""

# 启动后端
echo "[1/2] Starting Backend..."
cd backend
source venv/bin/activate
python -m app.main &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 2

# 启动前端
echo "[2/2] Starting Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "SmartArchitect AI is running!"
echo "========================================"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all services"

# 等待信号
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

wait
