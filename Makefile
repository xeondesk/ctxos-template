# CtxOS Development Makefile
# Supercharge your development workflow with these handy commands

.PHONY: help install dev test build clean docker docs lint format benchmark security

# Default target
help: ## Show this help message
	@echo "🚀 CtxOS Development Commands"
	@echo "=============================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# INSTALLATION & SETUP
# =============================================================================

install: ## Install all dependencies (Python + Node)
	@echo "📦 Installing Python dependencies..."
	poetry install
	@echo "📦 Installing Node.js dependencies..."
	cd src && npm install
	@echo "✅ Installation complete!"

fix-deps: ## Fix frontend dependency conflicts
	@echo "🔧 Fixing frontend dependency conflicts..."
	cd src && rm -rf node_modules package-lock.json
	npm install
	@echo "✅ Dependencies fixed!"

install-dev: ## Install development dependencies
	@echo "📦 Installing development dependencies..."
	poetry install --with dev
	cd src && npm install
	@echo "✅ Dev installation complete!"

setup: ## Full project setup (install + init db)
	@echo "🔧 Setting up CtxOS development environment..."
	make install
	make init-db
	make env-file
	@echo "✅ Setup complete! Run 'make dev' to start development."

env-file: ## Create .env file from template
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file..."; \
		cp .env.example .env 2>/dev/null || echo "DATABASE_URL=postgresql://ctxos_user:ctxos_password@localhost:5432/ctxos\nREDIS_URL=redis://localhost:6379/0\nSECRET_KEY=your-secret-key-here\nDEBUG=true" > .env; \
		echo "✅ .env file created. Please update with your values."; \
	else \
		echo "✅ .env file already exists."; \
	fi

# =============================================================================
# DEVELOPMENT
# =============================================================================

dev: ## Start development environment (API + Frontend)
	@echo "🚀 Starting development environment..."
	@echo "📊 Starting services with Docker Compose..."
	docker-compose -f docker-compose.dev.yml up -d postgres-dev redis-dev elasticsearch-dev
	@echo "🐍 Starting Python API server..."
	poetry run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "⚛️ Starting frontend development server..."
	cd src && npm run dev &
	@echo "✅ Development environment started!"
	@echo "🌐 API: http://localhost:8000"
	@echo "🎨 Frontend: http://localhost:3000"
	@echo "📊 Grafana: http://localhost:3001"
	@echo "🔍 Prometheus: http://localhost:9090"

dev-api: ## Start only API server
	@echo "🐍 Starting API server..."
	poetry run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start only frontend
	@echo "⚛️ Starting frontend development server..."
	cd src && npm run dev

dev-services: ## Start only backend services (PostgreSQL, Redis, Elasticsearch)
	@echo "📊 Starting backend services..."
	docker-compose -f docker-compose.dev.yml up -d postgres-dev redis-dev elasticsearch-dev

stop: ## Stop all development services
	@echo "🛑 Stopping development environment..."
	pkill -f "uvicorn\|npm run dev" || true
	docker-compose -f docker-compose.dev.yml down
	@echo "✅ Services stopped."

restart: ## Restart development environment
	make stop
	sleep 2
	make dev

# =============================================================================
# DATABASE
# =============================================================================
: ## Initialize database with schema and seed data
init-db: ## Initialize database (migrations + seed data)
	@echo "🗄️ Initializing database..."
	@echo "📊 Starting PostgreSQL..."
	docker-compose -f docker-compose.dev.yml up -d postgres-dev
	sleep 5
	@echo "🔧 Running database migrations..."
	poetry run alembic upgrade head || echo "Alembic not configured, skipping migrations..."
	@echo "🌱 Seeding database..."
	poetry run python scripts/seed_data.py || echo "Seed script not found, skipping..."
	@echo "✅ Database initialized!"

reset-db: ## Reset database (drop and recreate)
	@echo "💥 Resetting database..."
	docker-compose -f docker-compose.dev.yml down
	docker volume rm ctxos-template_postgres_dev_data || true
	make init-db
	@echo "✅ Database reset complete!"

migrate: ## Run database migrations
	@echo "🔄 Running database migrations..."
	poetry run alembic upgrade head

migrate-create: ## Create new database migration (usage: make migrate-create MSG="add_user_table")
	@echo "📝 Creating new migration..."
	poetry run alembic revision --autogenerate -m "$(MSG)"

# =============================================================================
# TESTING
# =============================================================================

test: ## Run all tests (Python + Frontend)
	@echo "🧪 Running all tests..."
	make test-python
	make test-frontend
	@echo "✅ All tests completed!"

