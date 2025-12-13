.PHONY: run start build test migrate-up migrate-down clean player-ingest

run: ## Run the API server
	go run cmd/api/main.go

start-db: ## Start PostgreSQL database
	@echo "🚀 Starting PostgreSQL database..."
	@docker ps -q --filter "name=football-postgres" | grep -q . && echo "✅ Database already running" || docker start football-postgres
	@echo "⏳ Waiting for database to be ready..."
	@sleep 2

start: ## Start the API server (alias for run)
	@echo "🚀 Starting backend API server on port 8080..."
	@make start-db
	go run cmd/api/main.go

build: ## Build the binary
	go build -o bin/api cmd/api/main.go

test: ## Run tests
	go test -v -cover ./...

test-coverage: ## Run tests with coverage
	go test -v -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out

migrate-up: ## Run database migrations
	go run cmd/migrate/main.go up

migrate-down: ## Rollback last migration
	go run cmd/migrate/main.go down

migrate-create: ## Create new migration (usage: make migrate-create name=create_users_table)
	@read -p "Enter migration name: " name; \
	migrate create -ext sql -dir migrations -seq $$name

ingest: ## Ingest data
	@echo "🚀 Starting data ingestion..."
	@echo "⚠️  This will take ~5 minutes (rate limiting: 10 req/min)"
	go run cmd/ingest/main.go

player-ingest: ## Stub command for player & lineup ingestion (Phase 2)
	@echo "Running player data ingestion..."
	go run cmd/player_ingest/main.go

generate-player-data: ## Generate realistic player data from match scores
	@echo "Generating realistic player data from match scores..."
	go run cmd/generate_player_data/main.go

clean: ## Clean build artifacts
	rm -rf bin/
	rm -f coverage.out
	go clean

deps: ## Download dependencies
	go mod download
	go mod tidy

lint: ## Run linter
	golangci-lint run

fmt: ## Format code
	go fmt ./...
