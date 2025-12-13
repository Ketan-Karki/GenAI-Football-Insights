# 🚀 Quick Start Guide

Get the Football Prediction Platform running locally in 10 minutes!

## Prerequisites Check

```bash
# Check Go
go version  # Should be 1.21+

# Check Node.js
node --version  # Should be 18+

# Check Python
python3 --version  # Should be 3.11+

# Check PostgreSQL
psql --version  # Should be 16+
```

## Step 1: Clone & Setup

```bash
# Navigate to project
cd "Gen AI Football Project"

# Copy environment file
cp .env.example .env

# Edit .env and add your football-data.org API key
# Get free API key from: https://www.football-data.org/client/register
```

## Step 2: Setup PostgreSQL

### Option A: Using Docker (Recommended)

```bash
# Start PostgreSQL in Docker
docker run --name football-postgres \
  -e POSTGRES_USER=football_user \
  -e POSTGRES_PASSWORD=your_secure_password \
  -e POSTGRES_DB=football_db \
  -p 5432:5432 \
  -d postgres:16-alpine
```

### Option B: Local Installation

```bash
# macOS
brew install postgresql@16
brew services start postgresql@16

# Ubuntu/Debian
sudo apt install postgresql-16
sudo systemctl start postgresql

# Create database
createdb football_db
```

## Step 3: Install Dependencies

```bash
# Backend (Go)
cd backend
go mod download
cd ..

# Frontend (Next.js)
cd frontend
npm install
cd ..

# ML Service (Python)
cd ml-service
pip install -r requirements.txt
# Or use virtual environment:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

## Step 4: Run Database Migrations

```bash
cd backend
go run cmd/migrate/main.go up
# Or use make:
make migrate-up
cd ..
```

## Step 5: Start Services

Open 3 terminal windows:

### Terminal 1: Backend API

```bash
cd backend
go run cmd/api/main.go
# Or: make run

# Should see:
# INFO Successfully connected to database
# INFO Starting API server address=0.0.0.0:8080
```

### Terminal 2: ML Service

```bash
cd ml-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Or: make run

# Should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 3: Frontend

```bash
cd frontend
npm run dev

# Should see:
# ▲ Next.js 14.x.x
# - Local:        http://localhost:3000
```

## Step 6: Verify Everything Works

### Test Backend API

```bash
curl http://localhost:8080/health
# Expected: {"status":"healthy","timestamp":1234567890}
```

### Test ML Service

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","model_loaded":false}
```

### Test Frontend

Open browser: http://localhost:3000

## Step 7: Get Football Data

Register for free API key:

1. Go to https://www.football-data.org/client/register
2. Fill in the form (use your email)
3. Copy the API key from the email
4. Add to `.env`:
   ```
   FOOTBALL_API_KEY=your_actual_api_key_here
   ```

## Common Issues & Solutions

### Issue: "Database connection failed"

**Solution:**

```bash
# Check if PostgreSQL is running
docker ps  # For Docker
# Or
pg_isready  # For local install

# Check DATABASE_URL in .env matches your setup
```

### Issue: "Port already in use"

**Solution:**

```bash
# Find process using the port
lsof -i :8080  # For backend
lsof -i :8000  # For ML service
lsof -i :3000  # For frontend

# Kill the process
kill -9 <PID>
```

### Issue: "Go modules not found"

**Solution:**

```bash
cd backend
go mod download
go mod tidy
```

### Issue: "Python packages not found"

**Solution:**

```bash
cd ml-service
pip install --upgrade pip
pip install -r requirements.txt
```

## Next Steps

1. **Fetch Initial Data**

   ```bash
   # TODO: Add data ingestion script
   ```

2. **Train ML Models**

   ```bash
   cd ml-service
   make train
   ```

3. **Explore API**

   - API Docs: http://localhost:8080/api/v1
   - ML Docs: http://localhost:8000/docs (FastAPI auto-docs)

4. **Start Development**
   - Backend: `backend/cmd/api/main.go`
   - Frontend: `frontend/app/page.tsx`
   - ML Service: `ml-service/app/main.py`

## Development Workflow

```bash
# Run all services at once (from project root)
make dev

# Run tests
make test

# Build for production
make build
```

## Useful Commands

```bash
# View logs
docker logs football-postgres  # Database logs

# Access database
psql postgresql://football_user:your_secure_password@localhost:5432/football_db

# Reset database
cd backend
make migrate-down
make migrate-up
```

## Getting Help

- Check `docs/ROADMAP.md` for project overview
- Check `README.md` for detailed documentation
- Open an issue on GitHub

---

**You're all set!** 🎉 Start building amazing features!
