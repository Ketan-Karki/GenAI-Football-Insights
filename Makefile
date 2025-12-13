.PHONY: help install dev build test clean deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && go mod download
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing ML service dependencies..."
	@if [ ! -d "ml-service/venv" ]; then \
		cd ml-service && python3 -m venv venv; \
	fi
	cd ml-service && source venv/bin/activate && pip install -r requirements.txt

start-db: ## Start PostgreSQL database
	@echo "🚀 Starting PostgreSQL database..."
	@docker ps -q --filter "name=football-postgres" | grep -q . && echo "✅ Database already running" || docker start football-postgres || docker run --name football-postgres -e POSTGRES_USER=ketan -e POSTGRES_PASSWORD=password -e POSTGRES_DB=football_db -p 5432:5432 -d postgres:15
	@echo "⏳ Waiting for database to be ready..."
	@sleep 2

dev: ## Start all services in development mode
	@echo "Starting all services..."
	@make start-db
	@make -j3 dev-backend dev-frontend dev-ml

start-backend: ## Start backend API server
	@echo "🚀 Starting backend API server on port 8080..."
	@make start-db
	cd backend && go run cmd/api/main.go

start-frontend: ## Start frontend dev server
	@echo "🚀 Starting frontend dev server on port 3000..."
	cd frontend && npm run dev

start-ml: ## Start ML service
	@echo "🚀 Starting ML service on port 8000..."
	@if [ ! -d "ml-service/venv" ]; then \
		echo "⚠️  Virtual environment not found. Creating it..."; \
		cd ml-service && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt; \
	fi
	cd ml-service && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-backend: ## Start backend API server (alias)
	@make start-backend

dev-frontend: ## Start frontend dev server (alias)
	@make start-frontend

dev-ml: ## Start ML service (alias)
	@cd ml-service && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

build: ## Build all services for production
	@echo "Building backend..."
	cd backend && go build -o bin/api cmd/api/main.go
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo "Done!"

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && go test ./...
	@echo "Running frontend tests..."
	cd frontend && npm test
	@echo "Running ML service tests..."
	cd ml-service && pytest

clean: ## Clean build artifacts
	rm -rf backend/bin
	rm -rf frontend/.next
	rm -rf frontend/out
	rm -rf ml-service/__pycache__
	rm -rf ml-service/.pytest_cache

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

stop-db: ## Stop PostgreSQL database
	@echo "🛑 Stopping PostgreSQL database..."
	@docker stop football-postgres || true

stop-all: ## Stop all services
	@echo "🛑 Stopping all services..."
	@docker stop football-postgres || true
	@pkill -f "go run cmd/api/main.go" || true
	@pkill -f "next dev" || true
	@pkill -f "uvicorn app.main:app" || true
	@echo "✅ All services stopped"

migrate-up: ## Run database migrations
	cd backend && go run cmd/migrate/main.go up

migrate-down: ## Rollback database migrations
	cd backend && go run cmd/migrate/main.go down

deploy: ## Deploy to production (run on droplet)
	./deployment/deploy.sh

lint: ## Run linters
	cd backend && golangci-lint run
	cd frontend && npm run lint
	cd ml-service && flake8 app/
