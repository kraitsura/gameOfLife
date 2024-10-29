#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
CLEAN=false
DEPLOY=false

# Function to display help
show_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -e, --environment    Set environment (development|production) (default: development)"
    echo "  -c, --clean         Clean before building"
    echo "  -d, --deploy        Deploy after building"
    echo "  -h, --help          Show this help message"
    exit 0
}

# Function to validate environment
validate_environment() {
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}No .env file found, creating default environment variables...${NC}"
        cat > .env << EOL
VITE_WS_URL=wss://simulation.aaryareddy.com/simulation/ws/simulation
APP_NAME=simulation
EOL
    fi

    # Source environment variables
    set -a
    source ".env"
    set +a
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -d|--deploy)
            DEPLOY=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            ;;
    esac
done

# Function to clean build artifacts
clean_build() {
    if [ "$CLEAN" = true ]; then
        echo -e "${BLUE}Cleaning build artifacts...${NC}"
        
        # Clean frontend
        rm -rf client/dist
        rm -rf client/node_modules
        
        # Clean backend
        find server -type d -name "__pycache__" -exec rm -rf {} +
        find server -type f -name "*.pyc" -delete
        
        echo -e "${GREEN}Clean completed${NC}"
    fi
}

# Function to deploy application
deploy_application() {
    if [ "$DEPLOY" = true ]; then
        echo -e "${BLUE}Deploying application...${NC}"
        
        # Create deployment directory if it doesn't exist
        DEPLOY_DIR="/opt/simulation"
        sudo mkdir -p "$DEPLOY_DIR"
        
        # Copy necessary files
        echo -e "${BLUE}Copying deployment files...${NC}"
        sudo cp docker-compose.yml "$DEPLOY_DIR/"
        sudo cp .env "$DEPLOY_DIR/.env"
        sudo cp -r nginx "$DEPLOY_DIR/"
        
        # Copy application code
        sudo cp -r client "$DEPLOY_DIR/"
        sudo cp -r server "$DEPLOY_DIR/"
        
        # Set permissions
        sudo chown -R root:root "$DEPLOY_DIR"
        
        # Navigate to deployment directory
        cd "$DEPLOY_DIR" || exit
        
        # Stop existing containers
        echo -e "${BLUE}Stopping existing containers...${NC}"
        sudo docker compose down
        
        # Start new containers
        echo -e "${BLUE}Starting containers...${NC}"
        sudo docker compose up -d --build
        
        # Check container health
        echo -e "${BLUE}Checking container health...${NC}"
        sleep 10
        if ! sudo docker compose ps | grep -q "Up"; then
            echo -e "${RED}Deployment failed: Containers are not healthy${NC}"
            sudo docker compose logs
            exit 1
        fi
        
        echo -e "${GREEN}Deployment completed successfully!${NC}"
        echo -e "${GREEN}Application is now available at simulation.aaryareddy.com/simulation${NC}"
    fi
}

# Main build process
main() {
    echo -e "${GREEN}Starting build process for ${ENVIRONMENT} environment${NC}"
    
    # Validate environment
    validate_environment
    
    # Clean if requested
    clean_build
    
    # Deploy if requested
    deploy_application
    
    echo -e "${GREEN}Process completed successfully!${NC}"
}

# Execute main function
main