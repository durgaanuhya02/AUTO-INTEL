#!/usr/bin/env python3
"""
Setup script for Agentic AI Business Decision System (No Docker)
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

def setup_environment():
    """Set up environment files"""
    if not os.path.exists('.env'):
        shutil.copy('.env.example', '.env')
        print("Created .env file from .env.example")
        print("Please edit .env file with your OpenAI API key")
    
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
    pip_cmd = 'venv\\Scripts\\pip'
    
    print("Installing Python dependencies...")
    result = run_command(f'{pip_cmd} install -r requirements.txt', cwd='backend')
    if result is not None:
        print("Installed Python dependencies")
    else:
        print("Failed to install Python dependencies")

def setup_frontend():
    """Set up Node.js frontend"""
    print("Setting up Node.js frontend...")
    
    # Install dependencies
    print("Installing Node.js dependencies...")
    result = run_command('npm install', cwd='frontend')
    if result is not None:
        print("Installed Node.js dependencies")
    else:
        print("Failed to install Node.js dependencies")

def create_startup_scripts():
    """Create startup scripts for different platforms"""
    
    # Windows batch file for no-docker setup
    windows_script = """@echo off
echo Starting Agentic AI Business Decision System (No Docker Mode)...
echo.
echo NOTE: This runs without Redis/PostgreSQL. Some features may be limited.
echo For full functionality, please install Docker and use the full setup.
echo.

echo Starting backend...
cd backend
start cmd /k "venv\\Scripts\\python -c \\"print('Starting backend server...'); import sys; sys.path.append('.'); from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)\\""
cd ..

echo Starting frontend...
cd frontend
start cmd /k "npm run dev"
cd ..

echo.
echo System is starting up...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause
"""
    
    with open('start_no_docker.bat', 'w') as f:
        f.write(windows_script)
    
    print("Created startup script: start_no_docker.bat")

def create_mock_data():
    """Create mock data for demo without database"""
    mock_data_script = '''
import json
import os
from datetime import datetime, timedelta
import random

# Create mock data directory
os.makedirs("mock_data", exist_ok=True)

# Mock metrics
current_metrics = {
    "revenue": 125000,
    "orders": 450,
    "customer_satisfaction": 4.2,
    "delivery_delay": 2.3,
    "churn_risk": 0.12
}

# Mock trends (last 20 data points)
trends = {}
for metric, current_value in current_metrics.items():
    trend_data = []
    base_value = current_value
    for i in range(20):
        # Add some realistic variation
        variation = random.uniform(-0.1, 0.1)
        value = base_value * (1 + variation)
        trend_data.append(round(value, 2))
    trends[metric] = trend_data

# Mock alerts
alerts = [
    {
        "id": 1,
        "title": "Revenue Drop Detected",
        "description": "Revenue has decreased by 8% compared to last week",
        "severity": "medium",
        "metric_type": "revenue",
        "current_value": 125000,
        "agent_type": "observer",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": 2,
        "title": "High Churn Risk",
        "description": "Customer churn risk is above normal threshold",
        "severity": "high",
        "metric_type": "churn_risk",
        "current_value": 0.12,
        "agent_type": "analyst",
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
    }
]

# Mock decisions
decisions = [
    {
        "id": 1,
        "title": "Promotional Campaign Recommendation",
        "description": "Launch targeted promotional campaign to boost revenue",
        "scenarios": [
            {
                "name": "10% Discount Campaign",
                "description": "Offer 10% discount to high-value customers",
                "confidence_score": 0.85,
                "risk_score": 0.15,
                "parameters": {"discount": 0.1, "target": "high_value"},
                "predicted_outcome": {"revenue_increase": 15000, "cost": 5000}
            }
        ],
        "recommended_scenario": "10% Discount Campaign",
        "confidence_score": 0.85,
        "financial_impact": 10000,
        "requires_approval": True,
        "reasoning": "Based on historical data, targeted promotions have shown 85% success rate",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
]

# Mock agent statuses
agent_statuses = [
    {
        "agent_type": "observer",
        "status": "active",
        "last_activity": datetime.utcnow().isoformat(),
        "current_task": "Monitoring revenue metrics",
        "metrics": {"processed_count": 1250}
    },
    {
        "agent_type": "analyst",
        "status": "active", 
        "last_activity": datetime.utcnow().isoformat(),
        "current_task": "Analyzing churn patterns",
        "metrics": {"processed_count": 890}
    },
    {
        "agent_type": "simulation",
        "status": "idle",
        "last_activity": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
        "metrics": {"processed_count": 45}
    },
    {
        "agent_type": "decision",
        "status": "active",
        "last_activity": datetime.utcnow().isoformat(),
        "current_task": "Evaluating promotion scenarios",
        "metrics": {"processed_count": 23}
    },
    {
        "agent_type": "governance",
        "status": "active",
        "last_activity": datetime.utcnow().isoformat(),
        "current_task": "Reviewing pending approvals",
        "metrics": {"processed_count": 12}
    }
]

# Save mock data
with open("mock_data/dashboard_data.json", "w") as f:
    json.dump({
        "current_metrics": current_metrics,
        "alerts": alerts,
        "recent_decisions": decisions,
        "agent_statuses": agent_statuses,
        "trends": trends
    }, f, indent=2)

print("Mock data created successfully!")
'''
    
    with open('create_mock_data.py', 'w') as f:
        f.write(mock_data_script)
    
    # Run the mock data creation
    run_command('python create_mock_data.py')
    print("Created mock data for demo")

def main():
    """Main setup function"""
    print("=== Agentic AI Business Decision System Setup (No Docker) ===")
    print()
    print("This setup runs the system without Docker for quick testing.")
    print("For full production features, please install Docker and use the full setup.")
    print()
    
    # Setup steps
    setup_environment()
    setup_backend()
    setup_frontend()
    create_mock_data()
    create_startup_scripts()
    
    print()
    print("=== Setup Complete! ===")
    print()
    print("To start the system:")
    print("  Windows: run start_no_docker.bat")
    print()
    print("Or manually:")
    print("  1. cd backend && venv\\Scripts\\python main.py")
    print("  2. cd frontend && npm run dev")
    print()
    print("Access the application:")
    print("  Frontend: http://localhost:3000")
    print("  Backend API: http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print()
    print("Note: This demo mode uses mock data.")
    print("For full functionality with real AI agents, install Docker and Redis.")

if __name__ == '__main__':
    main()