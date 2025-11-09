#!/bin/bash

# Script to run backend server
# Kills existing server if running, then starts fresh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting BrandAI Backend...${NC}"

# Get the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
BACKEND_DIR="$PROJECT_ROOT/backend"

cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Please create it first: python3.12 -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if port 8000 is in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use${NC}"
    echo "Finding and killing existing processes..."
    
    # Find process using port 8000
    PID=$(lsof -ti:8000)
    if [ ! -z "$PID" ]; then
        echo "Killing process $PID..."
        kill -9 $PID 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}✅ Killed existing process${NC}"
    fi
else
    echo -e "${GREEN}✅ Port 8000 is free${NC}"
fi

# Change to backend directory
cd "$BACKEND_DIR"

echo -e "${GREEN}📦 Starting FastAPI server...${NC}"
echo "Server will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

