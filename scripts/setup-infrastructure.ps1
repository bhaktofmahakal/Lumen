# Setup script for AI Research Copilot infrastructure (Windows)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "AI Research Copilot - Infrastructure Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    docker --version | Out-Null
} catch {
    Write-Host "Error: Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
try {
    docker-compose --version | Out-Null
    $composeCmd = "docker-compose"
} catch {
    try {
        docker compose version | Out-Null
        $composeCmd = "docker compose"
    } catch {
        Write-Host "Error: Docker Compose is not available." -ForegroundColor Red
        exit 1
    }
}

# Generate SSL certificates if they don't exist
if (-not (Test-Path "nginx/ssl/cert.pem") -or -not (Test-Path "nginx/ssl/key.pem")) {
    Write-Host "Generating SSL certificates..." -ForegroundColor Yellow
    & .\scripts\generate-ssl-certs.ps1
    Write-Host ""
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  Please update .env with your API keys before starting services" -ForegroundColor Yellow
    Write-Host ""
}

# Start Docker Compose services
Write-Host "Starting Docker Compose services..." -ForegroundColor Green
if ($composeCmd -eq "docker-compose") {
    docker-compose up -d
} else {
    docker compose up -d
}

Write-Host ""
Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host ""
Write-Host "Checking service health..." -ForegroundColor Green

# Check MySQL
Write-Host -NoNewline "MySQL: "
try {
    if ($composeCmd -eq "docker-compose") {
        docker-compose exec -T mysql mysqladmin ping -h localhost -u root -prootpassword 2>&1 | Out-Null
    } else {
        docker compose exec -T mysql mysqladmin ping -h localhost -u root -prootpassword 2>&1 | Out-Null
    }
    Write-Host "✓ Healthy" -ForegroundColor Green
} catch {
    Write-Host "✗ Unhealthy" -ForegroundColor Red
}

# Check Redis
Write-Host -NoNewline "Redis: "
try {
    if ($composeCmd -eq "docker-compose") {
        docker-compose exec -T redis redis-cli -a redispassword ping 2>&1 | Out-Null
    } else {
        docker compose exec -T redis redis-cli -a redispassword ping 2>&1 | Out-Null
    }
    Write-Host "✓ Healthy" -ForegroundColor Green
} catch {
    Write-Host "✗ Unhealthy" -ForegroundColor Red
}

# Check Qdrant
Write-Host -NoNewline "Qdrant: "
try {
    $response = Invoke-WebRequest -Uri "http://localhost:6333/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Healthy" -ForegroundColor Green
    } else {
        Write-Host "✗ Unhealthy" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Unhealthy" -ForegroundColor Red
}

# Check Python AI Service
Write-Host -NoNewline "Python AI Service: "
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Healthy" -ForegroundColor Green
    } else {
        Write-Host "✗ Unhealthy" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Unhealthy" -ForegroundColor Red
}

# Initialize Qdrant collections
Write-Host ""
Write-Host "Initializing Qdrant collections..." -ForegroundColor Green
if ($composeCmd -eq "docker-compose") {
    docker-compose exec -T python-ai-service python init_qdrant.py
} else {
    docker compose exec -T python-ai-service python init_qdrant.py
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Infrastructure setup completed!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services running:" -ForegroundColor Green
Write-Host "  - Nginx: http://localhost (HTTP) / https://localhost (HTTPS)"
Write-Host "  - Python AI Service: http://localhost:8000"
Write-Host "  - MySQL: localhost:3306"
Write-Host "  - Redis: localhost:6379"
Write-Host "  - Qdrant: http://localhost:6333"
Write-Host "  - Ollama: http://localhost:11434 (optional)"
Write-Host ""
Write-Host "Health check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "Detailed health: http://localhost:8000/health/detailed" -ForegroundColor Cyan
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop services: docker-compose down" -ForegroundColor Yellow
Write-Host "To view logs: docker-compose logs -f" -ForegroundColor Yellow
