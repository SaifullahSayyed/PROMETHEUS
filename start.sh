#!/bin/bash
set -e

echo ""
echo "████████████████████████████████████████"
echo "█  PROMETHEUS BOOT SEQUENCE INITIATED  █"
echo "████████████████████████████████████████"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Install from python.org"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found. Install from nodejs.org"
    exit 1
fi

# Check for .env
if [ ! -f "backend/.env" ]; then
    echo "SETUP: Creating backend/.env from template..."
    cp backend/.env.example backend/.env
    echo ""
    echo "⚠️  ACTION REQUIRED: Add your Anthropic API key to backend/.env"
    echo "   Get a free key at: https://console.anthropic.com"
    echo ""
    read -p "Press ENTER after adding your API key to backend/.env ..."
fi

# Install backend deps
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt -q
cd ..

# Install frontend deps
echo "Installing frontend dependencies..."
cd frontend
npm install --silent
cd ..

echo ""
echo "Starting PROMETHEUS..."
echo ""

# Start backend
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
sleep 3

# Start frontend
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "████████████████████████████████████████"
echo "█        PROMETHEUS ONLINE              █"
echo "█                                       █"
echo "█   Frontend: http://localhost:3000     █"
echo "█   Backend:  http://localhost:8000     █"
echo "█   API Docs: http://localhost:8000/docs █"
echo "████████████████████████████████████████"
echo ""
echo "Press Ctrl+C to shut down all services"
echo ""

# Keep alive and forward signals
cleanup() {
    echo "Shutting down PROMETHEUS..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

wait $BACKEND_PID $FRONTEND_PID
