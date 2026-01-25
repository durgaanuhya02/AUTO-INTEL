from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import json

from .base_agent import BaseAgent
from backend.models.schemas import AgentType, AgentMessage, DecisionStatus

class GovernanceAgent(BaseAgent):
    def __init__(self, redis_client, db_session):
        super().__init__(AgentType.GOVERNANCE, redis_client)
        self.db_session = db_session
        self.pending_decisions = []
        self.policy_rules = {}
        self.audit_log = []
    
    async def initialize(self):
        await self.update_status("initializing", "Loading governance policies")
        await self._load_policy_rules()
        await self.update_status("active", "Monitoring decisions")
        self.logger.info("Governance agent initialized successfully")
    
    async def process(self):
        await self.update_status("processing", "Reviewing decisions")
        
        try:
            if self.pending_decisions:
                for decision_package in self.pending_decisions:
                    result = await self._review_decision(decision_package)
                    if result:
                        await self._handle_decision_result(result)
                
                self.pending_decisions.clear()
            
            # Periodic audit and compliance checks
            await self._perform_audit_checks()
            
            await self.update_status("active", "Governance review complete")
            
        except Exception as e:
            self.logger.error(f"Error in governance processing: {e}")
            await self.update_status("error", f"Governance error: {str(e)}")
    
    async def handle_message(self, message: AgentMessage):
        await super().handle_message(message)
        
        if message.message_type == "decision_ready":
            self.pending_decisions.append(message.content)
            await self.update_status("processing", "Reviewing new decision")
        
        elif message.message_type == "human_approval":
            await self._handle_human_approval(message.content)
        
        elif message.message_type == "execution_complete":
            await self._log_execution(message.content)
    
    async def _review_decision(self, decision_package: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Review decision against governance policies"""
        
        try:
            decision_data = decision_package["decision"]
            analysis = decision_package["analysis"]
            
            # Apply policy rules
            policy_result = await self._apply_policy_rules(decision_data, analysis)
            
            # Determine final status
            if decision_data["requires_approval"] or policy_result["requires_approval"]:
                status = DecisionStatus.PENDING
                action = "request_human_approval"
            elif policy_result["approved"]:
                status = DecisionStatus.APPROVED
                action = "auto_approve"
            else:
                status = DecisionStatus.REJECTED
                action = "reject"
            
            # Create audit entry
            audit_entry = {
                "decision_id": decision_data.get("id", "pending"),
                "decision_title": decision_data["title"],
                "recommended_scenario": decision_data["recommended_scenario"],
                "financial_impact": decision_data["financial_impact"],
                "confidence_score": decision_data["confidence_score"],
                "policy_result": policy_result,
                "final_status": status,
                "action": action,
                "timestamp": datetime.utcnow().isoformat(),
                "governance_agent_id": str(id(self))
            }
            
            self.audit_log.append(audit_entry)
            
            # Store in Redis for dashboard access
            await self.redis_client.lpush("governance_log", json.dumps(audit_entry, default=str))
            await self.redis_client.ltrim("governance_log", 0, 99)  # Keep last 100 entries
            
            result = {
                "decision_package": decision_package,
                "audit_entry": audit_entry,
                "status": status,
                "action": action,
                "policy_violations": policy_result.get("violations", []),
                "approval_required": status == DecisionStatus.PENDING
            }
            
            self.logger.info(f"Decision reviewed: {action} - {decision_data['title']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error reviewing decision: {e}")
            return None
    
    async def _apply_policy_rules(self, decision_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Apply governance policy rules to the decision"""
        
        violations = []
        requires_approval = False
        approved = True
        
        # Financial impact rules
        financial_impact = abs(decision_data["financial_impact"])
        
        if financial_impact > self.policy_rules["max_auto_financial_impact"]:
            violations.append({
                "rule": "max_auto_financial_impact",
                "threshold": self.policy_rules["max_auto_financial_impact"],
                "actual": financial_impact,
                "severity": "high"
            })
            requires_approval = True
        
        # Confidence threshold rules
        confidence = decision_data["confidence_score"]
        if confidence < self.policy_rules["min_confidence_auto_approve"]:
            violations.append({
                "rule": "min_confidence_auto_approve",
                "threshold": self.policy_rules["min_confidence_auto_approve"],
                "actual": confidence,
                "severity": "medium"
            })
            requires_approval = True
        
        # Risk assessment rules
        scenarios = decision_data.get("scenarios", [])
        recommended_scenario = decision_data["recommended_scenario"]
        
        for scenario in scenarios:
            if scenario["name"] == recommended_scenario:
                risk_score = scenario["risk_score"]
                if risk_score > self.policy_rules["max_auto_risk_score"]:
                    violations.append({
                        "rule": "max_auto_risk_score",
                        "threshold": self.policy_rules["max_auto_risk_score"],
                        "actual": risk_score,
                        "severity": "high"
                    })
                    requires_approval = True
                break
        
        # Business hours rule
        current_hour = datetime.utcnow().hour
        if not (self.policy_rules["business_hours_start"] <= current_hour <= self.policy_rules["business_hours_end"]):
            violations.append({
                "rule": "business_hours_only",
                "message": "Decisions outside business hours require approval",
                "severity": "low"
            })
            requires_approval = True
        
        # Metric-specific rules
        anomaly = analysis["anomaly"]
        metric_type = anomaly["metric_type"]
        
        if metric_type in self.policy_rules["critical_metrics"]:
            violations.append({
                "rule": "critical_metrics",
                "message": f"Decisions affecting {metric_type} require approval",
                "severity": "medium"
            })
            requires_approval = True
        
        # Scenario-specific rules
        restricted_scenarios = self.policy_rules.get("restricted_scenarios", [])
        if any(restricted in recommended_scenario.lower() for restricted in restricted_scenarios):
            violations.append({
                "rule": "restricted_scenarios",
                "message": f"Scenario type '{recommended_scenario}' requires approval",
                "severity": "high"
            })
            requires_approval = True
        
        # If there are violations, decision needs review
        if violations and not requires_approval:
            # Some violations might not require approval but should be logged
            pass
        
        return {
            "approved": approved and not requires_approval,
            "requires_approval": requires_approval,
            "violations": violations,
            "policy_version": self.policy_rules.get("version", "1.0"),
            "review_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_decision_result(self, result: Dict[str, Any]):
        """Handle the result of decision review"""
        
        action = result["action"]
        decision_package = result["decision_package"]
        
        if action == "auto_approve":
            # Auto-approve and execute
            await self.send_message(
                None,  # Broadcast
                "decision_approved",
                {
                    "decision": decision_package["decision"],
                    "auto_approved": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Trigger execution (in a real system, this would integrate with execution systems)
            await self._trigger_execution(decision_package["decision"])
        
        elif action == "request_human_approval":
            # Send to human approval queue
            await self._request_human_approval(decision_package, result)
        
        elif action == "reject":
            # Reject decision
            await self.send_message(
                None,  # Broadcast
                "decision_rejected",
                {
                    "decision": decision_package["decision"],
                    "violations": result["policy_violations"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    async def _request_human_approval(self, decision_package: Dict[str, Any], review_result: Dict[str, Any]):
        """Request human approval for the decision"""
        
        approval_request = {
            "decision": decision_package["decision"],
            "analysis": decision_package["analysis"],
            "policy_violations": review_result["policy_violations"],
            "recommendation": "approve" if len(review_result["policy_violations"]) <= 2 else "review_carefully",
            "urgency": self._calculate_urgency(decision_package),
            "requested_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        # Store in approval queue
        await self.redis_client.lpush("approval_queue", json.dumps(approval_request, default=str))
        
        # Notify dashboard
        await self.send_message(
            None,  # Broadcast
            "approval_requested",
            approval_request
        )
        
        self.logger.info(f"Human approval requested for: {decision_package['decision']['title']}")
    
    async def _handle_human_approval(self, approval_data: Dict[str, Any]):
        """Handle human approval response"""
        
        decision_id = approval_data.get("decision_id")
        approved = approval_data.get("approved", False)
        comments = approval_data.get("comments", "")
        approver = approval_data.get("approver", "unknown")
        
        # Log the approval
        approval_log = {
            "decision_id": decision_id,
            "approved": approved,
            "approver": approver,
            "comments": comments,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.audit_log.append(approval_log)
        
        if approved:
            # Execute the decision
            await self.send_message(
                None,  # Broadcast
                "decision_approved",
                {
                    "decision_id": decision_id,
                    "human_approved": True,
                    "approver": approver,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            await self.send_message(
                None,  # Broadcast
                "decision_rejected",
                {
                    "decision_id": decision_id,
                    "human_rejected": True,
                    "reason": comments,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        self.logger.info(f"Human approval processed: {'approved' if approved else 'rejected'} by {approver}")
    
    def _calculate_urgency(self, decision_package: Dict[str, Any]) -> str:
        """Calculate urgency level for human approval"""
        
        decision = decision_package["decision"]
        analysis = decision_package["analysis"]
        
        # High urgency factors
        high_urgency_factors = 0
        
        # High financial impact
        if abs(decision["financial_impact"]) > 50000:
            high_urgency_factors += 1
        
        # Critical metric anomaly
        if analysis["anomaly"].get("severity") == "critical":
            high_urgency_factors += 1
        
        # High confidence but high risk
        if decision["confidence_score"] > 0.8 and any(s["risk_score"] > 0.7 for s in decision["scenarios"]):
            high_urgency_factors += 1
        
        if high_urgency_factors >= 2:
            return "high"
        elif high_urgency_factors == 1:
            return "medium"
        else:
            return "low"
    
    async def _trigger_execution(self, decision: Dict[str, Any]):
        """Trigger execution of approved decision"""
        
        # In a real system, this would integrate with execution systems
        # For demo, we'll simulate execution
        
        execution_data = {
            "decision_id": decision.get("id", "demo"),
            "scenario": decision["recommended_scenario"],
            "parameters": {},  # Would extract from scenario
            "status": "executing",
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Store execution status
        await self.redis_client.set(
            f"execution:{decision.get('id', 'demo')}",
            json.dumps(execution_data, default=str),
            ex=3600
        )
        
        self.logger.info(f"Execution triggered for: {decision['title']}")
    
    async def _perform_audit_checks(self):
        """Perform periodic audit and compliance checks"""
        
        try:
            # Check for overdue approvals
            approval_queue_length = await self.redis_client.llen("approval_queue")
            
            if approval_queue_length > 10:
                self.logger.warning(f"High number of pending approvals: {approval_queue_length}")
            
            # Check recent decision patterns
            if len(self.audit_log) > 20:
                recent_decisions = self.audit_log[-20:]
                auto_approval_rate = sum(1 for d in recent_decisions if d.get("action") == "auto_approve") / len(recent_decisions)
                
                if auto_approval_rate < 0.3:
                    self.logger.info(f"Low auto-approval rate: {auto_approval_rate:.2%}")
                elif auto_approval_rate > 0.8:
                    self.logger.info(f"High auto-approval rate: {auto_approval_rate:.2%}")
            
        except Exception as e:
            self.logger.error(f"Error in audit checks: {e}")
    
    async def _log_execution(self, execution_data: Dict[str, Any]):
        """Log execution completion"""
        
        log_entry = {
            "type": "execution_complete",
            "decision_id": execution_data.get("decision_id"),
            "status": execution_data.get("status"),
            "result": execution_data.get("result"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.audit_log.append(log_entry)
        self.logger.info(f"Execution logged: {execution_data.get('decision_id')}")
    
    async def _load_policy_rules(self):
        """Load governance policy rules"""
        
        self.policy_rules = {
            "version": "1.0",
            "max_auto_financial_impact": 10000,  # USD
            "min_confidence_auto_approve": 0.75,
            "max_auto_risk_score": 0.6,
            "business_hours_start": 9,  # 9 AM
            "business_hours_end": 17,   # 5 PM
            "critical_metrics": ["revenue", "churn_risk"],
            "restricted_scenarios": ["price_optimization", "logistics_optimization"],
            "max_pending_approvals": 20,
            "approval_timeout_hours": 24
        }
        
        self.logger.info("Governance policy rules loaded")