#!/bin/bash

# XGaming AI Chat Application Startup Script
# This script starts both the FastAPI backend and Next.js frontend

echo "🚀 Starting XGaming AI Chat Application..."

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Shutting down services..."
    jobs -p | xargs -r kill
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Check if required environment variables are set
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Warning: backend/.env not found. Please create it with required environment variables."
fi

if [ ! -f "frontend-new/.env.local" ]; then
    echo "⚠️  Warning: frontend-new/.env.local not found. Creating basic configuration..."
    echo "FASTAPI_URL=http://localhost:8000" > frontend-new/.env.local
fi

# Start the FastAPI backend
echo "🔧 Starting FastAPI backend on port 8000..."
cd backend
source venv/bin/activate && python -m app.server &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
cd ..

# Wait a moment for backend to start
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/api/chat/health > /dev/null 2>&1; then
    echo "❌ Backend failed to start properly"
    exit 1
fi

echo "✅ Backend is running"

# Start the Next.js frontend
echo "🎨 Starting Next.js frontend on port 3000..."
cd frontend-new
npm run dev &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd ..

# Wait a moment for frontend to start
sleep 10

echo "🎉 Both services are starting up!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 Backend Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services"

# Keep the script running and wait for both processes
wait