#!/bin/bash
# Setup script for AI Research Copilot infrastructure

set -e

echo "=========================================="
echo "AI Research Copilot - Infrastructure Setup"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Generate SSL certificates if they don't exist
if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
    echo "Generating SSL certificates..."
    bash scripts/generate-ssl-certs.sh
    echo ""
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API keys before starting services"
    echo ""
fi

# Start Docker Compose services
echo "Starting Docker Compose services..."
docker-compose up -d

echo ""
echo "Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

# Check MySQL
echo -n "MySQL: "
if docker-compose exec -T mysql mysqladmin ping -h localhost -u root -prootpassword &> /dev/null; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# Check Redis
echo -n "Redis: "
if docker-compose exec -T redis redis-cli -a redispassword ping &> /dev/null; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# Check Qdrant
echo -n "Qdrant: "
if curl -s http://localhost:6333/health &> /dev/null; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# Check Python AI Service
echo -n "Python AI Service: "
if curl -s http://localhost:8000/health &> /dev/null; then
    echo "✓ Healthy"
else
    echo "✗ Unhealthy"
fi

# Initialize Qdrant collections
echo ""
echo "Initializing Qdrant collections..."
docker-compose exec -T python-ai-service python init_qdrant.py

echo ""
echo "=========================================="
echo "Infrastructure setup completed!"
echo "=========================================="
echo ""
echo "Services running:"
echo "  - Nginx: http://localhost (HTTP) / https://localhost (HTTPS)"
echo "  - Python AI Service: http://localhost:8000"
echo "  - MySQL: localhost:3306"
echo "  - Redis: localhost:6379"
echo "  - Qdrant: http://localhost:6333"
echo "  - Ollama: http://localhost:11434 (optional)"
echo ""
echo "Health check: http://localhost:8000/health"
echo "Detailed health: http://localhost:8000/health/detailed"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "To stop services: docker-compose down"
echo "To view logs: docker-compose logs -f"
