#!/bin/bash
# cleanup-dev.sh - Force cleanup of development processes
# Use this script when dev-native.sh doesn't clean up properly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Cleaning up development processes...${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════${NC}"
echo ""

# Kill uvicorn processes
if pgrep -f "uvicorn app.main:app" > /dev/null 2>&1; then
    echo -e "${YELLOW}Killing uvicorn processes...${NC}"
    pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true
    echo -e "${GREEN}✓ Uvicorn processes terminated${NC}"
else
    echo "No uvicorn processes found"
fi

# Kill vite/npm processes from this project
if pgrep -f "vite.*gameOfLife" > /dev/null 2>&1; then
    echo -e "${YELLOW}Killing vite processes...${NC}"
    pkill -9 -f "vite.*gameOfLife" 2>/dev/null || true
    echo -e "${GREEN}✓ Vite processes terminated${NC}"
else
    echo "No vite processes found"
fi

# Clean PID files
if [ -d "scripts/pids" ]; then
    echo -e "${YELLOW}Removing PID files...${NC}"
    rm -f scripts/pids/*.pid
    echo -e "${GREEN}✓ PID files removed${NC}"
else
    echo "No PID directory found"
fi

# Optional: Clean log files (commented out by default)
# echo -e "${YELLOW}Removing log files...${NC}"
# rm -f scripts/logs/*.log
# echo -e "${GREEN}✓ Log files removed${NC}"

echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Cleanup complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo "You can now run: ./scripts/dev-native.sh"
