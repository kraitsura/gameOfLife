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

# PID files for robust process management
PID_DIR="scripts/pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

# Log files
LOG_DIR="scripts/logs"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Cleanup function with process group support and graceful shutdown
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"

    # Kill backend process group
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE" 2>/dev/null)
        if [ ! -z "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo "Stopping backend (PID: $BACKEND_PID)..."
            # Kill process group (-PID sends to entire group)
            kill -TERM -$BACKEND_PID 2>/dev/null || true

            # Wait up to 5 seconds for graceful shutdown
            for i in {1..5}; do
                if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ Backend stopped gracefully${NC}"
                    break
                fi
                sleep 1
            done

            # Force kill if still running
            if ps -p $BACKEND_PID > /dev/null 2>&1; then
                echo -e "${YELLOW}Force killing backend...${NC}"
                kill -9 -$BACKEND_PID 2>/dev/null || true
            fi
        fi
        rm -f "$BACKEND_PID_FILE"
    fi

    # Kill frontend process group (similar logic)
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE" 2>/dev/null)
        if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo "Stopping frontend (PID: $FRONTEND_PID)..."
            kill -TERM -$FRONTEND_PID 2>/dev/null || true

            for i in {1..5}; do
                if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ Frontend stopped gracefully${NC}"
                    break
                fi
                sleep 1
            done

            if ps -p $FRONTEND_PID > /dev/null 2>&1; then
                echo -e "${YELLOW}Force killing frontend...${NC}"
                kill -9 -$FRONTEND_PID 2>/dev/null || true
            fi
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi

    # Cleanup any remaining orphaned processes
    if pgrep -f "uvicorn app.main:app" > /dev/null 2>&1; then
        echo -e "${YELLOW}Cleaning up orphaned uvicorn processes...${NC}"
        pkill -f "uvicorn app.main:app" 2>/dev/null || true
    fi

    echo -e "${GREEN}Services stopped${NC}"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

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

# Check port availability
echo -e "${BLUE}Checking port availability...${NC}"

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}Error: Port 8000 is already in use${NC}"
    echo "Processes using port 8000:"
    lsof -i :8000
    echo ""
    echo "Kill with: kill -9 \$(lsof -t -i:8000)"
    echo "Or run: ./scripts/cleanup-dev.sh"
    exit 1
fi

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port 5173 is already in use${NC}"
    echo "Frontend may fail to start"
    echo ""
fi

echo -e "${GREEN}✓ Ports available${NC}"
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

# Start backend in background with process group
set -m  # Enable job control for process groups
# WebSocket configuration:
# --ws-max-size: Max WebSocket message size (10MB, default 16MB)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info \
  --ws-max-size 10485760 \
  > "../$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "../$BACKEND_PID_FILE"
set +m  # Disable job control

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

# Start frontend in background with process group
set -m  # Enable job control for process groups
if command -v bun &> /dev/null; then
    bun run dev > "../$FRONTEND_LOG" 2>&1 &
else
    npm run dev > "../$FRONTEND_LOG" 2>&1 &
fi
FRONTEND_PID=$!
echo $FRONTEND_PID > "../$FRONTEND_PID_FILE"
set +m  # Disable job control

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
