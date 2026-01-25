from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MetricType(str, Enum):
    REVENUE = "revenue"
    ORDERS = "orders"
    CHURN_RISK = "churn_risk"
    DELIVERY_DELAY = "delivery_delay"
    CUSTOMER_SATISFACTION = "customer_satisfaction"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DecisionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"

class AgentType(str, Enum):
    OBSERVER = "observer"
    ANALYST = "analyst"
    SIMULATION = "simulation"
    DECISION = "decision"
    GOVERNANCE = "governance"

# Metric Models
class MetricCreate(BaseModel):
    metric_type: MetricType
    value: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class MetricResponse(BaseModel):
    id: int
    metric_type: MetricType
    value: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Alert Models
class AlertCreate(BaseModel):
    title: str
    description: str
    severity: AlertSeverity
    metric_type: MetricType
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    agent_type: AgentType

class AlertResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: AlertSeverity
    metric_type: MetricType
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    agent_type: AgentType
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Decision Models
class DecisionScenario(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    predicted_outcome: Dict[str, float]
    confidence_score: float
    risk_score: float

class DecisionCreate(BaseModel):
    title: str
    description: str
    scenarios: List[DecisionScenario]
    recommended_scenario: str
    confidence_score: float
    financial_impact: float
    requires_approval: bool
    reasoning: str

class DecisionResponse(BaseModel):
    id: int
    title: str
    description: str
    scenarios: List[DecisionScenario]
    recommended_scenario: str
    confidence_score: float
    financial_impact: float
    requires_approval: bool
    reasoning: str
    status: DecisionStatus
    created_at: datetime
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Agent Communication Models
class AgentMessage(BaseModel):
    from_agent: AgentType
    to_agent: Optional[AgentType] = None
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentStatus(BaseModel):
    agent_type: AgentType
    status: str
    last_activity: datetime
    current_task: Optional[str] = None
    metrics: Dict[str, Any] = {}

# Dashboard Models
class DashboardData(BaseModel):
    current_metrics: Dict[str, float]
    alerts: List[AlertResponse]
    recent_decisions: List[DecisionResponse]
    agent_statuses: List[AgentStatus]
    trends: Dict[str, List[float]]