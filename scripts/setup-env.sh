#!/usr/bin/env bash
# Convert script to use LF line endings if needed
case `uname` in
    *CYGWIN*|*MINGW*|*MSYS*) sed -i 's/\r$//' "$0" ;;
esac

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
DOMAIN="localhost"
REGISTRY="local"

# Function to show help
show_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -e, --environment    Set environment (development|production)"
    echo "  -d, --domain        Set domain name"
    echo "  -r, --registry      Set docker registry"
    echo "  -h, --help          Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Function to generate random string
generate_random_string() {
    openssl rand -hex 16
}

# Function to create environment file
create_env_file() {
    local env_file=".env.${ENVIRONMENT}"
    local template_file=".env.example"
    
    # Check for existing .env file
    if [ -f ".env" ]; then
        echo -e "${YELLOW}Warning: A .env file exists in the root directory.${NC}"
        echo -e "${YELLOW}This may cause conflicts. Consider removing or renaming it.${NC}"
    fi

    if [ ! -f "$template_file" ]; then
        echo -e "${RED}Error: Template file $template_file not found${NC}"
        exit 1
    fi

    echo -e "${GREEN}Creating ${env_file}...${NC}"

    # Copy template
    cp "$template_file" "$env_file"

    # Update environment-specific values
    sed -i "s|ENVIRONMENT=.*|ENVIRONMENT=${ENVIRONMENT}|g" "$env_file"
    sed -i "s|DOCKER_REGISTRY=.*|DOCKER_REGISTRY=${REGISTRY}|g" "$env_file"
    sed -i "s|DOMAIN=.*|DOMAIN=${DOMAIN}|g" "$env_file"

    if [ "$ENVIRONMENT" = "production" ]; then
        # Update production-specific values
        sed -i "s|VITE_API_URL=.*|VITE_API_URL=https://${DOMAIN}/api|g" "$env_file"
        sed -i "s|VITE_WS_URL=.*|VITE_WS_URL=wss://${DOMAIN}/ws|g" "$env_file"
        sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=https://${DOMAIN}|g" "$env_file"
        sed -i "s|DEBUG=.*|DEBUG=false|g" "$env_file"
        sed -i "s|FRONTEND_REPLICAS=.*|FRONTEND_REPLICAS=3|g" "$env_file"
    else
        # Update development-specific values
        sed -i "s|VITE_API_URL=.*|VITE_API_URL=http://localhost:8000|g" "$env_file"
        sed -i "s|VITE_WS_URL=.*|VITE_WS_URL=ws://localhost:8000/ws|g" "$env_file"
        sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=http://localhost:3000|g" "$env_file"
        sed -i "s|DEBUG=.*|DEBUG=true|g" "$env_file"
        sed -i "s|FRONTEND_REPLICAS=.*|FRONTEND_REPLICAS=1|g" "$env_file"
    fi

    echo -e "${GREEN}Successfully created ${env_file}${NC}"
}

# Function to validate environment file
validate_env_file() {
    local env_file=".env.${ENVIRONMENT}"
    
    echo -e "${GREEN}Validating ${env_file}...${NC}"
    
    # Required variables
    local required_vars=(
        "APP_NAME"
        "ENVIRONMENT"
        "DOCKER_REGISTRY"
        "DOMAIN"
        "VITE_API_URL"
        "VITE_WS_URL"
        "BACKEND_HOST"
        "BACKEND_PORT"
        "CORS_ORIGINS"
        "DATABASE_URL"
    )

    local missing_vars=()
    
    # Source the env file
    source "$env_file"
    
    # Check for missing variables
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    # Report missing variables
    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo -e "${RED}Error: Missing required variables in ${env_file}:${NC}"
        printf '%s\n' "${missing_vars[@]}"
        exit 1
    fi
    
    echo -e "${GREEN}Environment file validation successful${NC}"
}

# Main function
main() {
    echo -e "${GREEN}Setting up environment for ${ENVIRONMENT}${NC}"
    
    # Create environment file
    create_env_file
    
    # Validate environment file
    validate_env_file
    
    echo -e "${GREEN}Environment setup completed successfully!${NC}"
    echo -e "${YELLOW}Don't forget to update sensitive values in ${ENVIRONMENT} environment file${NC}"
}

# Execute main function
main