
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
