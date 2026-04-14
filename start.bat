@echo off
echo.
echo ████████████████████████████████████████
echo █  PROMETHEUS BOOT SEQUENCE INITIATED  █
echo ████████████████████████████████████████
echo.

if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env"
    echo.
    echo ACTION REQUIRED: Add your Google Gemini API key to backend\.env
    echo Get a free key at: https://aistudio.google.com/app/apikey
    echo.
    pause
)

echo Installing backend dependencies...
cd backend
pip install -r requirements.txt -q
cd ..

echo Installing frontend dependencies...
cd frontend
npm install --silent
cd ..

echo Starting backend...
start /B cmd /c "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak > nul

echo Starting frontend...
start /B cmd /c "cd frontend && npm run dev"

echo.
echo ████████████████████████████████████████
echo █        PROMETHEUS ONLINE              █
echo █                                       █
echo █   Frontend: http://localhost:3000     █
echo █   Backend:  http://localhost:8000     █
echo █   API Docs: http://localhost:8000/docs █
echo ████████████████████████████████████████
echo.
echo Press Ctrl+C or close this window to shut down.
pause
