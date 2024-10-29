#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
SKIP_TESTS=false
PUSH=false
CLEAN=false
DEPLOY=false

# Function to display help
show_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -e, --environment    Set environment (development|production) (default: development)"
    echo "  -p, --push          Push images to registry"
    echo "  -c, --clean         Clean before building"
    echo "  -s, --skip-tests    Skip running tests"
    echo "  -d, --deploy        Deploy after building"
    echo "  -h, --help          Show this help message"
    exit 0
}

# Function to validate environment
validate_environment() {
    local env_file=".env.${ENVIRONMENT}"
    if [ ! -f "$env_file" ]; then
        echo -e "${RED}Error: Environment file $env_file not found${NC}"
        echo -e "${YELLOW}Run setup-env.sh to create environment files${NC}"
        exit 1
    fi

    # Source environment variables
    set -a
    source "$env_file"
    set +a

    # Validate required variables
    local required_vars=(
        "APP_NAME"
        "DOCKER_REGISTRY"
        "TAG"
        "VITE_API_URL"
        "VITE_WS_URL"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo -e "${RED}Error: Required variable $var is not set in $env_file${NC}"
            exit 1
        fi
    done
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
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
        rm -rf frontend/dist
        rm -rf frontend/node_modules
        
        # Clean backend
        find backend -type d -name "__pycache__" -exec rm -rf {} +
        find backend -type f -name "*.pyc" -delete
        rm -rf backend/venv
        
        echo -e "${GREEN}Clean completed${NC}"
    fi
}

# Function to build frontend
build_frontend() {
    echo -e "${BLUE}Building frontend for ${ENVIRONMENT}...${NC}"
    
    local dockerfile="frontend/Dockerfile"
    if [ "$ENVIRONMENT" = "development" ]; then
        dockerfile="frontend/Dockerfile.dev"
    fi

    # Build frontend image
    docker build \
        --build-arg VITE_API_URL="${VITE_API_URL}" \
        --build-arg VITE_WS_URL="${VITE_WS_URL}" \
        --build-arg NODE_ENV="${ENVIRONMENT}" \
        -f "${dockerfile}" \
        -t "${DOCKER_REGISTRY}/${APP_NAME}-frontend:${TAG}" \
        ./frontend

    if [ $? -ne 0 ]; then
        echo -e "${RED}Frontend build failed${NC}"
        exit 1
    fi
}

# Function to build backend
build_backend() {
    echo -e "${BLUE}Building backend for ${ENVIRONMENT}...${NC}"
    
    local dockerfile="backend/Dockerfile"
    if [ "$ENVIRONMENT" = "development" ]; then
        dockerfile="backend/Dockerfile.dev"
    fi

    # Build backend image
    docker build \
        --build-arg ENVIRONMENT="${ENVIRONMENT}" \
        -f "${dockerfile}" \
        -t "${DOCKER_REGISTRY}/${APP_NAME}-backend:${TAG}" \
        ./backend

    if [ $? -ne 0 ]; then
        echo -e "${RED}Backend build failed${NC}"
        exit 1
    fi
}

# Function to run tests
run_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        echo -e "${YELLOW}Skipping tests...${NC}"
        return 0
    fi

    echo -e "${BLUE}Running tests...${NC}"

    # Frontend tests
    echo -e "${BLUE}Running frontend tests...${NC}"
    docker run --rm \
        -e NODE_ENV=test \
        "${DOCKER_REGISTRY}/${APP_NAME}-frontend:${TAG}" \
        npm test

    # Backend tests
    echo -e "${BLUE}Running backend tests...${NC}"
    docker run --rm \
        -e ENVIRONMENT=test \
        "${DOCKER_REGISTRY}/${APP_NAME}-backend:${TAG}" \
        python -m pytest

    if [ $? -ne 0 ]; then
        echo -e "${RED}Tests failed${NC}"
        exit 1
    fi
}

# Function to push images
push_images() {
    if [ "$PUSH" = true ]; then
        echo -e "${BLUE}Pushing images to registry...${NC}"
        
        # Push frontend image
        docker push "${DOCKER_REGISTRY}/${APP_NAME}-frontend:${TAG}"
        
        # Push backend image
        docker push "${DOCKER_REGISTRY}/${APP_NAME}-backend:${TAG}"
        
        # Tag and push latest if in production
        if [ "$ENVIRONMENT" = "production" ]; then
            docker tag "${DOCKER_REGISTRY}/${APP_NAME}-frontend:${TAG}" "${DOCKER_REGISTRY}/${APP_NAME}-frontend:latest"
            docker tag "${DOCKER_REGISTRY}/${APP_NAME}-backend:${TAG}" "${DOCKER_REGISTRY}/${APP_NAME}-backend:latest"
            docker push "${DOCKER_REGISTRY}/${APP_NAME}-frontend:latest"
            docker push "${DOCKER_REGISTRY}/${APP_NAME}-backend:latest"
        fi
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
        sudo cp .env.${ENVIRONMENT} "$DEPLOY_DIR}/.env"
        sudo cp -r nginx "$DEPLOY_DIR/"
        
        # Create SSL directory and generate initial certificates if they don't exist
        if [ ! -d "$DEPLOY_DIR/ssl" ]; then
            echo -e "${BLUE}Setting up SSL certificates...${NC}"
            sudo mkdir -p "$DEPLOY_DIR/ssl"
            sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout "$DEPLOY_DIR/ssl/privkey.pem" \
                -out "$DEPLOY_DIR/ssl/fullchain.pem" \
                -subj "/CN=aaryareddy.com"
        fi
        
        # Stop existing containers
        echo -e "${BLUE}Stopping existing containers...${NC}"
        cd "$DEPLOY_DIR"
        sudo docker compose down
        
        # Pull latest images
        echo -e "${BLUE}Pulling latest images...${NC}"
        sudo docker compose pull
        
        # Start new containers
        echo -e "${BLUE}Starting containers...${NC}"
        sudo docker compose up -d
        
        # Scale frontend if in production
        if [ "$ENVIRONMENT" = "production" ]; then
            echo -e "${BLUE}Scaling frontend servers...${NC}"
            sudo docker compose up -d --scale frontend=3
        fi
        
        # Check container health
        echo -e "${BLUE}Checking container health...${NC}"
        sleep 10
        if ! sudo docker compose ps | grep -q "Up"; then
            echo -e "${RED}Deployment failed: Containers are not healthy${NC}"
            sudo docker compose logs
            exit 1
        fi
        
        echo -e "${GREEN}Deployment completed successfully!${NC}"
    fi
}

# Main build process
main() {
    echo -e "${GREEN}Starting build process for ${ENVIRONMENT} environment${NC}"
    
    # Validate environment
    validate_environment
    
    # Clean if requested
    clean_build
    
    # Build images
    build_frontend
    build_backend
    
    # Run tests
    run_tests
    
    # Push images if requested
    push_images
    
    # Deploy if requested
    deploy_application
    
    echo -e "${GREEN}Process completed successfully!${NC}"
}

# Execute main function
main