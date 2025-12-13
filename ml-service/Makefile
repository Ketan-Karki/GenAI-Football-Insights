.PHONY: run install test train train-enhanced test-predict clean lint fmt

run: ## Run the ML service
	python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

install: ## Install dependencies
	python3 -m pip install -r requirements.txt

test: ## Run tests
	python3 -m pytest tests/ -v

train: ## Train ML models
	@echo "🚀 Training ML model..."
	@echo "This will take a few minutes..."
	python3 app/train.py

train-enhanced: ## Train enhanced ML model with player statistics
	@echo "🚀 Training enhanced ML model with player statistics..."
	@echo "   This will use 2,700+ historical matches as training data"
	@echo "   Features: team form, player stats, head-to-head, etc."
	@echo ""
	python3 app/train_enhanced.py

test-predict: ## Test prediction with enhanced model
	@echo "🧪 Testing enhanced prediction..."
	curl -X POST http://localhost:8000/predict \
		-H "Content-Type: application/json" \
		-d '{"home_team_id": 86, "away_team_id": 65, "matchday": 16}' | jq

clean: ## Clean cache and artifacts
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf models/*.pkl

lint: ## Run linter
	python3 -m flake8 app/

fmt: ## Format code
	python3 -m black app/
	isort app/