test-python: ## Run Python tests
	@echo "🐍 Running Python tests..."
	poetry run pytest tests/ -v --cov=core --cov=api --cov-report=html --cov-report=term-missing

test-frontend: ## Run frontend tests
	@echo "⚛️ Running frontend tests..."
	cd src && npm test

test-watch: ## Run Python tests in watch mode
	@echo "👀 Running Python tests in watch mode..."
	poetry run ptw tests/ --runner "python -m pytest {files} -v"

test-integration: ## Run integration tests
	@echo "🔗 Running integration tests..."
	poetry run pytest tests/integration/ -v

test-performance: ## Run performance benchmarks
	@echo "⚡ Running performance benchmarks..."
	poetry run python benchmarks/benchmark_runner.py

# =============================================================================
# CODE QUALITY
# =============================================================================

lint: ## Run all linting (Python + TypeScript)
	@echo "🔍 Running all linting..."
	make lint-python
	make lint-typescript
	@echo "✅ Linting complete!"

lint-python: ## Run Python linting
	@echo "🐍 Python linting..."
	poetry run flake8 core/ api/ engines/ collectors/ normalizers/ agents/ cli/
	poetry run black --check core/ api/ engines/ collectors/ normalizers/ agents/ cli/
	poetry run isort --check-only core/ api/ engines/ collectors/ normalizers/ agents/ cli/
	poetry run mypy core/ api/ engines/ collectors/ normalizers/ agents/ cli/ || true
	poetry run bandit -r core/ api/ engines/ collectors/ normalizers/ agents/ cli/ || true
	poetry run safety check || true

lint-typescript: ## Run TypeScript linting
	@echo "⚛️ TypeScript linting..."
	cd src && npm run lint
	cd src && npm audit --audit-level=moderate || true

format: ## Format all code (Python + TypeScript)
	@echo "🎨 Formatting all code..."
	make format-python
	make format-typescript
	@echo "✅ Code formatted!"

format-python: ## Format Python code
	@echo "🐍 Formatting Python code..."
	poetry run black core/ api/ engines/ collectors/ normalizers/ agents/ cli/
	poetry run isort core/ api/ engines/ collectors/ normalizers/ agents/ cli/
	poetry run autoflake --in-place --remove-all-unused-imports --remove-unused-variables --recursive core/ api/ engines/ collectors/ normalizers/ agents/ cli/ || true

format-typescript: ## Format TypeScript code
	@echo "⚛️ Formatting TypeScript code..."
	cd src && npm run format
	cd src && npx prettier --write .

format-check: ## Check if code is formatted
	@echo "🔍 Checking code formatting..."
	make lint-python
	make lint-typescript

# =============================================================================
# BUILDING & DEPLOYMENT
# =============================================================================

build: ## Build all components (API + Frontend)
	@echo "🏗️ Building all components..."
	make build-api
	make build-frontend
	@echo "✅ Build complete!"

build-api: ## Build API for production
	@echo "🐍 Building API..."
	docker build -f Dockerfile.api -t ctxos-api:latest .

build-frontend: ## Build frontend for production
	@echo "⚛️ Building frontend..."
	cd src && npm run build

build-all: ## Build all Docker images
	@echo "🐳 Building all Docker images..."
	docker-compose build

deploy-dev: ## Deploy to development environment
	@echo "🚀 Deploying to development..."
	docker-compose -f docker-compose.dev.yml up -d --build
	@echo "✅ Development deployment complete!"

deploy-prod: ## Deploy to production environment
	@echo "🚀 Deploying to production..."
	docker-compose up -d --build
	@echo "✅ Production deployment complete!"

# =============================================================================
# DOCKER
# =============================================================================

docker-up: ## Start all services with Docker Compose
	@echo "🐳 Starting all services..."
	docker-compose up -d

docker-down: ## Stop all Docker services
	@echo "🐳 Stopping all services..."
	docker-compose down

docker-logs: ## Show Docker logs
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

docker-clean: ## Clean Docker containers and images
	@echo "🧹 Cleaning Docker..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

# =============================================================================
# DOCUMENTATION
# =============================================================================

docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	make docs-python
	make docs-frontend
	@echo "✅ Documentation generated!"

docs-python: ## Generate Python documentation
	@echo "🐍 Generating Python docs..."
	poetry run pdoc core/ api/ engines/ --html --output-dir docs/html

docs-serve: ## Serve documentation locally
	@echo "📚 Serving documentation..."
	cd docs && python -m http.server 8080
	@echo "📖 Documentation available at http://localhost:8080"

docs-view: ## Open documentation in browser
	@echo "📖 Opening documentation..."
	open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null || echo "Visit http://localhost:8080"

