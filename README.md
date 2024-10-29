# Circular Life Simulation

A real-time multi-species simulation inspired by Conway's Game of Life, featuring complex particle-based algorithms. Built with React, PixiJS, FastAPI, WebSockets, and Docker.

## 🚀 Features

- Real-time multi-species particle simulation
- Complex particle-based algorithms
- Responsive frontend with React and PixiJS
- FastAPI backend with WebSocket support
- Containerized deployment with Docker
- Scalable frontend architecture
- SQLite database for species persistence

## 🛠 Tech Stack

- **Frontend**: React, PixiJS, TypeScript, Vite
- **Backend**: FastAPI, Python, WebSockets
- **Database**: SQLite
- **Infrastructure**: Docker, Nginx
- **Build Tools**: Bash scripts, Environment management
- **Additional**: SSL/TLS with Certbot, Watchtower for updates

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js ≥ 18 (for local development)
- Python ≥ 3.11 (for local development)
- Bash shell

## 🏗 Project Structure

```
circular-life-simulation/
├── frontend/                 # Frontend React application
│   ├── src/
│   ├── Dockerfile
│   └── Dockerfile.dev
├── backend/                  # Backend FastAPI application
│   ├── app/
│   ├── Dockerfile
│   └── Dockerfile.dev
├── nginx/                    # Nginx configuration
│   └── conf.d/
├── scripts/                  # Build and deployment scripts
│   ├── build.sh
│   ├── dev-build.sh
│   └── setup-env.sh
└── docker-compose.yml        # Docker composition
```

## 🔧 Setup and Installation

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-username/circular-life-simulation.git
cd circular-life-simulation

# Make scripts executable
chmod +x scripts/*.sh

# Set up environment files
./scripts/setup-env.sh -e development
./scripts/setup-env.sh -e production -d your-domain.com -r your-registry
```

### 2. Environment Configuration

Update the environment files according to your needs:

```bash
# Development environment
nano .env.development

# Production environment
nano .env.production
```

Key environment variables:
```env
# Application
APP_NAME=circular-life-simulation
ENVIRONMENT=development|production

# Docker Registry
DOCKER_REGISTRY=your-registry
TAG=latest

# Domain Configuration
DOMAIN=localhost|your-domain.com
SSL_EMAIL=your@email.com

# Frontend URLs
VITE_API_URL=http://localhost:8000|https://your-domain.com/api
VITE_WS_URL=ws://localhost:8000/ws|wss://your-domain.com/ws
```

### 3. Local Development

```bash
# Start development environment
./scripts/dev-build.sh start

# View logs
./scripts/dev-build.sh logs

# Rebuild specific service
./scripts/dev-build.sh rebuild frontend

# Stop development environment
./scripts/dev-build.sh stop

# Clean development environment
./scripts/dev-build.sh clean
```

### 4. Production Build

```bash
# Build for production
./scripts/build.sh -e production -p

# Build with clean option
./scripts/build.sh -e production -c -p

# Build without running tests
./scripts/build.sh -e production -s -p
```

## 🚀 Deployment

### 1. Hetzner Setup

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Configure firewall
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

### 2. SSL Certificate Setup

```bash
# Initialize SSL certificates
./scripts/init-letsencrypt.sh
```

### 3. Deploy Application

```bash
# Deploy with production configuration
docker compose -f docker-compose.yml up -d

# Scale frontend replicas
docker compose up -d --scale frontend=3
```

## 🔍 Monitoring and Maintenance

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f frontend
```

### Update Services

```bash
# Pull latest images
docker compose pull

# Restart services
docker compose up -d
```

### Backup Database

```bash
# Create backup
docker compose exec backend ./backup.sh

# Restore backup
docker compose exec backend ./restore.sh backup_file.sql
```

## 🛠 Development Commands

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev

# Run tests
npm test
```

### Backend Development

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --reload
```

## 🔐 Security Notes

- Always use HTTPS in production
- Keep environment files secure and never commit them to version control
- Regularly update dependencies and Docker images
- Monitor logs for suspicious activities
- Backup database regularly

## 📝 Scripts Reference

### build.sh Options
```bash
./scripts/build.sh [options]
  -e, --environment    Set environment (development|production)
  -p, --push          Push images to registry
  -c, --clean         Clean before building
  -s, --skip-tests    Skip running tests
  -h, --help          Show help message
```

### dev-build.sh Commands
```bash
./scripts/dev-build.sh [command] [options]
  start         Start development environment
  stop          Stop development environment
  clean         Clean development environment
  logs          Show logs (all services if no service specified)
  rebuild       Rebuild specific service
  help          Show help message
```

### setup-env.sh Options
```bash
./scripts/setup-env.sh [options]
  -e, --environment    Set environment (development|production)
  -d, --domain        Set domain name
  -r, --reg