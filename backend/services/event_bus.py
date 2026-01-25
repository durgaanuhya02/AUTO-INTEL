"""
Enhanced Event Bus Service using Redis Streams for real-time event-driven architecture.
Supports autonomous agent communication and decision workflows.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Standardized event types for the agentic system"""
    METRIC_UPDATE = "metric_update"
    AGENT_STATUS = "agent_status"
    DECISION_PROPOSED = "decision_proposed"
    DECISION_APPROVED = "decision_approved"
    DECISION_REJECTED = "decision_rejected"
    DECISION_EXECUTED = "decision_executed"
    APPROVAL_REQUESTED = "approval_requested"
    ANOMALY_DETECTED = "anomaly_detected"
    INSIGHT_GENERATED = "insight_generated"
    ACTION_EXECUTED = "action_executed"
    SYSTEM_ALERT = "system_alert"

@dataclass
class Event:
    """Standardized event structure"""
    event_type: EventType
    source_agent: str
    timestamp: float
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=critical

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type.value,
            'source_agent': self.source_agent,
            'timestamp': self.timestamp,
            'data': self.data,
            'correlation_id': self.correlation_id,
            'priority': self.priority
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        return cls(
            event_type=EventType(data['event_type']),
            source_agent=data['source_agent'],
            timestamp=data['timestamp'],
            data=data['data'],
            correlation_id=data.get('correlation_id'),
            priority=data.get('priority', 1)
        )

class EventBus:
    """
    Redis Streams-based event bus for autonomous agent communication.
    Enables real-time, event-driven decision intelligence.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.consumer_groups: Dict[str, str] = {}
        self.running = False
        
    async def initialize(self) -> bool:
        """Initialize Redis connection and create consumer groups"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory fallback")
            return False
            
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            
            # Create consumer groups for each event type
            for event_type in EventType:
                stream_name = f"events:{event_type.value}"
                group_name = f"agents_{event_type.value}"
                
                try:
                    await self.redis_client.xgroup_create(
                        stream_name, group_name, id='0', mkstream=True
                    )
                    self.consumer_groups[event_type.value] = group_name
                    logger.info(f"Created consumer group {group_name} for {stream_name}")
                except redis.ResponseError as e:
                    if "BUSYGROUP" in str(e):
                        # Group already exists
                        self.consumer_groups[event_type.value] = group_name
                    else:
                        logger.error(f"Error creating consumer group: {e}")
                        
            logger.info("Event bus initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize event bus: {e}")
            return False
    
    async def publish(self, event: Event) -> bool:
        """Publish event to Redis stream"""
        if not self.redis_client:
            logger.warning("Redis not available, event not published")
            return False
            
        try:
            stream_name = f"events:{event.event_type.value}"
            event_data = event.to_dict()
            
            # Add to stream
            message_id = await self.redis_client.xadd(
                stream_name, 
                event_data,
                maxlen=10000  # Keep last 10k events per stream
            )
            
            logger.debug(f"Published event {event.event_type.value} with ID {message_id}")
            
            # Also publish to pub/sub for real-time notifications
            await self.redis_client.publish(
                f"realtime:{event.event_type.value}",
                json.dumps(event_data)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False
    
    async def subscribe(self, event_types: List[EventType], consumer_name: str, 
                       callback: Callable[[Event], None]) -> None:
        """Subscribe to specific event types"""
        if not self.redis_client:
            logger.warning("Redis not available, cannot subscribe")
            return
            
        try:
            streams = {}
            for event_type in event_types:
                stream_name = f"events:{event_type.value}"
                group_name = self.consumer_groups.get(event_type.value)
                if group_name:
                    streams[stream_name] = '>'
            
            if not streams:
                logger.warning("No valid streams to subscribe to")
                return
                
            logger.info(f"Consumer {consumer_name} subscribing to {list(streams.keys())}")
            
            while self.running:
                try:
                    # Read from multiple streams
                    messages = await self.redis_client.xreadgroup(
                        groupname=list(self.consumer_groups.values())[0],  # Use first group
                        consumername=consumer_name,
                        streams=streams,
                        count=10,
                        block=1000  # Block for 1 second
                    )
                    
                    for stream_name, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            try:
                                event = Event.from_dict(fields)
                                await asyncio.create_task(self._handle_event(callback, event))
                                
                                # Acknowledge message
                                group_name = stream_name.split(':')[1]
                                if group_name in self.consumer_groups.values():
                                    await self.redis_client.xack(
                                        stream_name, 
                                        list(self.consumer_groups.values())[0],
                                        message_id
                                    )
                                    
                            except Exception as e:
                                logger.error(f"Error processing message {message_id}: {e}")
                                
                except redis.ResponseError as e:
                    if "NOGROUP" not in str(e):
                        logger.error(f"Error reading from streams: {e}")
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Unexpected error in subscription: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")
    
    async def _handle_event(self, callback: Callable, event: Event) -> None:
        """Handle event with callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            logger.error(f"Error in event callback: {e}")
    
    async def get_recent_events(self, event_type: EventType, count: int = 100) -> List[Event]:
        """Get recent events of a specific type"""
        if not self.redis_client:
            return []
            
        try:
            stream_name = f"events:{event_type.value}"
            messages = await self.redis_client.xrevrange(stream_name, count=count)
            
            events = []
            for message_id, fields in messages:
                try:
                    event = Event.from_dict(fields)
                    events.append(event)
                except Exception as e:
                    logger.error(f"Error parsing event {message_id}: {e}")
                    
            return events
            
        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            return []
    
    async def start(self) -> None:
        """Start the event bus"""
        self.running = True
        logger.info("Event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus"""
        self.running = False
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Event bus stopped")

# Global event bus instance
event_bus = EventBus()

# Convenience functions for common event types
async def publish_metric_update(source_agent: str, metrics: Dict[str, Any], 
                               correlation_id: Optional[str] = None) -> bool:
    """Publish a metric update event"""
    event = Event(
        event_type=EventType.METRIC_UPDATE,
        source_agent=source_agent,
        timestamp=time.time(),
        data={"metrics": metrics},
        correlation_id=correlation_id,
        priority=2
    )
    return await event_bus.publish(event)

async def publish_anomaly_detected(source_agent: str, anomaly_data: Dict[str, Any],
                                  correlation_id: Optional[str] = None) -> bool:
    """Publish an anomaly detection event"""
    event = Event(
        event_type=EventType.ANOMALY_DETECTED,
        source_agent=source_agent,
        timestamp=time.time(),
        data=anomaly_data,
        correlation_id=correlation_id,
        priority=4  # Critical
    )
    return await event_bus.publish(event)

async def publish_decision_proposed(source_agent: str, decision_data: Dict[str, Any],
                                   correlation_id: Optional[str] = None) -> bool:
    """Publish a decision proposal event"""
    event = Event(
        event_type=EventType.DECISION_PROPOSED,
        source_agent=source_agent,
        timestamp=time.time(),
        data=decision_data,
        correlation_id=correlation_id,
        priority=3  # High
    )
    return await event_bus.publish(event)

async def publish_agent_status(agent_name: str, status_data: Dict[str, Any],
                              correlation_id: Optional[str] = None) -> bool:
    """Publish agent status update"""
    event = Event(
        event_type=EventType.AGENT_STATUS,
        source_agent=agent_name,
        timestamp=time.time(),
        data=status_data,
        correlation_id=correlation_id,
        priority=1
    )
    return await event_bus.publish(event)