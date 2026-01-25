export interface Metric {
  id: number;
  metric_type: string;
  value: number;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface Alert {
  id: number;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  metric_type: string;
  threshold_value?: number;
  current_value?: number;
  agent_type: string;
  created_at: string;
  resolved_at?: string;
}

export interface DecisionScenario {
  name: string;
  description: string;
  parameters: Record<string, any>;
  predicted_outcome: Record<string, number>;
  confidence_score: number;
  risk_score: number;
}

export interface Decision {
  id: number;
  title: string;
  description: string;
  scenarios: DecisionScenario[];
  recommended_scenario: string;
  confidence_score: number;
  financial_impact: number;
  requires_approval: boolean;
  reasoning: string;
  status: 'pending' | 'approved' | 'rejected' | 'executed';
  created_at: string;
  approved_at?: string;
  executed_at?: string;
}

export interface AgentStatus {
  agent_type: string;
  status: string;
  last_activity: string;
  current_task?: string;
  metrics: Record<string, any>;
}

export interface DashboardData {
  current_metrics: Record<string, number>;
  alerts: Alert[];
  recent_decisions: Decision[];
  agent_statuses: AgentStatus[];
  trends: Record<string, number[]>;
}

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface ApprovalRequest {
  decision: Decision;
  analysis: any;
  policy_violations: any[];
  recommendation: string;
  urgency: 'low' | 'medium' | 'high';
  requested_at: string;
  expires_at: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'critical';
  redis_healthy: boolean;
  agents_active: string;
  orchestrator_running: boolean;
  openai_available: boolean;
  timestamp: string;
}