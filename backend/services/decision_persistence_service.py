"""
Decision State Persistence Service
Stores and manages decision lifecycle for auditability and trust
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from .redis_cache_service import redis_cache_service
from .event_bus import event_bus, EventType, publish_decision_proposed

logger = logging.getLogger(__name__)

class DecisionStatus(Enum):
    """Decision lifecycle states"""
    PROPOSED = "proposed"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    FAILED = "failed"
    EXPIRED = "expired"

class DecisionCategory(Enum):
    """Decision categories"""
    PRICING = "pricing"
    INVENTORY = "inventory"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    CUSTOMER_SERVICE = "customer_service"
    RISK_MANAGEMENT = "risk_management"

@dataclass
class Decision:
    """Decision data structure"""
    id: str
    title: str
    description: str
    category: DecisionCategory
    proposed_action: str
    reasoning: str
    confidence: float
    estimated_impact: str
    estimated_value: float
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    
    # Lifecycle
    status: DecisionStatus
    proposed_by: str
    proposed_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Context
    correlation_id: Optional[str] = None
    triggering_event: Optional[str] = None
    supporting_data: Optional[Dict[str, Any]] = None
    
    # Execution
    execution_plan: Optional[List[str]] = None
    execution_results: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert enums and datetime objects
        data['category'] = self.category.value
        data['status'] = self.status.value
        data['proposed_at'] = self.proposed_at.isoformat()
        data['approved_at'] = self.approved_at.isoformat() if self.approved_at else None
        data['implemented_at'] = self.implemented_at.isoformat() if self.implemented_at else None
        data['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Decision':
        """Create from dictionary"""
        # Convert string values back to proper types
        data['category'] = DecisionCategory(data['category'])
        data['status'] = DecisionStatus(data['status'])
        data['proposed_at'] = datetime.fromisoformat(data['proposed_at'])
        data['approved_at'] = datetime.fromisoformat(data['approved_at']) if data['approved_at'] else None
        data['implemented_at'] = datetime.fromisoformat(data['implemented_at']) if data['implemented_at'] else None
        data['expires_at'] = datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None
        return cls(**data)

class DecisionPersistenceService:
    """
    Service for managing decision lifecycle and persistence
    Provides auditability, traceability, and governance
    """
    
    def __init__(self):
        self.decisions_cache_key = "agentic_decisions"
        self.decision_history_key = "decision_history"
        self.decision_stats_key = "decision_statistics"
        
    async def propose_decision(self, 
                             title: str,
                             description: str,
                             category: DecisionCategory,
                             proposed_action: str,
                             reasoning: str,
                             confidence: float,
                             estimated_impact: str,
                             estimated_value: float,
                             risk_level: str,
                             proposed_by: str,
                             correlation_id: Optional[str] = None,
                             triggering_event: Optional[str] = None,
                             supporting_data: Optional[Dict[str, Any]] = None,
                             execution_plan: Optional[List[str]] = None,
                             expires_in_hours: int = 24) -> Decision:
        """Propose a new decision"""
        try:
            # Generate decision ID
            decision_id = f"decision_{int(time.time())}_{proposed_by}"
            
            # Create decision object
            decision = Decision(
                id=decision_id,
                title=title,
                description=description,
                category=category,
                proposed_action=proposed_action,
                reasoning=reasoning,
                confidence=confidence,
                estimated_impact=estimated_impact,
                estimated_value=estimated_value,
                risk_level=risk_level,
                status=DecisionStatus.PROPOSED,
                proposed_by=proposed_by,
                proposed_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
                correlation_id=correlation_id,
                triggering_event=triggering_event,
                supporting_data=supporting_data,
                execution_plan=execution_plan
            )
            
            # Store decision
            await self._store_decision(decision)
            
            # Publish decision proposed event
            await self._publish_decision_event(decision, "proposed")
            
            # Update statistics
            await self._update_statistics("proposed")
            
            logger.info(f"📋 Decision proposed: {decision.title} (ID: {decision.id})")
            return decision
            
        except Exception as e:
            logger.error(f"❌ Error proposing decision: {e}")
            raise
    
    async def approve_decision(self, decision_id: str, approved_by: str, 
                             approval_notes: Optional[str] = None) -> bool:
        """Approve a pending decision"""
        try:
            decision = await self.get_decision(decision_id)
            if not decision:
                logger.error(f"❌ Decision {decision_id} not found")
                return False
            
            if decision.status != DecisionStatus.PROPOSED:
                logger.error(f"❌ Decision {decision_id} is not in proposed state (current: {decision.status})")
                return False
            
            # Check if expired
            if decision.expires_at and datetime.utcnow() > decision.expires_at:
                decision.status = DecisionStatus.EXPIRED
                await self._store_decision(decision)
                logger.warning(f"⏰ Decision {decision_id} has expired")
                return False
            
            # Update decision
            decision.status = DecisionStatus.APPROVED
            decision.approved_by = approved_by
            decision.approved_at = datetime.utcnow()
            
            if approval_notes:
                if not decision.supporting_data:
                    decision.supporting_data = {}
                decision.supporting_data['approval_notes'] = approval_notes
            
            # Store updated decision
            await self._store_decision(decision)
            
            # Publish approval event
            await self._publish_decision_event(decision, "approved")
            
            # Update statistics
            await self._update_statistics("approved")
            
            logger.info(f"✅ Decision approved: {decision.title} by {approved_by}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error approving decision {decision_id}: {e}")
            return False
    
    async def reject_decision(self, decision_id: str, rejected_by: str, 
                            rejection_reason: str) -> bool:
        """Reject a pending decision"""
        try:
            decision = await self.get_decision(decision_id)
            if not decision:
                return False
            
            if decision.status != DecisionStatus.PROPOSED:
                logger.error(f"❌ Decision {decision_id} is not in proposed state")
                return False
            
            # Update decision
            decision.status = DecisionStatus.REJECTED
            decision.approved_by = rejected_by  # Store who rejected it
            decision.approved_at = datetime.utcnow()
            
            if not decision.supporting_data:
                decision.supporting_data = {}
            decision.supporting_data['rejection_reason'] = rejection_reason
            decision.supporting_data['rejected_by'] = rejected_by
            
            # Store updated decision
            await self._store_decision(decision)
            
            # Publish rejection event
            await self._publish_decision_event(decision, "rejected")
            
            # Update statistics
            await self._update_statistics("rejected")
            
            logger.info(f"❌ Decision rejected: {decision.title} by {rejected_by}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error rejecting decision {decision_id}: {e}")
            return False
    
    async def implement_decision(self, decision_id: str, 
                               execution_results: Dict[str, Any]) -> bool:
        """Mark decision as implemented with results"""
        try:
            decision = await self.get_decision(decision_id)
            if not decision:
                return False
            
            if decision.status != DecisionStatus.APPROVED:
                logger.error(f"❌ Decision {decision_id} is not approved")
                return False
            
            # Update decision
            decision.status = DecisionStatus.IMPLEMENTED
            decision.implemented_at = datetime.utcnow()
            decision.execution_results = execution_results
            
            # Store updated decision
            await self._store_decision(decision)
            
            # Publish implementation event
            await self._publish_decision_event(decision, "implemented")
            
            # Update statistics
            await self._update_statistics("implemented")
            
            logger.info(f"🚀 Decision implemented: {decision.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error implementing decision {decision_id}: {e}")
            return False
    
    async def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get decision by ID"""
        try:
            if not redis_cache_service.redis_client:
                return None
            
            decision_data = await redis_cache_service.get_json(f"decision:{decision_id}")
            if decision_data:
                return Decision.from_dict(decision_data)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting decision {decision_id}: {e}")
            return None
    
    async def get_decisions_by_status(self, status: DecisionStatus, 
                                    limit: int = 100) -> List[Decision]:
        """Get decisions by status"""
        try:
            if not redis_cache_service.redis_client:
                return []
            
            # Get decision IDs by status
            decision_ids = await redis_cache_service.redis_client.lrange(
                f"decisions_by_status:{status.value}", 0, limit - 1
            )
            
            decisions = []
            for decision_id in decision_ids:
                decision = await self.get_decision(decision_id)
                if decision:
                    decisions.append(decision)
            
            return decisions
            
        except Exception as e:
            logger.error(f"❌ Error getting decisions by status {status}: {e}")
            return []
    
    async def get_recent_decisions(self, limit: int = 50) -> List[Decision]:
        """Get recent decisions"""
        try:
            if not redis_cache_service.redis_client:
                return []
            
            # Get recent decision IDs
            decision_ids = await redis_cache_service.redis_client.lrange(
                "recent_decisions", 0, limit - 1
            )
            
            decisions = []
            for decision_id in decision_ids:
                decision = await self.get_decision(decision_id)
                if decision:
                    decisions.append(decision)
            
            return decisions
            
        except Exception as e:
            logger.error(f"❌ Error getting recent decisions: {e}")
            return []
    
    async def get_decision_statistics(self) -> Dict[str, Any]:
        """Get decision statistics"""
        try:
            if not redis_cache_service.redis_client:
                return {}
            
            stats = await redis_cache_service.get_json(self.decision_stats_key)
            if not stats:
                stats = {
                    'total_proposed': 0,
                    'total_approved': 0,
                    'total_rejected': 0,
                    'total_implemented': 0,
                    'approval_rate': 0.0,
                    'implementation_rate': 0.0,
                    'by_category': {},
                    'by_risk_level': {},
                    'average_confidence': 0.0,
                    'total_estimated_value': 0.0
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting decision statistics: {e}")
            return {}
    
    async def _store_decision(self, decision: Decision):
        """Store decision in cache"""
        try:
            if not redis_cache_service.redis_client:
                return
            
            # Store individual decision
            await redis_cache_service.set_json(
                f"decision:{decision.id}", 
                decision.to_dict(), 
                ttl=86400 * 30  # 30 days
            )
            
            # Add to recent decisions list
            await redis_cache_service.redis_client.lpush("recent_decisions", decision.id)
            await redis_cache_service.redis_client.ltrim("recent_decisions", 0, 999)  # Keep last 1000
            
            # Add to status-based lists
            await redis_cache_service.redis_client.lpush(
                f"decisions_by_status:{decision.status.value}", 
                decision.id
            )
            await redis_cache_service.redis_client.ltrim(
                f"decisions_by_status:{decision.status.value}", 0, 999
            )
            
        except Exception as e:
            logger.error(f"❌ Error storing decision: {e}")
    
    async def _publish_decision_event(self, decision: Decision, event_type: str):
        """Publish decision lifecycle event"""
        try:
            event_data = {
                'decision_id': decision.id,
                'title': decision.title,
                'category': decision.category.value,
                'status': decision.status.value,
                'confidence': decision.confidence,
                'estimated_value': decision.estimated_value,
                'risk_level': decision.risk_level,
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Map event types to EventType enum
            event_type_mapping = {
                'proposed': EventType.DECISION_PROPOSED,
                'approved': EventType.DECISION_APPROVED,
                'rejected': EventType.DECISION_REJECTED,
                'implemented': EventType.DECISION_EXECUTED
            }
            
            if event_type in event_type_mapping:
                await publish_decision_proposed(
                    source_agent="decision_persistence",
                    decision_data=event_data,
                    correlation_id=decision.correlation_id
                )
            
        except Exception as e:
            logger.error(f"❌ Error publishing decision event: {e}")
    
    async def _update_statistics(self, action: str):
        """Update decision statistics"""
        try:
            if not redis_cache_service.redis_client:
                return
            
            stats = await self.get_decision_statistics()
            
            # Update counters
            if action == "proposed":
                stats['total_proposed'] += 1
            elif action == "approved":
                stats['total_approved'] += 1
            elif action == "rejected":
                stats['total_rejected'] += 1
            elif action == "implemented":
                stats['total_implemented'] += 1
            
            # Calculate rates
            if stats['total_proposed'] > 0:
                stats['approval_rate'] = (stats['total_approved'] + stats['total_rejected']) / stats['total_proposed']
                stats['implementation_rate'] = stats['total_implemented'] / stats['total_proposed']
            
            # Store updated stats
            await redis_cache_service.set_json(self.decision_stats_key, stats, ttl=3600)
            
        except Exception as e:
            logger.error(f"❌ Error updating statistics: {e}")
    
    async def cleanup_expired_decisions(self):
        """Clean up expired decisions"""
        try:
            proposed_decisions = await self.get_decisions_by_status(DecisionStatus.PROPOSED)
            
            for decision in proposed_decisions:
                if decision.expires_at and datetime.utcnow() > decision.expires_at:
                    decision.status = DecisionStatus.EXPIRED
                    await self._store_decision(decision)
                    logger.info(f"⏰ Expired decision: {decision.title}")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired decisions: {e}")

# Global decision persistence service
decision_persistence = DecisionPersistenceService()