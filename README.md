# ⚽ AI Football Match Prediction Platform

AI-powered football match prediction platform with ML-based predictions for major leagues.

## 🎯 Features

- **Match Predictions**: Win/Draw/Loss probabilities using Random Forest + XGBoost
- **Live Standings**: Real-time league tables
- **Historical Data**: 2024-2025 and 2025-2026 seasons
- **Premium UI**: Material Design 3 with glassmorphism
- **Cost**: $0/month (100% free MVP)

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Next.js Frontend (Static)              │
│  - shadcn/ui + TailwindCSS              │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  Go API Server (Gin)                    │
│  - REST endpoints                        │
│  - Caching layer                         │
│  - Rate limiting                         │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  Python ML Service (FastAPI)            │
│  - Random Forest + XGBoost              │
│  - Match prediction engine               │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  PostgreSQL 16                          │
│  - Matches, teams, predictions          │
└─────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Go 1.21+
- Node.js 18+
- Python 3.11+
- PostgreSQL 16
- Docker (optional)

### Local Development

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd "Gen AI Football Project"
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start PostgreSQL**

   ```bash
   # Using Docker
   docker-compose up -d postgres

   # Or install locally
   brew install postgresql@16  # macOS
   sudo apt install postgresql-16  # Ubuntu
   ```

4. **Run database migrations**

   ```bash
   cd backend
   make migrate-up
   ```

5. **Start backend services**

   ```bash
   # Terminal 1: Go API
   cd backend
   make run

   # Terminal 2: Python ML Service
   cd ml-service
   make run
   ```

6. **Start frontend**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

7. **Access the app**
   - Frontend: http://localhost:3000
   - API: http://localhost:8080
   - ML Service: http://localhost:8000

## 📁 Project Structure

```
.
├── backend/              # Go API server
│   ├── cmd/
│   │   └── api/         # Main application
│   ├── internal/
│   │   ├── models/      # Data models
│   │   ├── handlers/    # HTTP handlers
│   │   ├── services/    # Business logic
│   │   └── repository/  # Database layer
│   ├── pkg/
│   │   ├── football/    # Football API client
│   │   └── cache/       # Caching utilities
│   └── migrations/      # SQL migrations
│
├── frontend/            # Next.js frontend
│   ├── app/            # App router pages
│   ├── components/     # React components
│   ├── lib/            # Utilities
│   └── public/         # Static assets
│
├── ml-service/         # Python ML service
│   ├── app/
│   │   ├── models/     # ML models
│   │   ├── api/        # FastAPI routes
│   │   └── training/   # Model training scripts
│   └── requirements.txt
│
├── deployment/         # Deployment configs
│   ├── systemd/       # Systemd service files
│   ├── caddy/         # Caddyfile
│   └── docker/        # Dockerfiles
│
└── docs/              # Documentation
```

## 🛠️ Development Commands

### Backend (Go)

```bash
cd backend
make run          # Run API server
make test         # Run tests
make build        # Build binary
make migrate-up   # Run migrations
make migrate-down # Rollback migrations
```

### Frontend (Next.js)

```bash
cd frontend
npm run dev       # Development server
npm run build     # Production build
npm run lint      # Lint code
```

### ML Service (Python)

```bash
cd ml-service
make run          # Run FastAPI server
make train        # Train ML models
make test         # Run tests
```

## 🌐 Deployment

Deploy to your DigitalOcean droplet:

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Clone repository
git clone <your-repo-url>
cd "Gen AI Football Project"

# Run deployment script
./deployment/deploy.sh
```

See [deployment guide](./docs/DEPLOYMENT.md) for details.

## 📊 Tech Stack

- **Backend**: Go 1.21, Gin, PostgreSQL
- **Frontend**: Next.js 14, React, TailwindCSS, shadcn/ui
- **ML**: Python 3.11, FastAPI, scikit-learn, XGBoost
- **Database**: PostgreSQL 16
- **Deployment**: Caddy, Systemd, DigitalOcean

## 🔑 Environment Variables

Create `.env` file in project root:

```env
# Football API
FOOTBALL_API_KEY=your_api_key_here
FOOTBALL_API_BASE_URL=https://api.football-data.org/v4

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/football_db

# API Server
API_PORT=8080
API_ENV=development

# ML Service
ML_SERVICE_URL=http://localhost:8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) first.

## 📧 Contact

For questions or support, open an issue on GitHub.
