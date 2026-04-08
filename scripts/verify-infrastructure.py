#!/usr/bin/env python3
"""
Verification script for AI Research Copilot infrastructure
Checks that all configuration files and dependencies are properly set up
"""

import os
import sys
import json
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} missing: {filepath}")
        return False


def check_docker_compose():
    """Verify docker-compose.yml configuration"""
    print("\n=== Docker Compose Configuration ===")
    
    if not check_file_exists("docker-compose.yml", "Docker Compose file"):
        return False
    
    # Check for required services
    with open("docker-compose.yml", "r") as f:
        content = f.read()
        required_services = ["nginx", "php-backend", "python-ai-service", "mysql", "redis", "qdrant"]
        all_present = True
        
        for service in required_services:
            if service in content:
                print(f"  ✓ Service defined: {service}")
            else:
                print(f"  ✗ Service missing: {service}")
                all_present = False
        
        return all_present


def check_database_schema():
    """Verify database schema file"""
    print("\n=== Database Schema ===")
    
    if not check_file_exists("docker/mysql/init/01-schema.sql", "Database schema"):
        return False
    
    # Check for required tables
    with open("docker/mysql/init/01-schema.sql", "r") as f:
        content = f.read()
        required_tables = [
            "users", "projects", "project_collaborators", "documents", 
            "citations", "chat_sessions", "chat_messages", "latex_documents"
        ]
        all_present = True
        
        for table in required_tables:
            if f"CREATE TABLE IF NOT EXISTS {table}" in content:
                print(f"  ✓ Table defined: {table}")
            else:
                print(f"  ✗ Table missing: {table}")
                all_present = False
        
        return all_present


def check_environment_variables():
    """Verify environment variables"""
    print("\n=== Environment Variables ===")
    
    if not check_file_exists(".env.example", "Environment template"):
        return False
    
    # Check for required variables
    with open(".env.example", "r") as f:
        content = f.read()
        required_vars = [
            "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
            "REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD",
            "QDRANT_HOST", "QDRANT_PORT",
            "GEMINI_API_KEY", "GROQ_API_KEY",
            "JWT_SECRET"
        ]
        all_present = True
        
        for var in required_vars:
            if var in content:
                print(f"  ✓ Variable defined: {var}")
            else:
                print(f"  ✗ Variable missing: {var}")
                all_present = False
        
        return all_present


def check_python_service():
    """Verify Python AI service files"""
    print("\n=== Python AI Service ===")
    
    files = [
        ("ai-services/main.py", "Main application"),
        ("ai-services/config.py", "Configuration"),
        ("ai-services/health.py", "Health checker"),
        ("ai-services/init_qdrant.py", "Qdrant initializer"),
        ("ai-services/requirements.txt", "Python dependencies")
    ]
    
    all_present = True
    for filepath, description in files:
        if not check_file_exists(filepath, description):
            all_present = False
    
    return all_present


def check_health_endpoints():
    """Verify health check endpoints are implemented"""
    print("\n=== Health Check Endpoints ===")
    
    if not os.path.exists("ai-services/main.py"):
        print("✗ main.py not found")
        return False
    
    with open("ai-services/main.py", "r") as f:
        content = f.read()
        
        endpoints = [
            ("/health", "Basic health check"),
            ("/health/detailed", "Detailed health check")
        ]
        
        all_present = True
        for endpoint, description in endpoints:
            if endpoint in content:
                print(f"  ✓ Endpoint implemented: {endpoint} - {description}")
            else:
                print(f"  ✗ Endpoint missing: {endpoint} - {description}")
                all_present = False
        
        return all_present


def check_nginx_configuration():
    """Verify Nginx configuration"""
    print("\n=== Nginx Configuration ===")
    
    files = [
        ("nginx/nginx.conf", "Main Nginx config"),
        ("nginx/conf.d/default.conf", "Default site config")
    ]
    
    all_present = True
    for filepath, description in files:
        if not check_file_exists(filepath, description):
            all_present = False
    
    # Check SSL directory
    if os.path.exists("nginx/ssl"):
        print(f"  ✓ SSL directory exists: nginx/ssl")
    else:
        print(f"  ✗ SSL directory missing: nginx/ssl")
        all_present = False
    
    return all_present


def check_docker_files():
    """Verify Dockerfiles"""
    print("\n=== Docker Files ===")
    
    files = [
        ("docker/php/Dockerfile", "PHP Dockerfile"),
        ("docker/python/Dockerfile", "Python Dockerfile"),
        ("docker/php/php.ini", "PHP configuration"),
        ("docker/mysql/my.cnf", "MySQL configuration")
    ]
    
    all_present = True
    for filepath, description in files:
        if not check_file_exists(filepath, description):
            all_present = False
    
    return all_present


def check_setup_scripts():
    """Verify setup scripts"""
    print("\n=== Setup Scripts ===")
    
    files = [
        ("scripts/setup-infrastructure.sh", "Linux/Mac setup script"),
        ("scripts/setup-infrastructure.ps1", "Windows setup script"),
        ("scripts/generate-ssl-certs.sh", "Linux/Mac SSL script"),
        ("scripts/generate-ssl-certs.ps1", "Windows SSL script")
    ]
    
    all_present = True
    for filepath, description in files:
        if not check_file_exists(filepath, description):
            all_present = False
    
    return all_present


def main():
    """Run all verification checks"""
    print("=========================================")
    print("AI Research Copilot Infrastructure Verification")
    print("=========================================")
    
    checks = [
        ("Docker Compose", check_docker_compose),
        ("Database Schema", check_database_schema),
        ("Environment Variables", check_environment_variables),
        ("Python Service", check_python_service),
        ("Health Endpoints", check_health_endpoints),
        ("Nginx Configuration", check_nginx_configuration),
        ("Docker Files", check_docker_files),
        ("Setup Scripts", check_setup_scripts)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Error checking {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n=========================================")
    print("Verification Summary")
    print("=========================================")
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        color = "\033[92m" if result else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{status}{reset} - {name}")
        if not result:
            all_passed = False
    
    print("\n=========================================")
    if all_passed:
        print("✓ All infrastructure checks passed!")
        print("=========================================")
        print("\nNext steps:")
        print("1. Update .env with your API keys (GEMINI_API_KEY, GROQ_API_KEY)")
        print("2. Run: docker-compose up -d")
        print("3. Verify services: curl http://localhost:8000/health")
        return 0
    else:
        print("✗ Some infrastructure checks failed!")
        print("=========================================")
        print("\nPlease fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
