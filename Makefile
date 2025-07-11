.PHONY: help install install-frontend install-backend dev-frontend dev-backend dev prod test clean

help:
	@echo "Available commands:"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make install         - Install all dependencies (frontend + backend)"
	@echo "  make dev             - Start both frontend and backend development servers"
	@echo "  make dev-frontend    - Start frontend development server only"
	@echo "  make dev-backend     - Start backend development server only"
	@echo ""
	@echo "🏭 Production:"
	@echo "  make prod            - Start production server"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test            - Run tests"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean           - Clean build artifacts"

# Install dependencies
install: install-backend install-frontend

install-backend:
	@echo "📦 Installing backend dependencies..."
	@cd backend && pip install .

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	@cd frontend && npm install

# Development servers
dev-frontend:
	@echo "🖥️  Starting frontend development server..."
	@cd frontend && npm run dev

dev-backend:
	@echo "🔧 Starting backend development server with hot reload..."
	@cd backend && uvicorn fastapi_main:app --reload --host 127.0.0.1 --port 8000

# Run frontend and backend concurrently
dev:
	@echo "🚀 Starting both frontend and backend development servers..."
	@make dev-frontend & make dev-backend

# Production server
prod:
	@echo "🏭 Starting production server..."
	@cd backend && uvicorn fastapi_main:app --host 0.0.0.0 --port 8000

# Test
test:
	@echo "🧪 Running tests..."
	@cd backend && python -m pytest || echo "No tests found"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@cd frontend && rm -rf dist node_modules/.cache
	@cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@cd backend && find . -name "*.pyc" -delete 2>/dev/null || true 