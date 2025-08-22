.PHONY: help install run test clean docker-build docker-up docker-down docker-logs

# Default target
help:
	@echo "Chat API - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     Install Python dependencies"
	@echo "  run         Run the development server"
	@echo "  test        Test the API endpoints"
	@echo "  clean       Clean up generated files"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build    Build Docker images"
	@echo "  docker-up       Start all services"
	@echo "  docker-down     Stop all services"
	@echo "  docker-logs     View service logs"
	@echo ""
	@echo "Database:"
	@echo "  db-init     Initialize database"
	@echo "  db-reset    Reset database (WARNING: deletes all data)"

# Install dependencies
install:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt

# Run development server
run:
	@echo "🚀 Starting development server..."
	python run.py

# Test API endpoints
test:
	@echo "🧪 Testing API endpoints..."
	python test_api.py

# Clean up generated files
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.db" -delete
	@echo "✅ Cleanup complete"

# Docker commands
docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build

docker-up:
	@echo "🚀 Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker-compose down

docker-logs:
	@echo "📋 Viewing Docker logs..."
	docker-compose logs -f

# Database commands
db-init:
	@echo "🗄️  Initializing database..."
	python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
	@echo "✅ Database initialized"

db-reset:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "🗑️  Resetting database..."; \
		find . -name "*.db" -delete; \
		python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"; \
		echo "✅ Database reset complete"; \
	else \
		echo "❌ Database reset cancelled"; \
	fi

# Quick start (install + run)
quickstart: install run

# Full setup (install + docker)
setup: install docker-build docker-up
	@echo ""
	@echo "🎉 Setup complete!"
	@echo "📚 API Documentation: http://localhost:8000/docs"
	@echo "🌐 Frontend: Open frontend/index.html in your browser"
	@echo ""
	@echo "Use 'make docker-logs' to view service logs"
	@echo "Use 'make docker-down' to stop services"