.PHONY: help install install-frontend install-backend dev-frontend dev-backend dev-mcp dev prod test clean build trans start stop restart status

help:
	@echo "Available commands:"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make install         - Install all dependencies (frontend + backend)"
	@echo "  make dev             - Start all services + frontend dev server"
	@echo "  make dev-frontend    - Start frontend development server only"
	@echo "  make dev-backend     - Start backend development server only"
	@echo "  make dev-mcp         - Start MCP servers only"
	@echo ""
	@echo "🎮 Service Management:"
	@echo "  make start           - Start all services (backend + MCP)"
	@echo "  make stop            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo "  make status          - Check service status"
	@echo ""
	@echo "🏭 Production:"
	@echo "  make build           - Build production deployment package"
	@echo "  make trans           - Transfer package to remote server"
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
	@cd backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Development MCP servers
dev-mcp:
	@echo "🔧 Starting MCP servers..."
	@cd mcp_servers && ./manage.sh start

# Run all development servers concurrently
dev:
	@echo "🚀 Starting all development servers..."
	@OMIND_DEV_MODE=true ./scripts/manage_omind.sh start
	@echo "🖥️  Starting frontend development server..."
	@cd frontend && npm run dev

# Production server
prod:
	@echo "🏭 Starting production server..."
	@cd backend && uvicorn src.main:app --host 0.0.0.0 --port 8000

# Test
test:
	@echo "🧪 Running tests..."
	@cd backend && python -m pytest || echo "No tests found"

# Build production deployment package
build:
	@echo "📦 Building production deployment package..."
	@./build_omind.sh

# Keep old alias for compatibility
build-prod: build

# Transfer package to remote server
trans:
	@echo "📡 Transferring package to remote server..."
	@LATEST_PACKAGE=$$(ls -t dist/omind-*.tar.gz 2>/dev/null | head -n1); \
	if [ -z "$$LATEST_PACKAGE" ]; then \
		echo "❌ No package found. Please run 'make build' first."; \
		exit 1; \
	fi; \
	echo "📦 Transferring $$LATEST_PACKAGE..."; \
	echo "📡 Copying to root@82.156.146.51:/tmp/"; \
	scp "$$LATEST_PACKAGE" root@82.156.146.51:/tmp/ && \
	echo "✅ Successfully transferred:" && \
	echo "   - Package: /tmp/$$(basename $$LATEST_PACKAGE)" && \
	echo "   - 解压后使用: ./scripts/manage_omind.sh init"


# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@cd frontend && rm -rf dist node_modules/.cache
	@cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@cd backend && find . -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf dist

# Service management commands
start:
	@echo "🚀 Starting all services..."
	@./scripts/manage_omind.sh start

stop:
	@echo "🛑 Stopping all services..."
	@./scripts/manage_omind.sh stop

restart:
	@echo "🔄 Restarting all services..."
	@./scripts/manage_omind.sh restart

status:
	@echo "📊 Checking service status..."
	@./scripts/manage_omind.sh status