# =============================================================================
# MONITORING & DEBUGGING
# =============================================================================

logs: ## Show application logs
	@echo "📋 Showing application logs..."
	docker-compose logs -f ctxos-api ctxos-frontend

logs-api: ## Show API logs only
	@echo "📋 API logs:"
	docker-compose logs -f ctxos-api

logs-frontend: ## Show frontend logs only
	@echo "📋 Frontend logs:"
	docker-compose logs -f ctxos-frontend

status: ## Show status of all services
	@echo "📊 Service Status:"
	@echo "=================="
	docker-compose ps
	@echo ""
	@echo "🌐 Local Services:"
	@echo "  API:        http://localhost:8000"
	@echo "  Frontend:   http://localhost:3000"
	@echo "  Grafana:    http://localhost:3001"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Jaeger:     http://localhost:16686"

health: ## Check health of all services
	@echo "🏥 Checking service health..."
	@curl -s http://localhost:8000/health > /dev/null && echo "✅ API: Healthy" || echo "❌ API: Unhealthy"
	@curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend: Healthy" || echo "❌ Frontend: Unhealthy"
	@curl -s http://localhost:9200/_cluster/health > /dev/null && echo "✅ Elasticsearch: Healthy" || echo "❌ Elasticsearch: Unhealthy"

# =============================================================================
# UTILITIES
# =============================================================================

clean: ## Clean build artifacts and cache
	@echo "🧹 Cleaning project..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf src/dist/ src/node_modules/.cache/ 2>/dev/null || true
	rm -rf .coverage htmlcov/ 2>/dev/null || true
	rm -rf benchmarks/results/ 2>/dev/null || true
	@echo "✅ Clean complete!"

clean-all: ## Deep clean (including Docker and dependencies)
	@echo "🧹 Deep cleaning project..."
	make clean
	make docker-clean
	rm -rf src/node_modules/ 2>/dev/null || true
	poetry cache purge --all 2>/dev/null || true
	@echo "✅ Deep clean complete!"

shell: ## Open shell in API container
	@echo "🐚 Opening shell in API container..."
	docker-compose exec ctxos-api bash

shell-db: ## Open database shell
	@echo "🗄️ Opening database shell..."
	docker-compose exec postgres psql -U ctxos_user -d ctxos

shell-redis: ## Open Redis CLI
	@echo "🔴 Opening Redis CLI..."
	docker-compose exec redis redis-cli

backup: ## Backup database
	@echo "💾 Creating database backup..."
	docker-compose exec postgres pg_dump -U ctxos_user ctxos > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created!"

restore: ## Restore database (usage: make restore FILE=backup.sql)
	@echo "🔄 Restoring database from $(FILE)..."
	docker-compose exec -T postgres psql -U ctxos_user ctxos < $(FILE)
	@echo "✅ Database restored!"

# =============================================================================
# QUICK START COMMANDS
# =============================================================================

quick-start: ## Quick start for new developers
	@echo "🚀 Quick start for CtxOS development..."
	@echo "This will:"
	@echo "  1. Install dependencies"
	@echo "  2. Start services"
	@echo "  3. Run tests"
	@echo "  4. Start development servers"
	@echo ""
	@read -p "Continue? (y/N) " -n 1 -r; echo
	@if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		make setup; \
		make test; \
		make dev; \
	else \
		echo "Cancelled."; \
	fi

demo: ## Run demo of CtxOS features
	@echo "🎬 Running CtxOS demo..."
	poetry run python examples/core_modules_example.py
	poetry run python examples/collect_example.py
	poetry run python examples/graph_example.py
	poetry run python examples/risk_example.py
	@echo "✅ Demo complete!"

# =============================================================================
# PROJECT SPECIFIC
# =============================================================================

collect: ## Run data collection demo
	@echo "🔍 Running data collection demo..."
	poetry run python examples/collect_example.py

analyze: ## Run risk analysis demo
	@echo "📊 Running risk analysis demo..."
	poetry run python examples/risk_example.py

graph: ## Run graph analysis demo
	@echo "🕸️ Running graph analysis demo..."
	poetry run python examples/graph_example.py

benchmark: ## Run performance benchmarks
	@echo "⚡ Running performance benchmarks..."
	poetry run python benchmarks/benchmark_runner.py

# =============================================================================
# GIT HELPERS
# =============================================================================

git-setup: ## Set up git hooks
	@echo "🪝 Setting up git hooks..."
	pip install pre-commit
	pre-commit install
	cp scripts/pre-commit .git/hooks/ 2>/dev/null || echo "Pre-commit hook not found"
	chmod +x .git/hooks/pre-commit 2>/dev/null || true
	@echo "✅ Git hooks configured!"

