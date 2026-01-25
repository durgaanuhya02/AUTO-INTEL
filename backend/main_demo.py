"""
Demo version of the main application that runs without Redis/PostgreSQL
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime
from typing import Dict, Any
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Agentic AI Business Decision System (Demo)",
    description="Demo version - runs without Redis/PostgreSQL",
    version="1.0.0-demo"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load mock data
def load_mock_data():
    """Load mock data from file"""
    try:
        with open("../mock_data/dashboard_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default mock data if file doesn't exist
        return {
            "current_metrics": {
                "revenue": 125000,
                "orders": 450,
                "customer_satisfaction": 4.2,
                "delivery_delay": 2.3,
                "churn_risk": 0.12
            },
            "alerts": [
                {
                    "id": 1,
                    "title": "Demo Alert",
                    "description": "This is a demo alert",
                    "severity": "medium",
                    "metric_type": "revenue",
                    "current_value": 125000,
                    "agent_type": "observer",
                    "created_at": datetime.utcnow().isoformat()
                }
            ],
            "recent_decisions": [
                {
                    "id": 1,
                    "title": "Demo Decision",
                    "description": "This is a demo decision",
                    "scenarios": [],
                    "recommended_scenario": "Demo Scenario",
                    "confidence_score": 0.85,
                    "financial_impact": 10000,
                    "requires_approval": True,
                    "reasoning": "Demo reasoning",
                    "status": "pending",
                    "created_at": datetime.utcnow().isoformat()
                }
            ],
            "agent_statuses": [
                {
                    "agent_type": "observer",
                    "status": "active",
                    "last_activity": datetime.utcnow().isoformat(),
                    "current_task": "Demo task",
                    "metrics": {"processed_count": 100}
                }
            ],
            "trends": {
                "revenue": [120000, 122000, 125000, 123000, 125000] * 4,
                "orders": [400, 420, 450, 440, 450] * 4,
                "customer_satisfaction": [4.0, 4.1, 4.2, 4.1, 4.2] * 4,
                "delivery_delay": [2.5, 2.4, 2.3, 2.4, 2.3] * 4,
                "churn_risk": [0.15, 0.13, 0.12, 0.13, 0.12] * 4
            }
        }

@app.get("/")
async def root():
    return {
        "message": "Agentic AI Business Decision System (Demo Mode)",
        "version": "1.0.0-demo",
        "status": "running",
        "note": "This is a demo version running without Redis/PostgreSQL"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "mode": "demo",
        "redis": "not_required",
        "agents": "simulated",
        "note": "Demo mode - install Docker for full functionality"
    }

@app.get("/api/v1/dashboard")
async def get_dashboard_data():
    """Get dashboard data (demo version)"""
    try:
        mock_data = load_mock_data()
        return mock_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading demo data: {str(e)}")

@app.get("/api/v1/metrics")
async def get_metrics():
    """Get metrics (demo version)"""
    try:
        mock_data = load_mock_data()
        return {
            "current_metrics": mock_data["current_metrics"],
            "historical_data": mock_data["trends"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading demo metrics: {str(e)}")

@app.get("/api/v1/alerts")
async def get_alerts():
    """Get alerts (demo version)"""
    try:
        mock_data = load_mock_data()
        return {
            "alerts": mock_data["alerts"],
            "count": len(mock_data["alerts"]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading demo alerts: {str(e)}")

@app.get("/api/v1/decisions")
async def get_decisions():
    """Get decisions (demo version)"""
    try:
        mock_data = load_mock_data()
        return {
            "decisions": mock_data["recent_decisions"],
            "count": len(mock_data["recent_decisions"]),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading demo decisions: {str(e)}")

@app.get("/api/v1/agents/status")
async def get_agent_status():
    """Get agent status (demo version)"""
    try:
        mock_data = load_mock_data()
        return {
            "orchestrator_running": True,
            "agents": {
                agent["agent_type"]: {
                    "status": agent["status"],
                    "last_activity": agent["last_activity"],
                    "current_task": agent.get("current_task", ""),
                    "metrics": agent.get("metrics", {})
                }
                for agent in mock_data["agent_statuses"]
            },
            "redis_connected": False,
            "openai_available": False,
            "mode": "demo"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading demo agent status: {str(e)}")

@app.post("/api/v1/agents/trigger")
async def trigger_analysis(metric_type: str, current_value: float, description: str = None):
    """Trigger analysis (demo version)"""
    return {
        "status": "triggered",
        "message": f"Demo analysis triggered for {metric_type}",
        "metric_type": metric_type,
        "current_value": current_value,
        "note": "This is a demo - no actual analysis performed",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/approve-decision")
async def approve_decision(decision_id: str, approved: bool, approver: str, comments: str = None):
    """Approve decision (demo version)"""
    return {
        "status": "processed",
        "decision_id": decision_id,
        "approved": approved,
        "approver": approver,
        "comments": comments,
        "note": "This is a demo - no actual approval processed",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/system/health")
async def system_health():
    """System health (demo version)"""
    return {
        "status": "healthy",
        "mode": "demo",
        "redis_healthy": False,
        "agents_active": "5/5 (simulated)",
        "orchestrator_running": True,
        "openai_available": False,
        "note": "Demo mode - install Docker and Redis for full functionality",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    print("Starting Agentic AI Business Decision System (Demo Mode)")
    print("Note: This is a demo version without Redis/PostgreSQL")
    print("For full functionality, please install Docker and use the complete setup")
    print()
    
    uvicorn.run(
        "main_demo:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )