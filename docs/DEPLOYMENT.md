# 🚀 Deployment Guide - Football Match Prediction Platform

## Overview

This guide will help you deploy your Football Match Prediction Platform to your DigitalOcean droplet. The deployment is **100% FREE** using your existing infrastructure.

**Stack:**

- Frontend: Next.js (static build)
- Backend: Go API server
- ML Service: Python FastAPI
- Database: PostgreSQL
- Web Server: Caddy (auto HTTPS)

**Cost: $0/month** ✅

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] DigitalOcean droplet (minimum 2GB RAM)
- [ ] Domain or subdomain (e.g., `football.yourdomain.com`)
- [ ] Football-data.org API key (free tier)
- [ ] SSH access to your droplet
- [ ] PostgreSQL database set up
- [ ] All services tested locally

---

## 🔧 Step 1: Prepare Your Droplet

### 1.1 SSH into your droplet

```bash
ssh root@your-droplet-ip
```

### 1.2 Update system

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.3 Install required software

**Install Node.js 20 LTS**

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version  # Verify installation
```

**Install Go 1.21+**

```bash
cd /tmp
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc
go version  # Verify installation
```

**Install Python 3.11+**

```bash
sudo apt install -y python3 python3-pip python3-venv
python3 --version  # Verify installation
```

**Install Caddy**

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
caddy version  # Verify installation
```

**Install Git**

```bash
sudo apt install -y git
```

---

## 📦 Step 2: Deploy Application Code

### 2.1 Create project directory

```bash
sudo mkdir -p /var/www/football-prediction
sudo chown $USER:$USER /var/www/football-prediction
cd /var/www/football-prediction
```

### 2.2 Clone repository

```bash
# Replace with your actual repository URL
git clone https://github.com/yourusername/football-prediction.git .

# Or if using SSH
# git clone git@github.com:yourusername/football-prediction.git .
```

### 2.3 Create environment file

```bash
cp .env.example .env
nano .env
```

**Configure your .env file:**

```bash
# Football API
FOOTBALL_API_KEY=your_api_key_here

# Database
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/football_predictions

# Backend API
PORT=8080
ENVIRONMENT=production
GO_ENV=production

# ML Service
ML_SERVICE_URL=http://localhost:8000
PYTHON_ENV=production

# Frontend
NEXT_PUBLIC_API_URL=https://football.yourdomain.com/api
```

---

## 🏗️ Step 3: Build Application

### 3.1 Build Frontend

```bash
cd /var/www/football-prediction/frontend

# Install dependencies
npm install --production

# Build for production
npm run build

# Verify build
ls -la .next/
```

### 3.2 Build Backend

```bash
cd /var/www/football-prediction/backend

# Download Go dependencies
go mod download

# Build binary
go build -o football-api cmd/api/main.go

# Make executable
chmod +x football-api

# Verify build
./football-api --version || echo "Binary created successfully"
```

### 3.3 Setup ML Service

```bash
cd /var/www/football-prediction/ml-service

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deactivate
deactivate

# Verify
ls -la venv/
```

---

## 🔐 Step 4: Create Systemd Services

### 4.1 Backend API Service

Create service file:

```bash
sudo nano /etc/systemd/system/football-api.service
```

Add this content:

```ini
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
```

### 4.2 ML Service

Create service file:

```bash
sudo nano /etc/systemd/system/football-ml.service
```

Add this content:

```ini
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
```

### 4.3 Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/football-prediction
sudo chmod +x /var/www/football-prediction/backend/football-api
```

### 4.4 Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable football-api
sudo systemctl enable football-ml

# Start services
sudo systemctl start football-api
sudo systemctl start football-ml

# Check status
sudo systemctl status football-api
sudo systemctl status football-ml
```

---

## 🌐 Step 5: Configure Caddy Web Server

### 5.1 Create Caddyfile

```bash
sudo nano /etc/caddy/Caddyfile
```

### 5.2 Add Configuration

```caddy
# Replace with your actual subdomain
football.yourdomain.com {
    # Serve Next.js static files
    root * /var/www/football-prediction/frontend/.next/standalone

    # API proxy to Go backend
    handle /api/* {
        reverse_proxy localhost:8080
    }

    # Static assets with caching
    handle /_next/static/* {
        file_server
        header Cache-Control "public, max-age=31536000, immutable"
    }

    # Default file server
    file_server

    # Compression
    encode gzip

    # Security headers
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }

    # Logging
    log {
        output file /var/log/caddy/football.log
        format json
    }
}

# Redirect www to non-www
www.football.yourdomain.com {
    redir https://football.yourdomain.com{uri} permanent
}
```

### 5.3 Create log directory

```bash
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy
```

### 5.4 Validate and restart Caddy

```bash
# Validate configuration
sudo caddy validate --config /etc/caddy/Caddyfile

# Restart Caddy
sudo systemctl restart caddy

# Check status
sudo systemctl status caddy
```

---

## 🔗 Step 6: Configure DNS

### 6.1 Add DNS Record

Log in to your domain registrar and add an A record:

