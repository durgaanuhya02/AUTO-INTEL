import asyncio
import json
from datetime import datetime as real_datetime

import fakeredis
import numpy as np
import pytest
import pytest_asyncio

from agents.observer_agent import ObserverAgent
from agents.analyst_agent import AnalystAgent
from agents.simulation_agent import SimulationAgent
from agents.decision_agent import DecisionAgent
from agents.governance_agent import GovernanceAgent
from backend.models.schemas import AgentType


@pytest_asyncio.fixture
async def redis():
    client = fakeredis.aioredis.FakeRedis()
    yield client
    await client.aclose()


@pytest_asyncio.fixture
async def pipeline(redis):
    np.random.seed(7)
    agents = {
        "observer": ObserverAgent(redis, None),
        "analyst": AnalystAgent(redis, None, None),
        "simulation": SimulationAgent(redis),
        "decision": DecisionAgent(redis, None, None),
        "governance": GovernanceAgent(redis, None),
    }
    for agent in agents.values():
        await agent.initialize()
        await agent.start_listener()
    yield agents
    for agent in agents.values():
        await agent.stop()


@pytest.fixture
def business_hours(monkeypatch):
    """Freeze the governance clock to 12:00 UTC so the business-hours rule doesn't flap."""

    class FrozenDatetime(real_datetime):
        @classmethod
        def utcnow(cls):
            return real_datetime(2026, 1, 12, 12, 0, 0)

    monkeypatch.setattr("agents.governance_agent.datetime", FrozenDatetime)


@pytest.fixture
def after_hours(monkeypatch):
    class FrozenDatetime(real_datetime):
        @classmethod
        def utcnow(cls):
            return real_datetime(2026, 1, 12, 23, 0, 0)

    monkeypatch.setattr("agents.governance_agent.datetime", FrozenDatetime)


async def until(predicate, timeout=3.0):
    """Poll until predicate() is truthy; fail loudly instead of hanging."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition not met within timeout")


class BroadcastSpy:
    """Collects everything published on agent:broadcast."""

    def __init__(self, redis):
        self.redis = redis
        self.messages = []
        self._task = None

    async def start(self):
        ready = asyncio.Event()

        async def run():
            pubsub = self.redis.pubsub()
            await pubsub.subscribe("agent:broadcast")
            ready.set()
            async for m in pubsub.listen():
                if m["type"] == "message":
                    self.messages.append(json.loads(m["data"]))

        self._task = asyncio.create_task(run())
        await ready.wait()

    def types(self):
        return [m["message_type"] for m in self.messages]

    async def stop(self):
        if self._task:
            self._task.cancel()


@pytest_asyncio.fixture
async def spy(redis):
    s = BroadcastSpy(redis)
    await s.start()
    yield s
    await s.stop()


def anomaly(metric="revenue", current=6000.0, expected=15000.0, severity="high"):
    return {
        "metric_type": metric,
        "current_value": current,
        "expected_value": expected,
        "z_score": 3.4,
        "severity": severity,
        "description": f"{metric} anomaly detected: {current:.2f} (expected ~{expected:.2f})",
    }


# --------------------------------------------------------------------------------------
# Full-app fixtures (REST + WebSocket). Redis is fakeredis; the app runs its real lifespan.
# --------------------------------------------------------------------------------------
PIPELINE_STAGES = [
    ("analyst", "pending_anomalies"),
    ("simulation", "pending_analyses"),
    ("decision", "pending_scenarios"),
    ("governance", "pending_decisions"),
]


@pytest.fixture(scope="session")
def app_client():
    import backend.core.database as db
    from fastapi.testclient import TestClient

    server = fakeredis.FakeServer()
    db.redis_client = fakeredis.aioredis.FakeRedis(server=server)

    from backend.main import app
    import backend.main as main_module
    from agents.agent_orchestrator import orchestrator

    with TestClient(app) as client:
        client.fake_server = server

        async def quiesce():
            # The agents' own 30s loops would race the tests; tests drive stages explicitly.
            for task in list(main_module.background_tasks):
                if task.get_name() == "orchestrator":
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
            for agent in orchestrator.agents.values():
                await agent.stop()

        client.portal.call(quiesce)
        yield client


@pytest.fixture
def sync_redis(app_client):
    return fakeredis.FakeRedis(server=app_client.fake_server)


@pytest.fixture(autouse=False)
def clean_state(sync_redis):
    sync_redis.flushall()
    yield


async def _drive_live_pipeline(issue):
    from agents.agent_orchestrator import orchestrator

    agents = orchestrator.agents
    await agents["observer"].send_message(AgentType.ANALYST, "anomaly_detected", issue)
    for name, attr in PIPELINE_STAGES:
        await until(lambda: getattr(agents[name], attr), timeout=5)
        await agents[name].process()


@pytest.fixture
def live_pipeline(app_client, clean_state):
    """Start pub/sub listeners on the app's real agents; yields drive(issue)."""
    from agents.agent_orchestrator import orchestrator

    async def up():
        for agent in orchestrator.agents.values():
            await agent.start_listener()

    async def down():
        for agent in orchestrator.agents.values():
            await agent.stop()

    app_client.portal.call(up)
    yield lambda issue: app_client.portal.call(_drive_live_pipeline, issue)
    app_client.portal.call(down)
