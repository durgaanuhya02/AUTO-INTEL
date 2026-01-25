#!/usr/bin/env python3
"""
Setup script for Agentic AI Business Decision System
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def check_requirements():
    """Check if required tools are installed"""
    requirements = {
        'python': 'python --version',
        'node': 'node --version',
        'npm': 'npm --version',
        'docker': 'docker --version',
        'docker-compose': 'docker-compose --version'
    }
    
    missing = []
    for tool, command in requirements.items():
        if not run_command(command):
            missing.append(tool)
    
    if missing:
        print("Missing required tools:")
        for tool in missing:
            print(f"  - {tool}")
        print("\nPlease install the missing tools and try again.")
        return False
    
    return True

def setup_environment():
    """Set up environment files"""
    if not os.path.exists('.env'):
        shutil.copy('.env.example', '.env')
        print("Created .env file from .env.example")
        print("Please edit .env file with your configuration")
    
    # Create backend .env
    backend_env = Path('backend/.env')
    if not backend_env.exists():
        shutil.copy('.env.example', backend_env)
        print("Created backend/.env file")

def setup_backend():
    """Set up Python backend"""
    print("Setting up Python backend...")
    
    # Create virtual environment
    if not os.path.exists('backend/venv'):
        run_command('python -m venv venv', cwd='backend')
        print("Created Python virtual environment")
    
    # Install dependencies
    if os.name == 'nt':  # Windows
        pip_cmd = 'venv\\Scripts\\pip'
    else:  # Unix/Linux/macOS
        pip_cmd = 'venv/bin/pip'
    
    run_command(f'{pip_cmd} install -r requirements.txt', cwd='backend')
    print("Installed Python dependencies")

def setup_frontend():
    """Set up Node.js frontend"""
    print("Setting up Node.js frontend...")
    
    # Install dependencies
    run_command('npm install', cwd='frontend')
    print("Installed Node.js dependencies")

def setup_database():
    """Set up database using Docker"""
    print("Setting up database with Docker...")
    
    # Start database services
    run_command('docker-compose up -d postgres redis', cwd='docker')
    print("Started PostgreSQL and Redis containers")
    
    # Wait for database to be ready
    import time
    print("Waiting for database to be ready...")
    time.sleep(10)
    
    # Run database schema
    run_command(
        'docker exec -i agentic_ai_postgres psql -U user -d agentic_ai < ../database/schema.sql',
        cwd='docker'
    )
    print("Database schema created")

def setup_ml_models():
    """Set up and train ML models"""
    print("Setting up ML models...")
    
    # Run model training script
    try:
        run_command('python train_models.py', cwd='.')
        print("ML models trained successfully")
    except Exception as e:
        print(f"Warning: ML model training failed: {e}")
        print("System will use fallback methods")

def create_startup_scripts():
    """Create startup scripts for different platforms"""
    
    # Windows batch file
    windows_script = """@echo off
echo Starting Agentic AI Business Decision System...

echo Starting database services...
cd docker
docker-compose up -d postgres redis
cd ..

echo Starting backend...
cd backend
start cmd /k "venv\\Scripts\\python main.py"
cd ..

echo Starting frontend...
cd frontend
start cmd /k "npm run dev"
cd ..

echo System is starting up...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause
"""
    
    with open('start.bat', 'w') as f:
        f.write(windows_script)
    
    # Unix shell script
    unix_script = """#!/bin/bash
echo "Starting Agentic AI Business Decision System..."

echo "Starting database services..."
cd docker
docker-compose up -d postgres redis
cd ..

echo "Starting backend..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

echo "Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "System is running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    cd docker
    docker-compose down
    cd ..
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for user interrupt
wait
"""
    
    with open('start.sh', 'w') as f:
        f.write(unix_script)
    
    # Make shell script executable
    if os.name != 'nt':
        os.chmod('start.sh', 0o755)
    
    print("Created startup scripts: start.bat (Windows) and start.sh (Unix)")

def main():
    """Main setup function"""
    print("=== Agentic AI Business Decision System Setup ===")
    print()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup steps
    setup_environment()
    setup_backend()
    setup_frontend()
    setup_database()
    setup_ml_models()
    create_startup_scripts()
    
    print()
    print("=== Setup Complete! ===")
    print()
    print("To start the system:")
    print("  Windows: run start.bat")
    print("  Unix/Linux/macOS: ./start.sh")
    print()
    print("Or manually:")
    print("  1. cd docker && docker-compose up -d")
    print("  2. cd backend && python main.py")
    print("  3. cd frontend && npm run dev")
    print()
    print("Access the application:")
    print("  Frontend: http://localhost:3000")
    print("  Backend API: http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print()
    print("Don't forget to:")
    print("  1. Edit .env file with your OpenAI API key")
    print("  2. Configure any other settings as needed")

if __name__ == '__main__':
    main()