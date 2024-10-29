#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load development environment
if [ -f ".env.development" ]; then
    set -a
    source ".env.development"
    set +a
else
    echo -e "${RED}Error: .env.development file not found${NC}"
    echo -e "${YELLOW}Run setup-env.sh -e development to create it${NC}"
    exit 1
fi

# Function to check if docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running${NC}"
        exit 1
    fi
}

# Function to start development environment
start_dev() {
    source ".env.development"
    
    echo -e "${BLUE}Starting development environment...${NC}"
    
    # Build and start services
    docker compose -f docker-compose.dev.yml --env-file .env.development up --build -d
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to start development environment${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Development environment is ready!${NC}"
    echo -e "${GREEN}Frontend: ${VITE_API_URL}${NC}"
    echo -e "${GREEN}Backend: http://localhost:${BACKEND_PORT}${NC}"
}

# Function to stop development environment
stop_dev() {
    echo -e "${YELLOW}Stopping development environment...${NC}"
    docker compose -f docker-compose.dev.yml down
}

# Function to clean development environment
clean_dev() {
    echo -e "${YELLOW}Cleaning development environment...${NC}"
    
    # Stop containers and remove volumes
    docker compose -f docker-compose.dev.yml down -v
    
    # Remove development artifacts
    echo -e "${YELLOW}Removing development artifacts...${NC}"
    rm -rf frontend/node_modules frontend/dist
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    
    echo -e "${GREEN}Development environment cleaned!${NC}"
}

# Function to show logs
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker compose -f docker-compose.dev.yml logs -f
    else
        docker compose -f docker-compose.dev.yml logs -f $service
    fi
}

# Function to rebuild specific service
rebuild_service() {
    local service=$1
    if [ -z "$service" ]; then
        echo -e "${RED}Error: Service name required${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Rebuilding ${service}...${NC}"
    docker compose -f docker-compose.dev.yml --env-file .env.development up -d --build $service
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Service ${service} rebuilt successfully${NC}"
    else
        echo -e "${RED}Failed to rebuild ${service}${NC}"
        exit 1
    fi
}

# Show help message
show_help() {
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  start         Start development environment"
    echo "  stop          Stop development environment"
    echo "  clean         Clean development environment"
    echo "  logs [service] Show logs (all services if no service specified)"
    echo "  rebuild [service] Rebuild specific service"
    echo "  help          Show this help message"
}

# Main script
case "$1" in
    start)
        check_docker
        start_dev
        ;;
    stop)
        stop_dev
        ;;
    clean)
        clean_dev
        ;;
    logs)
        show_logs $2
        ;;
    rebuild)
        rebuild_service $2
        ;;
    help)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac