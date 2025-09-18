#!/bin/bash

# Vite frontend
cd frontend
pnpm run dev &
FRONTEND_PID=$!
cd ..

# FastAPI backend
cd backend
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
python3 api.py &

wait $FRONTEND_PID