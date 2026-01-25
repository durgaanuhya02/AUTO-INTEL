from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, Enum
from sqlalchemy.sql import func
from ..core.database import Base
from .schemas import MetricType, AlertSeverity, DecisionStatus, AgentType
import enum

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(Enum(MetricType), nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    metric_type = Column(Enum(MetricType), nullable=False, index=True)
    threshold_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    agent_type = Column(Enum(AgentType), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class Decision(Base):
    __tablename__ = "decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    scenarios = Column(JSON, nullable=False)  # List of DecisionScenario
    recommended_scenario = Column(String(255), nullable=False)
    confidence_score = Column(Float, nullable=False)
    financial_impact = Column(Float, nullable=False)
    requires_approval = Column(Boolean, nullable=False, default=False)
    reasoning = Column(Text, nullable=False)
    status = Column(Enum(DecisionStatus), nullable=False, default=DecisionStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(255), nullable=True)

class AgentActivity(Base):
    __tablename__ = "agent_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(Enum(AgentType), nullable=False, index=True)
    activity_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class AgentCommunication(Base):
    __tablename__ = "agent_communications"
    
    id = Column(Integer, primary_key=True, index=True)
    from_agent = Column(Enum(AgentType), nullable=False, index=True)
    to_agent = Column(Enum(AgentType), nullable=True, index=True)
    message_type = Column(String(100), nullable=False)
    content = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, nullable=False, default=False)