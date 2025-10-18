#!/bin/bash

# dev.sh - Start local development environment using Docker Compose
# Usage: ./scripts/dev.sh [OPTIONS]
# Options:
#   --backend-only    Start only the backend service
#   --logs           Follow logs after starting
#   --build          Force rebuild containers
#   --down           Stop all services
#   --help           Show this help message

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.dev.yml"
PROJECT_NAME="gameoflife-dev"

# Parse arguments
BACKEND_ONLY=false
FOLLOW_LOGS=false
FORCE_BUILD=false
STOP_SERVICES=false

print_help() {
    echo "Game of Life - Development Environment"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --backend-only    Start only the backend service"
    echo "  --logs           Follow logs after starting services"
    echo "  --build          Force rebuild containers before starting"
    echo "  --down           Stop and remove all development containers"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Start all services"
    echo "  $0 --backend-only --logs     # Start backend only and show logs"
    echo "  $0 --build                   # Rebuild and start all services"
    echo "  $0 --down                    # Stop all services"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        --logs)
            FOLLOW_LOGS=true
            shift
            ;;
        --build)
            FORCE_BUILD=true
            shift
            ;;
        --down)
            STOP_SERVICES=true
            shift
            ;;
        --help)
            print_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_help
            exit 1
            ;;
    esac
done

# Stop services if requested
if [ "$STOP_SERVICES" = true ]; then
    echo -e "${YELLOW}Stopping development services...${NC}"
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
    echo -e "${GREEN}Services stopped successfully${NC}"
    exit 0
fi

# Check if .env.development exists
if [ ! -f .env.development ]; then
    echo -e "${RED}Error: .env.development not found${NC}"
    echo "Please create .env.development based on .env.example"
    exit 1
fi

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo -e "${YELLOW}Creating .env.local from template...${NC}"
    cp .env.local.example .env.local
    echo -e "${GREEN}Created .env.local - customize as needed${NC}"
fi

# Determine which services to start
SERVICES=""
if [ "$BACKEND_ONLY" = true ]; then
    SERVICES="backend"
    echo -e "${BLUE}Starting backend service only...${NC}"
else
    echo -e "${BLUE}Starting all development services...${NC}"
fi

# Build arguments
BUILD_ARGS=""
if [ "$FORCE_BUILD" = true ]; then
    BUILD_ARGS="--build"
fi

# Start services
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d $BUILD_ARGS $SERVICES

# Wait a moment for services to initialize
sleep 2

# Check service status
echo ""
echo -e "${GREEN}Services started successfully!${NC}"
echo ""
echo -e "${BLUE}Service URLs:${NC}"
if [ "$BACKEND_ONLY" = true ]; then
    echo "  Backend API: http://localhost:8000"
    echo "  WebSocket:   ws://localhost:8000/ws/simulation"
    echo "  Health:      http://localhost:8000/api/health"
    echo ""
    echo -e "${YELLOW}Note: Frontend not started. Run manually with:${NC}"
    echo "  cd client && npm run dev"
else
    echo "  Frontend:    http://localhost:5173"
    echo "  Backend API: http://localhost:8000"
    echo "  WebSocket:   ws://localhost:8000/ws/simulation"
    echo "  Health:      http://localhost:8000/api/health"
fi

echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  View logs:        docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f"
echo "  Stop services:    ./scripts/dev.sh --down"
echo "  Restart backend:  docker compose -f $COMPOSE_FILE -p $PROJECT_NAME restart backend"
echo "  Shell in backend: docker compose -f $COMPOSE_FILE -p $PROJECT_NAME exec backend bash"

# Follow logs if requested
if [ "$FOLLOW_LOGS" = true ]; then
    echo ""
    echo -e "${BLUE}Following logs (Ctrl+C to exit)...${NC}"
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f $SERVICES
fi
