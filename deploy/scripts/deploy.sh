#!/bin/bash

# Football Prediction Platform - Quick Deployment Script
# This script helps automate the deployment process

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   Football Prediction Platform - Deployment Script       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print step
print_step() {
    echo -e "\n${YELLOW}📌 $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running on droplet
print_step "Checking environment..."
if [ ! -f "/etc/os-release" ]; then
    print_error "This script should be run on your DigitalOcean droplet"
    exit 1
fi
print_success "Environment check passed"

# Get user input
print_step "Configuration"
read -p "Enter your domain/subdomain (e.g., football.yourdomain.com): " DOMAIN
read -p "Enter your Football API key: " API_KEY
read -p "Enter PostgreSQL password: " DB_PASSWORD

# Create project directory
print_step "Creating project directory..."
sudo mkdir -p /var/www/football-prediction
sudo chown $USER:$USER /var/www/football-prediction
print_success "Project directory created"

# Clone repository
print_step "Cloning repository..."
cd /var/www/football-prediction
read -p "Enter your repository URL: " REPO_URL
git clone $REPO_URL .
print_success "Repository cloned"

# Create .env file
print_step "Creating environment file..."
cat > .env << EOF
# Football API
FOOTBALL_API_KEY=$API_KEY

# Database
DATABASE_URL=postgresql://postgres:$DB_PASSWORD@localhost:5432/football_predictions

# Backend API
PORT=8080
ENVIRONMENT=production
GO_ENV=production

# ML Service
ML_SERVICE_URL=http://localhost:8000
PYTHON_ENV=production

# Frontend
NEXT_PUBLIC_API_URL=https://$DOMAIN/api
EOF
print_success "Environment file created"

# Build frontend
print_step "Building frontend..."
cd frontend
npm install --production
npm run build
print_success "Frontend built"

# Build backend
print_step "Building backend..."
cd ../backend
go mod download
go build -o football-api cmd/api/main.go
chmod +x football-api
print_success "Backend built"

# Setup ML service
print_step "Setting up ML service..."
cd ../ml-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
print_success "ML service setup complete"

# Create systemd services
print_step "Creating systemd services..."

# Backend service
sudo tee /etc/systemd/system/football-api.service > /dev/null << 'EOF'
[Unit]
Description=Football Prediction API Server
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/football-prediction/backend
EnvironmentFile=/var/www/football-prediction/.env
ExecStart=/var/www/football-prediction/backend/football-api
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# ML service
sudo tee /etc/systemd/system/football-ml.service > /dev/null << 'EOF'
[Unit]
Description=Football Prediction ML Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/football-prediction/ml-service
EnvironmentFile=/var/www/football-prediction/.env
ExecStart=/var/www/football-prediction/ml-service/venv/bin/python -m app.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd services created"

# Set permissions
print_step "Setting permissions..."
sudo chown -R www-data:www-data /var/www/football-prediction
sudo chmod +x /var/www/football-prediction/backend/football-api
print_success "Permissions set"

# Configure Caddy
print_step "Configuring Caddy..."
sudo tee /etc/caddy/Caddyfile > /dev/null << EOF
$DOMAIN {
    root * /var/www/football-prediction/frontend/.next/standalone
    
    handle /api/* {
        reverse_proxy localhost:8080
    }
    
    handle /_next/static/* {
        file_server
        header Cache-Control "public, max-age=31536000, immutable"
    }
    
    file_server
    encode gzip
    
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }
    
    log {
        output file /var/log/caddy/football.log
        format json
    }
}
EOF

sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy
print_success "Caddy configured"

# Start services
print_step "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable football-api football-ml
sudo systemctl start football-api football-ml
sudo systemctl restart caddy
print_success "Services started"

# Health checks
print_step "Running health checks..."
sleep 5

if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    print_success "Backend API is healthy"
else
    print_error "Backend API health check failed"
fi

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "ML service is healthy"
else
    print_error "ML service health check failed"
fi

# Final instructions
echo -e "\n${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              Deployment Complete! 🎉                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Configure DNS: Add A record for $DOMAIN pointing to this server's IP"
echo "2. Wait 5-30 minutes for DNS propagation"
echo "3. Visit https://$DOMAIN to see your site"
echo "4. Check logs: sudo journalctl -u football-api -f"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  View logs:    sudo journalctl -u football-api -f"
echo "  Restart API:  sudo systemctl restart football-api"
echo "  Restart ML:   sudo systemctl restart football-ml"
echo "  Check status: sudo systemctl status football-api football-ml"
echo ""
echo -e "${GREEN}Deployment successful! 🚀⚽${NC}"
