#!/usr/bin/env python3
"""
Enhanced Governance Agent - Safety Layer and Approval Logic
Responsible autonomy with risk evaluation and human oversight
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import uuid

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

@dataclass
class GovernancePolicy:
    """Governance policy definition"""
    policy_id: str
    policy_name: str
    policy_type: str
    conditions: Dict[str, Any]
    action: str
    priority: int
    active: bool

@dataclass
class ApprovalRequest:
    """Approval request structure"""
    request_id: str
    decision_id: str
    title: str
    description: str
    risk_level: str
    financial_impact: float
    confidence_score: float
    urgency: str
    policy_violations: List[Dict[str, Any]]
    recommendation: str
    expires_at: datetime
    created_at: datetime

@dataclass
class GovernanceDecision:
    """Governance decision result"""
    decision_id: str
    action: str  # approve, reject, request_approval
    reasoning: str
    policy_checks: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    approval_required: bool
    auto_approved: bool
    conditions: List[str]
    monitoring_requirements: List[str]

class EnhancedGovernanceAgent(BaseAgent):
    """Safety layer agent with responsible autonomy logic"""
    
    def __init__(self):
        super().__init__("enhanced_governance_agent")
        self.governance_queue = []
        self.approval_queue = []
        self.policies = []
        self.audit_log = []
        self.running = False
        
        # Governance thresholds
        self.auto_approval_thresholds = {
            'max_financial_impact': 15000,
            'min_confidence_score': 0.75,
            'max_risk_level': 'medium',
            'max_implementation_days': 14
        }
        
    async def initialize(self):
        """Initialize the governance agent"""
        await super().initialize()
        logger.info("🛡️ Enhanced Governance Agent initialized - Safety layer active...")
        
        # Subscribe to decision and approval events
        from backend.services.event_bus import event_bus
        await event_bus.subscribe_to_stream(
            'governance', 
            'governance_group', 
            'enhanced_governance_agent',
            self._handle_governance_request
        )
        
        self.running = True
        
        # Start governance processing loops
        asyncio.create_task(self._process_governance_queue())
        asyncio.create_task(self._monitor_approval_queue())
        
        # Initialize governance policies
        await self._initialize_governance_policies()
    
    async def _handle_governance_request(self, event):
        """Handle governance requests from decision agent"""
        try:
            if event.event_type in ['approval_required', 'auto_execute']:
                governance_request = {
                    'id': event.event_id,
                    'event_type': event.event_type,
                    'decision_record': event.data.get('decision_record', {}),
                    'priority': event.data.get('priority', 'medium'),
                    'timestamp': datetime.fromisoformat(event.timestamp)
                }
                
                # Add to governance queue
                self.governance_queue.append(governance_request)
                
                # Sort by priority
                self.governance_queue.sort(
                    key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x['priority'], 1)
                )
                
                await self.update_status("governance_queued", 
                                       f"Queued governance review")
                
                logger.info(f"🛡️ Governance request queued: {event.event_type} "
                           f"(priority: {governance_request['priority']})")
        
        except Exception as e:
            logger.error(f"Error handling governance request: {str(e)}")
    
    async def _process_governance_queue(self):
        """Process governance queue with safety checks"""
        while self.running:
            try:
                if self.governance_queue:
                    governance_request = self.governance_queue.pop(0)
                    await self._review_decision(governance_request)
                else:
                    await asyncio.sleep(5)  # Wait for new requests
                    
            except Exception as e:
                logger.error(f"Error processing governance queue: {str(e)}")
                await asyncio.sleep(10)
    
    async def _review_decision(self, governance_request: Dict[str, Any]):
        """Review decision against governance policies"""
        try:
            await self.update_status("reviewing", "Conducting governance review")
            
            logger.info(f"🔍 Starting governance review: {governance_request['id']}")
            
            decision_record = governance_request['decision_record']
            decision_result = decision_record['decision_result']
            
            # Apply governance policies
            policy_results = await self._apply_governance_policies(decision_result)
            
            # Conduct risk assessment
            risk_assessment = await self._conduct_risk_assessment(decision_result, policy_results)
            
            # Determine governance action
            governance_action = await self._determine_governance_action(
                decision_result, policy_results, risk_assessment
            )
            
            # Create governance decision
            governance_decision = GovernanceDecision(
                decision_id=decision_result['decision_id'],
                action=governance_action['action'],
                reasoning=governance_action['reasoning'],
                policy_checks=policy_results,
                risk_assessment=risk_assessment,
                approval_required=governance_action['approval_required'],
                auto_approved=governance_action['auto_approved'],
                conditions=governance_action.get('conditions', []),
                monitoring_requirements=governance_action.get('monitoring_requirements', [])
            )
            
            # Log governance decision
            audit_entry = {
                'governance_decision': governance_decision.__dict__,
                'original_decision': decision_result,
                'timestamp': datetime.now().isoformat(),
                'agent_id': self.agent_id
            }
            
            self.audit_log.append(audit_entry)
            if len(self.audit_log) > 100:
                self.audit_log = self.audit_log[-100:]
            
            # Execute governance action
            await self._execute_governance_action(governance_decision, decision_record)
            
            await self.update_status("review_complete", "Governance review completed")
            
            logger.info(f"✅ Governance review completed: {governance_decision.action} "
                       f"(approval required: {governance_decision.approval_required})")
        
        except Exception as e:
            logger.error(f"Error reviewing decision: {str(e)}")
            await self.update_status("error", f"Governance review failed: {str(e)}")
    
    async def _apply_governance_policies(self, decision_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply governance policies to decision"""
        try:
            policy_results = []
            
            for policy in self.policies:
                if not policy.active:
                    continue
                
                policy_result = await self._evaluate_policy(policy, decision_result)
                if policy_result:
                    policy_results.append(policy_result)
            
            logger.info(f"Applied {len(self.policies)} policies, {len(policy_results)} triggered")
            return policy_results
            
        except Exception as e:
            logger.error(f"Error applying governance policies: {str(e)}")
            return []
    
    async def _evaluate_policy(self, policy: GovernancePolicy, 
                             decision_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate single policy against decision"""
        try:
            conditions = policy.conditions
            
            # Financial impact policy
            if policy.policy_type == 'financial_limit':
                financial_impact = abs(decision_result.get('financial_impact', 0))
                limit = conditions.get('max_amount', 0)
                
                if financial_impact > limit:
                    return {
                        'policy_id': policy.policy_id,
                        'policy_name': policy.policy_name,
                        'triggered': True,
                        'severity': 'high' if financial_impact > limit * 2 else 'medium',
                        'message': f"Financial impact ${financial_impact:,.0f} exceeds limit ${limit:,.0f}",
                        'action_required': policy.action
                    }
            
            # Risk level policy
            elif policy.policy_type == 'risk_limit':
                risk_level = decision_result.get('risk_assessment', {}).get('overall_risk_level', 'medium')
                max_risk = conditions.get('max_risk_level', 'medium')
                
                risk_values = {'low': 1, 'medium': 2, 'high': 3}
                if risk_values.get(risk_level, 2) > risk_values.get(max_risk, 2):
                    return {
                        'policy_id': policy.policy_id,
                        'policy_name': policy.policy_name,
                        'triggered': True,
                        'severity': 'high',
                        'message': f"Risk level '{risk_level}' exceeds maximum '{max_risk}'",
                        'action_required': policy.action
                    }
            
            # Confidence threshold policy
            elif policy.policy_type == 'confidence_threshold':
                confidence = decision_result.get('confidence_level', 0)
                min_confidence = conditions.get('min_confidence', 0.7)
                
                if confidence < min_confidence:
                    return {
                        'policy_id': policy.policy_id,
                        'policy_name': policy.policy_name,
                        'triggered': True,
                        'severity': 'medium',
                        'message': f"Confidence {confidence:.2f} below threshold {min_confidence:.2f}",
                        'action_required': policy.action
                    }
            
            # Business hours policy
            elif policy.policy_type == 'business_hours':
                current_hour = datetime.now().hour
                start_hour = conditions.get('start_hour', 9)
                end_hour = conditions.get('end_hour', 17)
                
                if not (start_hour <= current_hour <= end_hour):
                    return {
                        'policy_id': policy.policy_id,
                        'policy_name': policy.policy_name,
                        'triggered': True,
                        'severity': 'low',
                        'message': f"Decision made outside business hours ({current_hour}:00)",
                        'action_required': policy.action
                    }
            
            # Scenario type policy
            elif policy.policy_type == 'scenario_restriction':
                scenario_type = decision_result.get('selected_scenario', {}).get('scenario', {}).get('scenario_type', '')
                restricted_types = conditions.get('restricted_types', [])
                
                if any(restricted in str(scenario_type).lower() for restricted in restricted_types):
                    return {
                        'policy_id': policy.policy_id,
                        'policy_name': policy.policy_name,
                        'triggered': True,
                        'severity': 'high',
                        'message': f"Scenario type '{scenario_type}' requires approval",
                        'action_required': policy.action
                    }
            
            return None  # Policy not triggered
            
        except Exception as e:
            logger.error(f"Error evaluating policy {policy.policy_id}: {str(e)}")
            return None
    
    async def _conduct_risk_assessment(self, decision_result: Dict[str, Any], 
                                     policy_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Conduct comprehensive risk assessment"""
        try:
            # Aggregate risk factors
            risk_factors = []
            
            # Policy violations as risk factors
            high_severity_violations = [p for p in policy_results if p.get('severity') == 'high']
            medium_severity_violations = [p for p in policy_results if p.get('severity') == 'medium']
            
            if high_severity_violations:
                risk_factors.append({
                    'factor': 'policy_violations_high',
                    'count': len(high_severity_violations),
                    'impact': 'high'
                })
            
            if medium_severity_violations:
                risk_factors.append({
                    'factor': 'policy_violations_medium',
                    'count': len(medium_severity_violations),
                    'impact': 'medium'
                })
            
            # Financial risk
            financial_impact = abs(decision_result.get('financial_impact', 0))
            if financial_impact > 50000:
                risk_factors.append({
                    'factor': 'high_financial_impact',
                    'value': financial_impact,
                    'impact': 'high'
                })
            elif financial_impact > 20000:
                risk_factors.append({
                    'factor': 'medium_financial_impact',
                    'value': financial_impact,
                    'impact': 'medium'
                })
            
            # Confidence risk
            confidence = decision_result.get('confidence_level', 0)
            if confidence < 0.6:
                risk_factors.append({
                    'factor': 'low_confidence',
                    'value': confidence,
                    'impact': 'high'
                })
            elif confidence < 0.75:
                risk_factors.append({
                    'factor': 'medium_confidence',
                    'value': confidence,
                    'impact': 'medium'
                })
            
            # Calculate overall risk score
            overall_risk_score = await self._calculate_risk_score(risk_factors)
            
            # Determine risk level
            if overall_risk_score > 0.7:
                overall_risk_level = 'high'
            elif overall_risk_score > 0.4:
                overall_risk_level = 'medium'
            else:
                overall_risk_level = 'low'
            
            return {
                'overall_risk_level': overall_risk_level,
                'overall_risk_score': overall_risk_score,
                'risk_factors': risk_factors,
                'mitigation_required': overall_risk_score > 0.5,
                'monitoring_required': overall_risk_score > 0.3
            }
            
        except Exception as e:
            logger.error(f"Error conducting risk assessment: {str(e)}")
            return {'overall_risk_level': 'medium', 'overall_risk_score': 0.5}
    
    async def _calculate_risk_score(self, risk_factors: List[Dict[str, Any]]) -> float:
        """Calculate numerical risk score from risk factors"""
        try:
            if not risk_factors:
                return 0.0
            
            total_score = 0.0
            
            for factor in risk_factors:
                impact = factor.get('impact', 'medium')
                
                if impact == 'high':
                    total_score += 0.3
                elif impact == 'medium':
                    total_score += 0.2
                else:
                    total_score += 0.1
            
            # Normalize to 0-1 range
            return min(1.0, total_score)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 0.5
    
    async def _determine_governance_action(self, decision_result: Dict[str, Any],
                                         policy_results: List[Dict[str, Any]],
                                         risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Determine governance action based on policies and risk"""
        try:
            # Check for blocking policy violations
            blocking_violations = [p for p in policy_results if p.get('action_required') == 'block']
            if blocking_violations:
                return {
                    'action': 'reject',
                    'reasoning': f"Decision blocked by {len(blocking_violations)} policy violation(s)",
                    'approval_required': False,
                    'auto_approved': False
                }
            
            # Check for approval-requiring violations
            approval_violations = [p for p in policy_results if p.get('action_required') == 'require_approval']
            
            # Check auto-approval criteria
            can_auto_approve = await self._check_auto_approval_criteria(decision_result, risk_assessment)
            
            if approval_violations or not can_auto_approve or decision_result.get('requires_approval', False):
                # Requires human approval
                urgency = await self._calculate_urgency(decision_result, risk_assessment)
                
                return {
                    'action': 'request_approval',
                    'reasoning': await self._generate_approval_reasoning(decision_result, policy_results, risk_assessment),
                    'approval_required': True,
                    'auto_approved': False,
                    'urgency': urgency,
                    'conditions': await self._generate_approval_conditions(decision_result, policy_results),
                    'monitoring_requirements': await self._generate_monitoring_requirements(decision_result, risk_assessment)
                }
            else:
                # Can auto-approve
                return {
                    'action': 'approve',
                    'reasoning': await self._generate_auto_approval_reasoning(decision_result, risk_assessment),
                    'approval_required': False,
                    'auto_approved': True,
                    'conditions': await self._generate_execution_conditions(decision_result),
                    'monitoring_requirements': await self._generate_monitoring_requirements(decision_result, risk_assessment)
                }
            
        except Exception as e:
            logger.error(f"Error determining governance action: {str(e)}")
            return {
                'action': 'request_approval',
                'reasoning': 'Error in governance evaluation - defaulting to approval required',
                'approval_required': True,
                'auto_approved': False
            }
    
    async def _check_auto_approval_criteria(self, decision_result: Dict[str, Any],
                                          risk_assessment: Dict[str, Any]) -> bool:
        """Check if decision meets auto-approval criteria"""
        try:
            thresholds = self.auto_approval_thresholds
            
            # Financial impact check
            financial_impact = abs(decision_result.get('financial_impact', 0))
            if financial_impact > thresholds['max_financial_impact']:
                return False
            
            # Confidence check
            confidence = decision_result.get('confidence_level', 0)
            if confidence < thresholds['min_confidence_score']:
                return False
            
            # Risk level check
            risk_level = risk_assessment.get('overall_risk_level', 'medium')
            if risk_level == 'high':
                return False
            
            # Implementation time check (if available)
            execution_plan = decision_result.get('execution_plan', [])
            if execution_plan:
                total_hours = sum(step.get('duration_hours', 0) for step in execution_plan)
                total_days = total_hours / 24
                if total_days > thresholds['max_implementation_days']:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking auto-approval criteria: {str(e)}")
            return False
    
    async def _calculate_urgency(self, decision_result: Dict[str, Any],
                               risk_assessment: Dict[str, Any]) -> str:
        """Calculate urgency level for approval requests"""
        try:
            urgency_factors = 0
            
            # High financial impact
            if abs(decision_result.get('financial_impact', 0)) > 50000:
                urgency_factors += 1
            
            # High risk
            if risk_assessment.get('overall_risk_level') == 'high':
                urgency_factors += 1
            
            # Critical business impact
            business_impact = decision_result.get('selected_scenario', {}).get('business_impact', '')
            if 'critical' in business_impact.lower():
                urgency_factors += 1
            
            # Time sensitivity
            time_to_impact = decision_result.get('selected_scenario', {}).get('scenario', {}).get('time_to_impact', 14)
            if time_to_impact <= 3:
                urgency_factors += 1
            
            if urgency_factors >= 3:
                return 'critical'
            elif urgency_factors >= 2:
                return 'high'
            elif urgency_factors >= 1:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Error calculating urgency: {str(e)}")
            return 'medium'
    
    async def _generate_approval_reasoning(self, decision_result: Dict[str, Any],
                                         policy_results: List[Dict[str, Any]],
                                         risk_assessment: Dict[str, Any]) -> str:
        """Generate reasoning for approval requirement"""
        try:
            reasons = []
            
            # Policy violations
            if policy_results:
                high_violations = [p for p in policy_results if p.get('severity') == 'high']
                medium_violations = [p for p in policy_results if p.get('severity') == 'medium']
                
                if high_violations:
                    reasons.append(f"{len(high_violations)} high-severity policy violation(s)")
                if medium_violations:
                    reasons.append(f"{len(medium_violations)} medium-severity policy violation(s)")
            
            # Risk factors
            risk_level = risk_assessment.get('overall_risk_level', 'medium')
            if risk_level == 'high':
                reasons.append("High risk level requires human oversight")
            
            # Financial impact
            financial_impact = abs(decision_result.get('financial_impact', 0))
            if financial_impact > 25000:
                reasons.append(f"Significant financial impact: ${financial_impact:,.0f}")
            
            # Confidence concerns
            confidence = decision_result.get('confidence_level', 0)
            if confidence < 0.7:
                reasons.append(f"Low confidence score: {confidence:.2f}")
            
            # Business impact
            business_impact = decision_result.get('selected_scenario', {}).get('business_impact', '')
            if 'critical' in business_impact.lower():
                reasons.append("Critical business impact requires approval")
            
            if not reasons:
                reasons.append("Standard approval process for significant decisions")
            
            return f"Approval required due to: {', '.join(reasons)}"
            
        except Exception as e:
            logger.error(f"Error generating approval reasoning: {str(e)}")
            return "Approval required for governance compliance"
    
    async def _generate_auto_approval_reasoning(self, decision_result: Dict[str, Any],
                                              risk_assessment: Dict[str, Any]) -> str:
        """Generate reasoning for auto-approval"""
        try:
            reasons = []
            
            # Low risk
            if risk_assessment.get('overall_risk_level') == 'low':
                reasons.append("low risk profile")
            
            # High confidence
            confidence = decision_result.get('confidence_level', 0)
            if confidence >= 0.75:
                reasons.append(f"high confidence ({confidence:.2f})")
            
            # Reasonable financial impact
            financial_impact = abs(decision_result.get('financial_impact', 0))
            if financial_impact <= 15000:
                reasons.append(f"manageable financial impact (${financial_impact:,.0f})")
            
            # No policy violations
            reasons.append("no policy violations")
            
            return f"Auto-approved based on: {', '.join(reasons)}"
            
        except Exception as e:
            logger.error(f"Error generating auto-approval reasoning: {str(e)}")
            return "Auto-approved within governance parameters"
    
    async def _generate_approval_conditions(self, decision_result: Dict[str, Any],
                                          policy_results: List[Dict[str, Any]]) -> List[str]:
        """Generate conditions for approval"""
        conditions = []
        
        try:
            # Financial conditions
            financial_impact = abs(decision_result.get('financial_impact', 0))
            if financial_impact > 25000:
                conditions.append("Obtain CFO approval for financial commitment")
            
            # Risk conditions
            risk_level = decision_result.get('risk_assessment', {}).get('overall_risk_level', 'medium')
            if risk_level == 'high':
                conditions.append("Implement additional risk mitigation measures")
                conditions.append("Establish clear rollback procedures")
            
            # Policy-specific conditions
            for policy_result in policy_results:
                if policy_result.get('triggered'):
                    policy_name = policy_result.get('policy_name', 'Unknown Policy')
                    conditions.append(f"Address {policy_name} requirements before execution")
            
            # Implementation conditions
            complexity = decision_result.get('selected_scenario', {}).get('implementation_complexity', 'medium')
            if complexity == 'high':
                conditions.append("Conduct pilot implementation before full rollout")
            
            return conditions[:5]  # Limit to 5 conditions
            
        except Exception as e:
            logger.error(f"Error generating approval conditions: {str(e)}")
            return ["Ensure proper implementation oversight"]
    
    async def _generate_execution_conditions(self, decision_result: Dict[str, Any]) -> List[str]:
        """Generate conditions for execution"""
        conditions = []
        
        try:
            # Standard execution conditions
            conditions.append("Monitor key performance indicators during implementation")
            conditions.append("Report progress at regular intervals")
            
            # Scenario-specific conditions
            scenario_type = decision_result.get('selected_scenario', {}).get('scenario', {}).get('scenario_type', '')
            
            if 'pricing' in str(scenario_type).lower():
                conditions.append("Monitor competitor responses to pricing changes")
            elif 'marketing' in str(scenario_type).lower():
                conditions.append("Track campaign performance metrics daily")
            elif 'operational' in str(scenario_type).lower():
                conditions.append("Ensure minimal disruption to ongoing operations")
            
            return conditions[:3]  # Limit to 3 conditions
            
        except Exception as e:
            logger.error(f"Error generating execution conditions: {str(e)}")
            return ["Follow standard implementation procedures"]
    
    async def _generate_monitoring_requirements(self, decision_result: Dict[str, Any],
                                             risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate monitoring requirements"""
        requirements = []
        
        try:
            # Always monitor the primary metric
            requirements.append("Monitor primary business metric daily")
            
            # Risk-based monitoring
            if risk_assessment.get('overall_risk_level') == 'high':
                requirements.append("Conduct hourly risk assessment for first 48 hours")
                requirements.append("Establish emergency response procedures")
            elif risk_assessment.get('overall_risk_level') == 'medium':
                requirements.append("Review risk indicators twice daily")
            
            # Financial monitoring
            financial_impact = abs(decision_result.get('financial_impact', 0))
            if financial_impact > 15000:
                requirements.append("Track financial performance against projections")
            
            # Scenario-specific monitoring
            monitoring_metrics = decision_result.get('monitoring_metrics', [])
            for metric in monitoring_metrics[:3]:  # Top 3 metrics
                requirements.append(f"Monitor {metric} performance")
            
            return requirements[:5]  # Limit to 5 requirements
            
        except Exception as e:
            logger.error(f"Error generating monitoring requirements: {str(e)}")
            return ["Monitor implementation progress and outcomes"]
    
    async def _execute_governance_action(self, governance_decision: GovernanceDecision,
                                       decision_record: Dict[str, Any]):
        """Execute the governance action"""
        try:
            if governance_decision.action == 'approve':
                # Auto-approve and execute
                await self._auto_approve_decision(governance_decision, decision_record)
            elif governance_decision.action == 'request_approval':
                # Create approval request
                await self._create_approval_request(governance_decision, decision_record)
            elif governance_decision.action == 'reject':
                # Reject decision
                await self._reject_decision(governance_decision, decision_record)
            
            # Publish governance result
            await self._publish_governance_result(governance_decision, decision_record)
            
        except Exception as e:
            logger.error(f"Error executing governance action: {str(e)}")
    
    async def _auto_approve_decision(self, governance_decision: GovernanceDecision,
                                   decision_record: Dict[str, Any]):
        """Auto-approve and execute decision"""
        try:
            # Log auto-approval
            logger.info(f"🟢 Auto-approved decision: {governance_decision.decision_id}")
            
            # Here you would integrate with execution systems
            # For now, we'll just log the execution
            execution_plan = decision_record['decision_result'].get('execution_plan', [])
            logger.info(f"Executing {len(execution_plan)} implementation steps")
            
            # Update status
            await self.update_status("auto_approved", f"Decision {governance_decision.decision_id} auto-approved and executing")
            
        except Exception as e:
            logger.error(f"Error auto-approving decision: {str(e)}")
    
    async def _create_approval_request(self, governance_decision: GovernanceDecision,
                                     decision_record: Dict[str, Any]):
        """Create approval request for human review"""
        try:
            decision_result = decision_record['decision_result']
            
            approval_request = ApprovalRequest(
                request_id=str(uuid.uuid4()),
                decision_id=governance_decision.decision_id,
                title=decision_result.get('selected_scenario', {}).get('scenario', {}).get('title', 'Decision Approval Required'),
                description=governance_decision.reasoning,
                risk_level=governance_decision.risk_assessment.get('overall_risk_level', 'medium'),
                financial_impact=decision_result.get('financial_impact', 0),
                confidence_score=decision_result.get('confidence_level', 0),
                urgency=getattr(governance_decision, 'urgency', 'medium'),
                policy_violations=[p for p in governance_decision.policy_checks if p.get('triggered')],
                recommendation=decision_record['simulation_report'].get('recommendation', ''),
                expires_at=datetime.now() + timedelta(hours=24),  # 24-hour expiry
                created_at=datetime.now()
            )
            
            # Add to approval queue
            self.approval_queue.append(approval_request)
            
            logger.info(f"🟡 Created approval request: {approval_request.request_id}")
            
            # Update status
            await self.update_status("approval_requested", f"Decision {governance_decision.decision_id} requires approval")
            
        except Exception as e:
            logger.error(f"Error creating approval request: {str(e)}")
    
    async def _reject_decision(self, governance_decision: GovernanceDecision,
                             decision_record: Dict[str, Any]):
        """Reject decision due to policy violations"""
        try:
            logger.info(f"🔴 Rejected decision: {governance_decision.decision_id}")
            logger.info(f"Rejection reason: {governance_decision.reasoning}")
            
            # Update status
            await self.update_status("decision_rejected", f"Decision {governance_decision.decision_id} rejected")
            
        except Exception as e:
            logger.error(f"Error rejecting decision: {str(e)}")
    
    async def _publish_governance_result(self, governance_decision: GovernanceDecision,
                                       decision_record: Dict[str, Any]):
        """Publish governance result to event bus"""
        from backend.services.event_bus import event_bus, Event
        
        governance_event = Event(
            event_id=str(uuid.uuid4()),
            event_type='governance_completed',
            source='enhanced_governance_agent',
            timestamp=datetime.now().isoformat(),
            data={
                'governance_decision': governance_decision.__dict__,
                'original_decision': decision_record
            }
        )
        
        await event_bus.publish_event('governance', governance_event)
        
        logger.info(f"🛡️ Published governance result for {governance_decision.decision_id}")
    
    async def _monitor_approval_queue(self):
        """Monitor approval queue for expired requests"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check for expired approval requests
                expired_requests = [
                    req for req in self.approval_queue 
                    if req.expires_at < current_time
                ]
                
                for expired_request in expired_requests:
                    logger.warning(f"⏰ Approval request expired: {expired_request.request_id}")
                    self.approval_queue.remove(expired_request)
                
                # Sleep for 5 minutes before next check
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error monitoring approval queue: {str(e)}")
                await asyncio.sleep(60)
    
    async def _initialize_governance_policies(self):
        """Initialize governance policies"""
        self.policies = [
            GovernancePolicy(
                policy_id="financial_limit_high",
                policy_name="High Financial Impact Limit",
                policy_type="financial_limit",
                conditions={"max_amount": 50000},
                action="require_approval",
                priority=1,
                active=True
            ),
            GovernancePolicy(
                policy_id="financial_limit_medium",
                policy_name="Medium Financial Impact Limit",
                policy_type="financial_limit",
                conditions={"max_amount": 25000},
                action="require_approval",
                priority=2,
                active=True
            ),
            GovernancePolicy(
                policy_id="risk_limit_high",
                policy_name="High Risk Restriction",
                policy_type="risk_limit",
                conditions={"max_risk_level": "medium"},
                action="require_approval",
                priority=1,
                active=True
            ),
            GovernancePolicy(
                policy_id="confidence_threshold",
                policy_name="Minimum Confidence Threshold",
                policy_type="confidence_threshold",
                conditions={"min_confidence": 0.6},
                action="require_approval",
                priority=3,
                active=True
            ),
            GovernancePolicy(
                policy_id="business_hours",
                policy_name="Business Hours Restriction",
                policy_type="business_hours",
                conditions={"start_hour": 9, "end_hour": 17},
                action="require_approval",
                priority=4,
                active=True
            ),
            GovernancePolicy(
                policy_id="pricing_restriction",
                policy_name="Pricing Change Restriction",
                policy_type="scenario_restriction",
                conditions={"restricted_types": ["pricing_adjustment"]},
                action="require_approval",
                priority=2,
                active=True
            )
        ]
        
        logger.info(f"Initialized {len(self.policies)} governance policies")
    
    def stop_governance(self):
        """Stop the governance processing"""
        self.running = False
        logger.info("🛑 Enhanced Governance Agent stopping...")

# Global enhanced governance agent instance
enhanced_governance_agent = EnhancedGovernanceAgent() 