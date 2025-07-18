#!/bin/bash
echo "Starting 2D Animation AI FastAPI application..."
uvicorn main:app --reload --reload-dir app  --host 0.0.0.0 --port 8000