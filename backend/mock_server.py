#!/usr/bin/env python3
"""
Mock backend server for testing frontend without full infrastructure
"""
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any
import uvicorn
import psutil

app = FastAPI(
    title="Mock Agentic AI Backend",
    description="Mock backend for testing frontend functionality",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
mock_dashboard_data = {
    "current_metrics": {
        "revenue": 125000.50,
        "orders": 1250,
        "customer_satisfaction": 4.2,
        "churn_risk": 12.5
    },
    "alerts": [
        {
            "id": 1,
            "title": "High Revenue Alert",
            "message": "Revenue has increased by 15% in the last hour",
            "severity": "info",
            "timestamp": datetime.now().isoformat(),
            "status": "active"
        },
        {
            "id": 2,
            "title": "Customer Satisfaction Drop",
            "message": "Customer satisfaction has dropped below 4.0",
            "severity": "warning",
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "status": "active"
        }
    ],
    "recent_decisions": [
        {
            "id": 1,
            "title": "Inventory Optimization",
            "description": "Recommended: Increase inventory for high-demand products",
            "scenarios": ["increase_inventory", "maintain_current", "reduce_inventory"],
            "recommended_scenario": "increase_inventory",
            "confidence_score": 0.85,
            "financial_impact": 25000.0,
            "requires_approval": True,
            "reasoning": "Based on recent sales trends and demand forecasting",
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "approved_at": None,
            "executed_at": None
        }
    ],
    "agent_statuses": [
        {
            "agent_type": "observer",
            "status": "active",
            "last_activity": datetime.now().isoformat(),
            "current_task": "Monitoring revenue metrics",
            "health_score": 0.95
        },
        {
            "agent_type": "analyst",
            "status": "active",
            "last_activity": datetime.now().isoformat(),
            "current_task": "Analyzing customer behavior patterns",
            "health_score": 0.88
        },
        {
            "agent_type": "decision",
            "status": "active",
            "last_activity": datetime.now().isoformat(),
            "current_task": "Evaluating inventory decisions",
            "health_score": 0.92
        }
    ],
    "trends": {
        "revenue": [120000, 121500, 123000, 124200, 125000],
        "orders": [1200, 1220, 1235, 1245, 1250],
        "customer_satisfaction": [4.1, 4.15, 4.18, 4.2, 4.2],
        "churn_risk": [15.2, 14.8, 13.5, 12.8, 12.5]
    }
}

@app.get("/")
async def root():
    return {"message": "Mock Agentic AI Backend", "status": "running"}

@app.get("/api/v1/dashboard")
async def get_dashboard_data():
    """Get mock dashboard data"""
    return mock_dashboard_data

@app.get("/api/v1/metrics/real-time")
async def get_real_time_metrics():
    """Get mock real-time metrics"""
    return {
        "metrics": {
            "revenue": {"value": 125000.50, "timestamp": datetime.now().isoformat()},
            "orders": {"value": 1250, "timestamp": datetime.now().isoformat()},
            "customer_satisfaction": {"value": 4.2, "timestamp": datetime.now().isoformat()},
            "churn_risk": {"value": 12.5, "timestamp": datetime.now().isoformat()}
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/enterprise/integrations/status")
async def get_integration_status():
    """Get mock integration status"""
    return {
        "integrations": {
            "salesforce": {
                "status": "connected",
                "enabled": True,
                "last_check": datetime.now().isoformat()
            },
            "sap": {
                "status": "connected",
                "enabled": True,
                "last_check": datetime.now().isoformat()
            },
            "dynamics365": {
                "status": "disconnected",
                "enabled": False,
                "last_check": (datetime.now() - timedelta(hours=2)).isoformat()
            },
            "oracle_erp": {
                "status": "connected",
                "enabled": True,
                "last_check": datetime.now().isoformat()
            },
            "hubspot": {
                "status": "connected",
                "enabled": True,
                "last_check": datetime.now().isoformat()
            }
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/analytics/status")
async def get_analytics_status():
    """Get mock analytics status"""
    return {
        "running": True,
        "trained_models": 5,
        "total_models": 8,
        "last_training": datetime.now().isoformat(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/metrics/system")
async def get_system_metrics():
    """Get real system performance metrics"""
    try:
        # Get actual system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Calculate uptime
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        # Mock some metrics
        network_latency = 45.2
        response_time = 150
        active_connections = 12
        requests_per_minute = 45
        error_rate = 0.5
        
        return {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "network_latency": network_latency,
            "response_time": response_time,
            "uptime": uptime,
            "active_connections": active_connections,
            "requests_per_minute": requests_per_minute,
            "error_rate": error_rate,
            "timestamp": datetime.now().isoformat(),
            "memory_total": memory.total,
            "memory_available": memory.available,
            "disk_total": disk.total,
            "disk_free": disk.free
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching system metrics: {str(e)}")

@app.post("/api/v1/ml/upload-csv")
async def upload_csv_file(file: UploadFile = File(...)):
    """Mock CSV upload endpoint"""
    return {
        "status": "success",
        "file_path": f"uploads/{file.filename}",
        "analysis": {
            "file_info": {
                "filename": file.filename,
                "rows": 1000,
                "columns": 8,
                "size_mb": 2.5
            },
            "column_info": {
                "revenue": {"dtype": "float64", "null_count": 0, "unique_values": 950},
                "customer_id": {"dtype": "int64", "null_count": 0, "unique_values": 800},
                "product_category": {"dtype": "object", "null_count": 5, "unique_values": 12}
            },
            "data_quality": {
                "total_missing_values": 15,
                "missing_percentage": 1.8,
                "duplicate_rows": 3
            }
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/ml/train-model")
async def train_ml_model(request: Dict[str, Any]):
    """Mock model training endpoint"""
    return {
        "status": "success",
        "model_info": {
            "model_name": f"revenue_model_{int(time.time())}",
            "model_type": "regression",
            "target_column": request.get("target_column", "revenue"),
            "training_accuracy": 0.92,
            "validation_accuracy": 0.88,
            "feature_importance": {
                "customer_segment": 0.35,
                "product_category": 0.28,
                "seasonality": 0.22,
                "marketing_spend": 0.15
            }
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/approve-decision")
async def approve_decision(request: Dict[str, Any]):
    """Mock decision approval endpoint"""
    return {
        "status": "processed",
        "decision_id": request.get("decision_id"),
        "approved": request.get("approved", False),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-mock"
    }

if __name__ == "__main__":
    print("Starting Mock Backend Server...")
    print("Frontend can access this at: http://localhost:8001")
    uvicorn.run(
        "mock_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )