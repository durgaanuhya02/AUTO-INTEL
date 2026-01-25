from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime
import json
import redis.asyncio as redis
from backend.models.schemas import AgentType, AgentMessage, AgentStatus

class BaseAgent(ABC):
    def __init__(self, agent_type: AgentType, redis_client: redis.Redis):
        self.agent_type = agent_type
        self.redis_client = redis_client
        self.logger = logging.getLogger(f"agent.{agent_type.value}")
        self.status = "idle"
        self.current_task = None
        self.last_activity = datetime.utcnow()
        self.metrics = {}
        
    async def start(self):
        """Start the agent's main loop"""
        self.logger.info(f"{self.agent_type.value} agent starting...")
        await self.initialize()
        
        # Start message listener
        asyncio.create_task(self._message_listener())
        
        # Start main processing loop
        while True:
            try:
                await self.process()
                await asyncio.sleep(30)  # Process every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in {self.agent_type.value} agent: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    @abstractmethod
    async def initialize(self):
        """Initialize agent-specific resources"""
        pass
    
    @abstractmethod
    async def process(self):
        """Main processing logic for the agent"""
        pass
    
    async def send_message(self, to_agent: Optional[AgentType], message_type: str, content: Dict[str, Any]):
        """Send message to another agent or broadcast"""
        message = AgentMessage(
            from_agent=self.agent_type,
            to_agent=to_agent,
            message_type=message_type,
            content=content
        )
        
        channel = f"agent:{to_agent.value}" if to_agent else "agent:broadcast"
        await self.redis_client.publish(channel, message.model_dump_json())
        
        self.logger.info(f"Sent {message_type} to {to_agent or 'broadcast'}")
    
    async def _message_listener(self):
        """Listen for messages from other agents"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(f"agent:{self.agent_type.value}", "agent:broadcast")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    agent_message = AgentMessage.model_validate_json(message["data"])
                    await self.handle_message(agent_message)
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages from other agents"""
        self.logger.info(f"Received {message.message_type} from {message.from_agent}")
        # Override in subclasses for specific message handling
    
    async def update_status(self, status: str, task: Optional[str] = None, metrics: Optional[Dict[str, Any]] = None):
        """Update agent status in Redis"""
        self.status = status
        self.current_task = task
        self.last_activity = datetime.utcnow()
        if metrics:
            self.metrics.update(metrics)
        
        status_data = AgentStatus(
            agent_type=self.agent_type,
            status=self.status,
            last_activity=self.last_activity,
            current_task=self.current_task,
            metrics=self.metrics
        )
        
        await self.redis_client.set(
            f"agent_status:{self.agent_type.value}",
            status_data.model_dump_json(),
            ex=300  # Expire after 5 minutes
        )
    
    async def get_agent_status(self, agent_type: AgentType) -> Optional[AgentStatus]:
        """Get status of another agent"""
        status_data = await self.redis_client.get(f"agent_status:{agent_type.value}")
        if status_data:
            return AgentStatus.model_validate_json(status_data)
        return None
    
    async def store_data(self, key: str, data: Any, expire: int = 3600):
        """Store data in Redis with expiration"""
        await self.redis_client.set(
            f"agent_data:{self.agent_type.value}:{key}",
            json.dumps(data, default=str),
            ex=expire
        )
    
    async def get_data(self, key: str) -> Optional[Any]:
        """Retrieve data from Redis"""
        data = await self.redis_client.get(f"agent_data:{self.agent_type.value}:{key}")
        if data:
            return json.loads(data)
        return None