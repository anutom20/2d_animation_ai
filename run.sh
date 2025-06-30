#!/bin/bash
echo "Starting 2D Animation AI FastAPI application..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000