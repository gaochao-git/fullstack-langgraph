.PHONY: help install install-frontend install-backend dev-frontend dev-backend dev-mcp dev prod test clean build trans

help:
	@echo "Available commands:"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make install         - Install all dependencies (frontend + backend)"
	@echo "  make dev             - Start local development servers (frontend + backend)"
	@echo "  make dev-frontend    - Start frontend development server only"
	@echo "  make dev-backend     - Start backend development server only"
	@echo ""
	@echo "🏭 Production:"
	@echo "  make prod            - Start production server"
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
	@cd backend && uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

# Development MCP servers
dev-mcp:
	@echo "🔧 Starting MCP servers..."
	@cd scripts && ./start_mcp.sh

# Run all development servers concurrently
dev:
	@echo "🚀 Starting frontend, backend and MCP servers..."
	@make dev-mcp && make dev-frontend & make dev-backend

# Production server
prod:
	@echo "🏭 Starting production server..."
	@cd backend && uvicorn src.api.app:app --host 0.0.0.0 --port 8000

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
	scp "$$LATEST_PACKAGE" manage_omind.sh root@82.156.146.51:/tmp/ && \
	echo "✅ Successfully transferred:" && \
	echo "   - Package: /tmp/$$(basename $$LATEST_PACKAGE)" && \
	echo "   - Script:  /tmp/manage_omind.sh"


# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@cd frontend && rm -rf dist node_modules/.cache
	@cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@cd backend && find . -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf dist