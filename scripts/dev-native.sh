#!/bin/bash

# dev-native.sh - Start local development environment natively (no Docker)
# Requirements: uv, npm/bun installed
# Usage: ./scripts/dev-native.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PIDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""

# Log files
LOG_DIR="scripts/logs"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"

    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    echo -e "${GREEN}Services stopped${NC}"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Create log directory
mkdir -p "$LOG_DIR"

# Banner
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Game of Life - Native Development Environment${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed${NC}"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

if ! command -v bun &> /dev/null && ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: Neither bun nor npm is installed${NC}"
    echo "Install bun from: https://bun.sh"
    echo "Or install npm from: https://nodejs.org"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Check environment files
if [ ! -f .env.development ]; then
    echo -e "${RED}Error: .env.development not found${NC}"
    exit 1
fi

if [ ! -f .env.local ]; then
    echo -e "${YELLOW}Creating .env.local from template...${NC}"
    cp .env.local.example .env.local
fi

# Load environment variables (properly handle values with special characters)
set -a  # Automatically export all variables
source .env.development 2>/dev/null || true
if [ -f .env.local ]; then
    source .env.local 2>/dev/null || true
fi
set +a  # Stop auto-exporting

# Start Backend
echo -e "${BLUE}Starting backend...${NC}"
cd server

# Sync dependencies if needed
if [ ! -d .venv ]; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    uv sync
fi

# Start backend in background
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "../$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

cd ..
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo "  Log: $BACKEND_LOG"
echo ""

# Wait for backend to be ready
echo -e "${BLUE}Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Error: Backend failed to start${NC}"
        echo "Check logs at: $BACKEND_LOG"
        tail -n 20 "$BACKEND_LOG"
        exit 1
    fi
    sleep 1
done
echo ""

# Start Frontend
echo -e "${BLUE}Starting frontend...${NC}"
cd client

# Install dependencies if needed
if [ ! -d node_modules ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    if command -v bun &> /dev/null; then
        bun install
    else
        npm install
    fi
fi

# Start frontend in background
if command -v bun &> /dev/null; then
    bun run dev > "../$FRONTEND_LOG" 2>&1 &
else
    npm run dev > "../$FRONTEND_LOG" 2>&1 &
fi
FRONTEND_PID=$!

cd ..
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo "  Log: $FRONTEND_LOG"
echo ""

# Show service information
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}All services running!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Service URLs:${NC}"
echo "  Frontend:    http://localhost:5173"
echo "  Backend API: http://localhost:8000"
echo "  WebSocket:   ws://localhost:8000/ws/simulation"
echo "  Health:      http://localhost:8000/api/health"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo "  Backend:  tail -f $BACKEND_LOG"
echo "  Frontend: tail -f $FRONTEND_LOG"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running and show combined logs
tail -f "$BACKEND_LOG" "$FRONTEND_LOG"
