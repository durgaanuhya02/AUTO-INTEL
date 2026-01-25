import asyncio
import logging
from typing import Dict, Any, List
import redis.asyncio as redis
import openai
from sqlalchemy.ext.asyncio import AsyncSession

from .observer_agent import ObserverAgent
from .analyst_agent import AnalystAgent
from .enhanced_simulation_agent import EnhancedSimulationAgent
from .decision_agent import DecisionAgent
from .governance_agent import GovernanceAgent
from backend.core.config import settings
from backend.core.database import get_db
from backend.services.ml_service import MLService
from backend.services.real_time_analytics_engine import RealTimeAnalyticsEngine

class AgentOrchestrator:
    def __init__(self):
        self.agents = {}
        self.redis_client = None
        self.openai_client = None
        self.db_session = None
        self.ml_service = None
        self.analytics_engine = None
        self.logger = logging.getLogger("orchestrator")
        self.running = False

    async def initialize(self):
        """Initialize all agents and connections"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(settings.redis_url)
            await self.redis_client.ping()
            self.logger.info("Redis connection established")

            # Initialize OpenAI client
            if settings.openai_api_key:
                self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
                self.logger.info("OpenAI client initialized")
            else:
                self.logger.warning("OpenAI API key not provided - AI features will be limited")

            # Get database session (simplified for demo)
            self.db_session = None  # Would be properly initialized in production

            # Initialize ML services
            await self._initialize_ml_services()

            # Initialize agents
            await self._initialize_agents()

            self.logger.info("Agent orchestrator initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize orchestrator: {e}")
            raise

    async def _initialize_ml_services(self):
        """Initialize ML services"""
        try:
            self.ml_service = MLService()
            await self.ml_service.initialize()

            self.analytics_engine = RealTimeAnalyticsEngine()
            await self.analytics_engine.initialize()

            self.logger.info("ML services initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize ML services: {e}")
            # Continue without ML - agents will use fallbacks
    
    async def _initialize_agents(self):
        """Initialize all AI agents"""
        
        # Observer Agent
        self.agents["observer"] = ObserverAgent(
            redis_client=self.redis_client,
            db_session=self.db_session
        )
        
        # Analyst Agent
        self.agents["analyst"] = AnalystAgent(
            redis_client=self.redis_client,
            db_session=self.db_session,
            openai_client=self.openai_client
        )
        
        # Simulation Agent
        self.agents["simulation"] = EnhancedSimulationAgent(
            ml_service=self.ml_service,
            analytics_engine=self.analytics_engine
        )
        
        # Decision Agent
        self.agents["decision"] = DecisionAgent(
            redis_client=self.redis_client,
            db_session=self.db_session,
            openai_client=self.openai_client
        )
        
        # Governance Agent
        self.agents["governance"] = GovernanceAgent(
            redis_client=self.redis_client,
            db_session=self.db_session
        )
        
        # Initialize each agent
        for agent_name, agent in self.agents.items():
            try:
                await agent.initialize()
                self.logger.info(f"{agent_name} agent initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize {agent_name} agent: {e}")
    
    async def start(self):
        """Start all agents"""
        if self.running:
            self.logger.warning("Orchestrator is already running")
            return
        
        self.running = True
        self.logger.info("Starting agent orchestrator...")
        
        # Start all agents concurrently
        agent_tasks = []
        for agent_name, agent in self.agents.items():
            task = asyncio.create_task(agent.start())
            task.set_name(f"agent_{agent_name}")
            agent_tasks.append(task)
        
        # Start monitoring task
        monitor_task = asyncio.create_task(self._monitor_agents())
        monitor_task.set_name("agent_monitor")
        
        try:
            # Wait for all tasks (they should run indefinitely)
            await asyncio.gather(*agent_tasks, monitor_task)
        except Exception as e:
            self.logger.error(f"Error in agent orchestrator: {e}")
        finally:
            self.running = False
    
    async def stop(self):
        """Stop all agents gracefully"""
        self.logger.info("Stopping agent orchestrator...")
        self.running = False
        
        # In a production system, we would properly stop all agent tasks
        # For now, we'll just mark as stopped
        
        if self.redis_client:
            await self.redis_client.close()
        
        self.logger.info("Agent orchestrator stopped")
    
    async def _monitor_agents(self):
        """Monitor agent health and performance"""
        while self.running:
            try:
                # Check agent statuses
                agent_statuses = {}
                for agent_name in self.agents.keys():
                    status_data = await self.redis_client.get(f"agent_status:{agent_name}")
                    if status_data:
                        agent_statuses[agent_name] = status_data.decode()
                    else:
                        agent_statuses[agent_name] = "unknown"
                
                # Store aggregated status
                await self.redis_client.set(
                    "orchestrator_status",
                    f"running:{len(agent_statuses)} agents",
                    ex=60
                )
                
                # Log status periodically
                active_agents = sum(1 for status in agent_statuses.values() if "active" in status.lower())
                self.logger.info(f"Agent status: {active_agents}/{len(self.agents)} active")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in agent monitoring: {e}")
                await asyncio.sleep(30)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            status = {
                "orchestrator_running": self.running,
                "agents": {},
                "redis_connected": False,
                "openai_available": self.openai_client is not None
            }
            
            # Check Redis connection
            try:
                await self.redis_client.ping()
                status["redis_connected"] = True
            except:
                pass
            
            # Get agent statuses
            for agent_name in self.agents.keys():
                try:
                    status_data = await self.redis_client.get(f"agent_status:{agent_name}")
                    if status_data:
                        import json
                        agent_status = json.loads(status_data)
                        status["agents"][agent_name] = agent_status
                    else:
                        status["agents"][agent_name] = {"status": "unknown"}
                except Exception as e:
                    status["agents"][agent_name] = {"status": "error", "error": str(e)}
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
    
    async def trigger_manual_analysis(self, metric_type: str, current_value: float) -> Dict[str, Any]:
        """Manually trigger analysis for testing purposes"""
        try:
            # Create a simulated anomaly
            anomaly = {
                "metric_type": metric_type,
                "current_value": current_value,
                "expected_value": current_value * 0.8,
                "severity": "medium",
                "description": f"Manual trigger for {metric_type}"
            }
            
            # Send to analyst agent
            if "analyst" in self.agents:
                await self.agents["analyst"].send_message(
                    None,
                    "anomaly_detected",
                    anomaly
                )
                
                return {"status": "triggered", "anomaly": anomaly}
            else:
                return {"status": "error", "message": "Analyst agent not available"}
                
        except Exception as e:
            self.logger.error(f"Error triggering manual analysis: {e}")
            return {"status": "error", "message": str(e)}

# Global orchestrator instance
orchestrator = AgentOrchestrator()