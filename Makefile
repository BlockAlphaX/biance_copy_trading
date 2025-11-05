.PHONY: help setup install install-dev test lint format clean run run-dev stop logs docker-build docker-up docker-down deploy

PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := venv
VENV_BIN := $(VENV)/bin

help:  ## Show this help message
	@echo "Binance Copy Trading - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## Initial setup - create venv and install dependencies
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Installing dependencies..."
	$(VENV_BIN)/pip install --upgrade pip setuptools wheel
	$(VENV_BIN)/pip install -r requirements.txt
	$(VENV_BIN)/pip install -r requirements-web.txt
	@echo "Running database migrations..."
	$(VENV_BIN)/alembic upgrade head
	@echo "Setup complete! Activate venv with: source $(VENV)/bin/activate"

install:  ## Install production dependencies
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-web.txt

install-dev:  ## Install development dependencies
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-web.txt
	$(PIP) install pytest pytest-asyncio pytest-cov black flake8 mypy

test:  ## Run tests
	$(VENV_BIN)/pytest tests/ -v --cov=src --cov=web

test-unit:  ## Run unit tests only
	$(VENV_BIN)/pytest tests/unit/ -v

test-integration:  ## Run integration tests only
	$(VENV_BIN)/pytest tests/integration/ -v

test-e2e:  ## Run end-to-end tests only
	$(VENV_BIN)/pytest tests/e2e/ -v

lint:  ## Run linting
	$(VENV_BIN)/flake8 src/ web/ --max-line-length=120
	$(VENV_BIN)/mypy src/ web/ --ignore-missing-imports

format:  ## Format code with black
	$(VENV_BIN)/black src/ web/ tests/

clean:  ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage

run:  ## Run the web server
	$(VENV_BIN)/python web_server.py

run-dev:  ## Run the web server in development mode with auto-reload
	$(VENV_BIN)/uvicorn web.api.main:app --reload --host 0.0.0.0 --port 8000

run-trading:  ## Run the trading bot (futures)
	$(VENV_BIN)/python main_futures.py

start:  ## Start application using management script
	./scripts/manage.sh start

stop:  ## Stop application using management script
	./scripts/manage.sh stop

restart:  ## Restart application using management script
	./scripts/manage.sh restart

status:  ## Show application status
	./scripts/manage.sh status

logs:  ## Show application logs
	./scripts/manage.sh logs

follow:  ## Follow application logs in real-time
	./scripts/manage.sh follow

# Frontend commands
frontend-install:  ## Install frontend dependencies
	cd web/frontend && npm install

frontend-dev:  ## Run frontend in development mode
	cd web/frontend && npm run dev

frontend-build:  ## Build frontend for production
	cd web/frontend && npm run build

frontend-preview:  ## Preview frontend production build
	cd web/frontend && npm run preview

# Docker commands
docker-build:  ## Build Docker image
	docker build -t binance-copy-trading:latest .

docker-up:  ## Start Docker containers
	docker-compose up -d

docker-down:  ## Stop Docker containers
	docker-compose down

docker-logs:  ## Show Docker container logs
	docker-compose logs -f

docker-restart:  ## Restart Docker containers
	docker-compose restart

docker-clean:  ## Remove Docker containers and images
	docker-compose down -v
	docker rmi binance-copy-trading:latest 2>/dev/null || true

# Database commands
db-migrate:  ## Create a new database migration
	$(VENV_BIN)/alembic revision --autogenerate -m "$(msg)"

db-upgrade:  ## Upgrade database to latest migration
	$(VENV_BIN)/alembic upgrade head

db-downgrade:  ## Downgrade database by one migration
	$(VENV_BIN)/alembic downgrade -1

db-history:  ## Show migration history
	$(VENV_BIN)/alembic history

db-current:  ## Show current migration version
	$(VENV_BIN)/alembic current

# Deployment
deploy:  ## Deploy to remote server
	./deploy.sh

# Utility commands
check-config:  ## Validate configuration file
	@if [ -f config.futures.yaml ]; then \
		echo "Configuration file found: config.futures.yaml"; \
		$(VENV_BIN)/python -c "import yaml; yaml.safe_load(open('config.futures.yaml'))"; \
		echo "Configuration is valid!"; \
	else \
		echo "Error: config.futures.yaml not found"; \
		exit 1; \
	fi

create-config:  ## Create config from example
	@if [ ! -f config.futures.yaml ]; then \
		cp config.futures.example.yaml config.futures.yaml; \
		echo "Created config.futures.yaml from example"; \
		echo "Please edit it with your API keys"; \
	else \
		echo "config.futures.yaml already exists"; \
	fi

backup:  ## Backup database and logs
	@mkdir -p backups
	@tar -czf backups/backup-$$(date +%Y%m%d-%H%M%S).tar.gz data/ logs/ config.futures.yaml 2>/dev/null || true
	@echo "Backup created in backups/"

all: clean setup test  ## Clean, setup, and test
