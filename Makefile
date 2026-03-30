.PHONY: help install start stop restart logs setup clean

help:
	@echo "Local AI Lab - Available Commands"
	@echo "=================================="
	@echo "make install     - Install all dependencies"
	@echo "make setup       - Initial setup (models, config)"
	@echo "make start       - Start all services"
	@echo "make stop        - Stop all services"
	@echo "make restart     - Restart all services"
	@echo "make logs        - View service logs"
	@echo "make clean       - Clean up containers and volumes"
	@echo ""
	@echo "Development:"
	@echo "make dev-cli     - Run CLI in development mode"
	@echo "make dev-web     - Run Web UI in development mode"
	@echo ""
	@echo "Testing:"
	@echo "make test        - Run all tests"
	@echo "make test-unit   - Run unit tests only"
	@echo "make test-integration - Run integration tests"
	@echo "make test-e2e    - Run end-to-end tests"
	@echo "make test-coverage - Run tests with coverage report"

install:
	@echo "Installing CLI..."
	cd cli && pip install -e .
	@echo "Installing Web UI dependencies..."
	cd web-ui && npm install
	@echo "Installing Go agent..."
	cd agents/ops-agent && go mod tidy
	@echo "Installing Rust agent..."
	cd agents/security-agent && cargo fetch
	@echo "Installing Node agent..."
	cd agents/architect-agent && npm install

setup:
	@echo "Setting up Local AI Lab..."
	lab setup
	lab model pull qwen2.5-coder:7b
	@echo "Setup complete!"

start:
	docker-compose -f docker/docker-compose.yml up -d
	@echo "Services started!"
	@echo "Web UI: http://localhost:3000"
	@echo "API: http://localhost:8000"

stop:
	docker-compose -f docker/docker-compose.yml down

restart: stop start

logs:
	docker-compose -f docker/docker-compose.yml logs -f

clean:
	docker-compose -f docker/docker-compose.yml down -v
	docker system prune -f

dev-cli:
	cd cli && python -m lab

dev-web:
	cd web-ui && npm run dev

test:
	@echo "Running all tests..."
	cd cli && python tests/run_tests.py

test-unit:
	@echo "Running unit tests..."
	cd cli && pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	cd cli && pytest tests/integration/ -v

test-e2e:
	@echo "Running E2E tests..."
	cd cli && pytest tests/e2e/ -v

test-coverage:
	@echo "Running tests with coverage..."
	cd cli && pytest --cov=lab --cov-report=term-missing

test-web:
	cd web-ui && npm test
