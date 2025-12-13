# 🚀 Dev Notes - Football Prediction Platform

## Dec 9-10, 2024 - Initial Setup

### Planning

- Budget: $78/month → $0/month (existing droplet + subdomain)
- Stack: Go + Next.js + Python ML + PostgreSQL
- Why PostgreSQL not SQLite: Concurrency (SQLite = single writer)

### What We Built

```
backend/          → Go API (port 8080)
ml-service/       → Python FastAPI (port 8000) ✅ Running
frontend/         → Next.js (pending)
```

### Backend (Go)

- `cmd/api/main.go` - API server with /health
- `migrations/` - PostgreSQL schema (competitions, teams, matches, standings, predictions)
- Commands: `make run`, `make migrate-up`

### ML Service (Python)

- FastAPI with /health, /predict endpoints
- Python 3.13 (NOT 3.14 - too new for pydantic)
- Setup: `./setup.sh` then `source venv/bin/activate`

### Issues Solved

1. SQLite → PostgreSQL (concurrency)
2. Python 3.14 → 3.13 (compatibility)
3. macOS pip → Use venv always
4. Local PostgreSQL@14 conflicting with Docker - stopped brew service

### Quick Commands

```bash
# Backend
cd backend && make run

# ML Service
cd ml-service && source venv/bin/activate && make run

# Database
make migrate-up
```

## Dec 11, 2024 - Full Stack MVP Complete

### Frontend (Next.js)

- shadcn/ui components with TailwindCSS
- Beautiful football-themed UI with gradients
- Real team logos from API (with fallback badges)
- 7 competitions: PL, La Liga, Bundesliga, Serie A, Ligue 1, CL, WC
- Match cards show team names in predictions (not "HOME WIN")
- Responsive design with smooth animations

### Data Ingestion

- `cmd/ingest/main.go` - Fetch historical matches
- Saves competitions, teams, matches to PostgreSQL
- Rate limiting: 10 req/min (free tier)
- Command: `make ingest`

### Status

✅ Backend API (port 8080) - real data
✅ Frontend (port 3000) - beautiful UI
✅ ML Service (port 8000) - mock predictions
✅ PostgreSQL (Docker) - ready
✅ API key configured - working

### Next

- [ ] Run data ingestion: `cd backend && make ingest`
- [ ] Train ML model with historical data
- [ ] Improve prediction accuracy
- [ ] Deploy to DigitalOcean

---

_Last: Dec 11, 2024_