- **Type**: A
- **Name**: football (or your chosen subdomain)
- **Value**: Your droplet's IP address
- **TTL**: 300 (5 minutes)

### 6.2 Verify DNS Propagation

```bash
# Check DNS resolution
nslookup football.yourdomain.com

# Or use dig
dig football.yourdomain.com
```

**Note**: DNS propagation can take 5-30 minutes.

---

## ✅ Step 7: Verify Deployment

### 7.1 Check Services

```bash
# Check all services are running
sudo systemctl status football-api football-ml caddy postgresql

# Check if services are listening on correct ports
sudo netstat -tulpn | grep -E '8080|8000|80|443'
```

### 7.2 Test Endpoints

```bash
# Test backend API
curl http://localhost:8080/health

# Test ML service
curl http://localhost:8000/health

# Test via Caddy (after DNS propagates)
curl https://football.yourdomain.com/api/health
```

### 7.3 View Logs

```bash
# Backend API logs
sudo journalctl -u football-api -f

# ML service logs
sudo journalctl -u football-ml -f

# Caddy logs
sudo journalctl -u caddy -f

# Or view Caddy access logs
sudo tail -f /var/log/caddy/football.log
```

---

## 🔄 Step 8: Setup Database Backups

### 8.1 Create backup script

```bash
sudo nano /usr/local/bin/backup-football-db.sh
```

Add this content:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/football-db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="football_predictions"

mkdir -p $BACKUP_DIR
pg_dump $DB_NAME | gzip > "$BACKUP_DIR/football_db_$TIMESTAMP.sql.gz"
find $BACKUP_DIR -name "football_db_*.sql.gz" -mtime +7 -delete
echo "Backup completed: football_db_$TIMESTAMP.sql.gz"
```

### 8.2 Make executable

```bash
sudo chmod +x /usr/local/bin/backup-football-db.sh
```

### 8.3 Add to crontab (daily at 2 AM)

```bash
sudo crontab -e
```

Add this line:

```
0 2 * * * /usr/local/bin/backup-football-db.sh >> /var/log/football-backup.log 2>&1
```

---

## 🔄 Updating the Application

### Quick Update Script

```bash
cd /var/www/football-prediction

# Pull latest code
git pull origin main

# Rebuild frontend
cd frontend
npm install
npm run build

# Rebuild backend
cd ../backend
go build -o football-api cmd/api/main.go

# Update ML service
cd ../ml-service
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Restart services
sudo systemctl restart football-api
sudo systemctl restart football-ml
sudo systemctl reload caddy

# Check status
sudo systemctl status football-api football-ml
```

---

## 🐛 Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u football-api -n 50
sudo journalctl -u football-ml -n 50

# Check if port is already in use
sudo netstat -tulpn | grep :8080
sudo netstat -tulpn | grep :8000
```

### Frontend not loading

```bash
# Check Caddy config
sudo caddy validate --config /etc/caddy/Caddyfile

# Check Caddy logs
sudo journalctl -u caddy -n 50

# Verify build exists
ls -la /var/www/football-prediction/frontend/.next/
```

### Database connection issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U postgres -d football_predictions -c "SELECT 1;"
```

### SSL certificate issues

```bash
# Caddy auto-provisions SSL, but if issues occur:
sudo systemctl restart caddy

# Check Caddy logs for certificate errors
sudo journalctl -u caddy -f
```

---

## 📊 Monitoring

### Check Resource Usage

```bash
# Memory
free -h

# Disk
df -h

# CPU
top

# Service status
sudo systemctl status football-api football-ml caddy
```

### View Real-time Logs

```bash
# All services
sudo journalctl -f

# Specific service
sudo journalctl -u football-api -f
```

---

## 🎯 Post-Deployment Checklist

- [ ] All services running (API, ML, Caddy, PostgreSQL)
- [ ] DNS pointing to droplet IP
- [ ] HTTPS working (Caddy auto-provisions)
- [ ] Frontend loads correctly
- [ ] API endpoints responding
- [ ] ML predictions working
- [ ] Database backups configured
- [ ] Logs accessible and rotating
- [ ] Resource usage acceptable

---

## 🚀 Next Steps

1. **Test thoroughly**: Visit https://football.yourdomain.com
2. **Monitor for 24 hours**: Check logs and resource usage
3. **Share with friends**: Get initial feedback
4. **Track metrics**: User engagement, prediction accuracy
5. **Plan improvements**: Based on user feedback

---

## 💰 Cost Summary

- **Droplet**: $0 (existing)
- **Domain**: $0 (subdomain)
- **SSL**: $0 (Caddy auto Let's Encrypt)
- **APIs**: $0 (free tier)
- **Total**: **$0/month** 🎉

---

## 📞 Support

If you encounter issues:

1. Check logs: `sudo journalctl -u <service-name> -n 50`
2. Verify services: `sudo systemctl status <service-name>`
3. Check resources: `free -h` and `df -h`
4. Review this guide's troubleshooting section

---

**Deployment Date**: **\*\***\_**\*\***
**Domain**: football.yourdomain.com
**Droplet IP**: **\*\***\_**\*\***

---

_Good luck with your deployment! 🚀⚽_