git-clean: ## Clean git branches (except main)
	@echo "🧹 Cleaning git branches..."
	git branch | grep -v "main" | xargs git branch -D 2>/dev/null || true
	@echo "✅ Git branches cleaned!"

# =============================================================================
# SECURITY
# =============================================================================

security: ## Run all security scans
	@echo "🔒 Running security scans..."
	make security-python
	make security-frontend
	make security-container
	@echo "✅ Security scans complete!"

security-python: ## Run Python security scans
	@echo "🐍 Running Python security scans..."
	poetry run bandit -r core/ api/ engines/ collectors/ normalizers/ agents/ cli/ -f json -o bandit-report.json || true
	poetry run safety check --json --output safety-report.json || true
	poetry run semgrep --config=auto --json --output semgrep-report.json . || true
	@echo "✅ Python security scans complete!"

security-frontend: ## Run frontend security scans
	@echo "⚛️ Running frontend security scans..."
	cd src && npm audit --audit-level=moderate --json > ../npm-audit-report.json || true
	@echo "✅ Frontend security scans complete!"

security-container: ## Run container security scans
	@echo "🐳 Running container security scans..."
	docker build -t ctxos-security-scan . || true
	@if command -v trivy >/dev/null 2>&1; then \
		trivy image --format json --output trivy-report.json ctxos-security-scan || true; \
	else \
		echo "⚠️ Trivy not installed, skipping container scan"; \
	fi
	@echo "✅ Container security scans complete!"

pre-commit: ## Run pre-commit hooks
	@echo "🪝 Running pre-commit hooks..."
	pre-commit run --all-files
	@echo "✅ Pre-commit hooks complete!"

pre-commit-update: ## Update pre-commit hooks
	@echo "🔄 Updating pre-commit hooks..."
	pre-commit autoupdate
	@echo "✅ Pre-commit hooks updated!"

# =============================================================================
# VERSION MANAGEMENT
# =============================================================================

version: ## Show current version
	@echo "📋 CtxOS Version:"
	@grep -E "^version" pyproject.toml || echo "Version not found in pyproject.toml"

version-patch: ## Bump patch version
	@echo "🔢 Bumping patch version..."
	poetry version patch

version-minor: ## Bump minor version
	@echo "🔢 Bumping minor version..."
	poetry version minor

version-major: ## Bump major version
	@echo "🔢 Bumping major version..."
	poetry version major

# =============================================================================
# DEVELOPMENT SHORTCUTS
# =============================================================================

q: ## Quick dev start (alias for dev)
	make dev

t: ## Quick test run (alias for test)
	make test-python

b: ## Quick build (alias for build)
	make build

c: ## Quick clean (alias for clean)
	make clean

l: ## Quick lint (alias for lint)
	make lint-python

f: ## Quick format (alias for format)
	make format-python

# =============================================================================
# INFO & HELP
# =============================================================================

info: ## Show project information
	@echo "📊 CtxOS Project Information"
	@echo "=========================="
	@echo "📁 Project Root: $(PWD)"
	@echo "🐍 Python Version: $(shell python --version)"
	@echo "⚛️ Node.js Version: $(shell node --version)"
	@echo "🐳 Docker Version: $(shell docker --version)"
	@echo "📦 Poetry Version: $(shell poetry --version)"
	@echo ""
	@echo "📋 Environment:"
	@if [ -f .env ]; then echo "✅ .env file exists"; else echo "❌ .env file missing"; fi
	@echo "🔧 Services:"
	@docker-compose ps 2>/dev/null || echo "❌ Services not running"

tree: ## Show project tree structure
	@echo "🌳 CtxOS Project Tree"
	@echo "====================="
	@tree -I 'node_modules|__pycache__|*.pyc|.git' -L 3

# =============================================================================
# SECURITY POLICY
# =============================================================================

security-policy-check: ## Check security policy compliance
	@echo "🔒 Checking security policy compliance..."
	@if [ ! -f "SECURITY.md" ]; then \
		echo "❌ SECURITY.md file not found"; \
		exit 1; \
	else \
		echo "✅ SECURITY.md file found"; \
	fi
	@if [ ! -f "LICENSE" ]; then \
		echo "❌ LICENSE file not found"; \
		exit 1; \
	else \
		echo "✅ LICENSE file found"; \
	fi
	@if [ ! -f ".github/branch-protection.yml" ]; then \
		echo "❌ Branch protection config not found"; \
		exit 1; \
	else \
		echo "✅ Branch protection config found"; \
	fi
	@echo "✅ Security policy compliance check complete!"

# End of Makefile
