#!/bin/bash

# Vite frontend
cd frontend
pnpm run dev &
FRONTEND_PID=$!
cd ..

# FastAPI backend
cd backend
source .venv/bin/activate
python3 api.py &

wait $FRONTEND_PID