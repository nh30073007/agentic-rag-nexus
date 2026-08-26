@echo off
echo ========================================
echo   Agentic RAG Nexus - Starting Services
echo ========================================

REM Activate virtual environment
call venv\Scripts\activate

REM Start Backend in background
start "Backend" cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
timeout /t 5

REM Start Frontend
start "Frontend" cmd /k "streamlit run frontend/app.py"

echo ========================================
echo   Services Started!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:8501
echo   API Docs: http://localhost:8000/docs
echo ========================================
pause