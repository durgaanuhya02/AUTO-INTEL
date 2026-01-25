-- Initialize the Agentic AI database

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE metric_type AS ENUM ('revenue', 'orders', 'churn_risk', 'delivery_delay', 'customer_satisfaction');
CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE decision_status AS ENUM ('pending', 'approved', 'rejected', 'executed');
CREATE TYPE agent_type AS ENUM ('observer', 'analyst', 'simulation', 'decision', 'governance');

-- Metrics table
CREATE TABLE metrics (
    id SERIAL PRIMARY KEY,
    metric_type metric_type NOT NULL,
    value DECIMAL(12,2) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_metrics_type_timestamp ON metrics(metric_type, timestamp);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);

-- Alerts table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    severity alert_severity NOT NULL,
    metric_type metric_type NOT NULL,
    threshold_value DECIMAL(12,2),
    current_value DECIMAL(12,2),
    agent_type agent_type NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
CREATE INDEX idx_alerts_agent_type ON alerts(agent_type);

-- Decisions table
CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    scenarios JSONB NOT NULL,
    recommended_scenario VARCHAR(255) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    financial_impact DECIMAL(12,2) NOT NULL,
    requires_approval BOOLEAN NOT NULL DEFAULT FALSE,
    reasoning TEXT NOT NULL,
    status decision_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE,
    approved_by VARCHAR(255)
);

CREATE INDEX idx_decisions_status ON decisions(status);
CREATE INDEX idx_decisions_created_at ON decisions(created_at);
CREATE INDEX idx_decisions_requires_approval ON decisions(requires_approval);

-- Agent activities table
CREATE TABLE agent_activities (
    id SERIAL PRIMARY KEY,
    agent_type agent_type NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agent_activities_type_timestamp ON agent_activities(agent_type, timestamp);

-- Agent communications table
CREATE TABLE agent_communications (
    id SERIAL PRIMARY KEY,
    from_agent agent_type NOT NULL,
    to_agent agent_type,
    message_type VARCHAR(100) NOT NULL,
    content JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_agent_communications_to_agent ON agent_communications(to_agent);
CREATE INDEX idx_agent_communications_processed ON agent_communications(processed);

-- Insert sample data for testing
INSERT INTO metrics (metric_type, value, timestamp) VALUES
    ('revenue', 15000.00, NOW() - INTERVAL '1 hour'),
    ('orders', 150, NOW() - INTERVAL '1 hour'),
    ('churn_risk', 0.15, NOW() - INTERVAL '1 hour'),
    ('delivery_delay', 2.5, NOW() - INTERVAL '1 hour'),
    ('customer_satisfaction', 4.2, NOW() - INTERVAL '1 hour');

-- Create a view for dashboard summary
CREATE VIEW dashboard_summary AS
SELECT 
    m.metric_type,
    m.value as current_value,
    LAG(m.value) OVER (PARTITION BY m.metric_type ORDER BY m.timestamp) as previous_value,
    m.timestamp
FROM metrics m
WHERE m.timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY m.metric_type, m.timestamp DESC;