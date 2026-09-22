"""Behaviours that matter for continuous 24/7 operation."""
import asyncio

from backend.models.schemas import AgentType
from tests.conftest import until, anomaly


async def test_message_arriving_mid_processing_is_not_dropped(pipeline):
    """Regression: process() used to iterate the inbox then .clear() it after awaiting,
    silently discarding anything delivered in between."""
    analyst = pipeline["analyst"]
    observer = pipeline["observer"]
    original = analyst._perform_root_cause_analysis
    processing = asyncio.Event()

    async def slow(a):
        processing.set()
        await asyncio.sleep(0.15)
        return await original(a)

    analyst._perform_root_cause_analysis = slow

    await observer.send_message(AgentType.ANALYST, "anomaly_detected", anomaly("revenue"))
    await until(lambda: analyst.pending_anomalies)
    task = asyncio.create_task(analyst.process())
    await processing.wait()

    await observer.send_message(AgentType.ANALYST, "anomaly_detected", anomaly("orders", 60, 150))
    await task

    await until(lambda: any(a["metric_type"] == "orders" for a in analyst.pending_anomalies))


async def test_malformed_message_does_not_kill_the_listener(pipeline, redis):
    analyst = pipeline["analyst"]
    await redis.publish("agent:analyst", b"{not json")
    await redis.publish("agent:analyst", b'{"unexpected": "shape"}')
    await pipeline["observer"].send_message(AgentType.ANALYST, "anomaly_detected", anomaly("revenue"))
    await until(lambda: analyst.pending_anomalies)


async def test_broadcast_reaches_every_agent(pipeline):
    received = {}
    for name, agent in pipeline.items():
        async def record(message, _name=name, _orig=agent.handle_message):
            received[_name] = message.message_type
            await _orig(message)
        agent.handle_message = record

    await pipeline["observer"].send_message(None, "ping", {})
    await until(lambda: len(received) == len(pipeline))
    assert set(received.values()) == {"ping"}


async def test_directed_message_reaches_only_its_target(pipeline):
    seen = []
    for name, agent in pipeline.items():
        async def record(message, _name=name):
            seen.append(_name)
        agent.handle_message = record

    await pipeline["observer"].send_message(AgentType.DECISION, "ping", {})
    await until(lambda: seen)
    await asyncio.sleep(0.1)
    assert seen == ["decision"]


async def test_start_initializes_once_and_loops_until_stopped(redis):
    from agents.simulation_agent import SimulationAgent

    agent = SimulationAgent(redis)
    agent.process_interval = 0.01
    inits, cycles = [], []
    original_init, original_process = agent.initialize, agent.process

    async def counting_init():
        inits.append(1)
        await original_init()

    async def counting_process():
        cycles.append(1)
        await original_process()

    agent.initialize, agent.process = counting_init, counting_process

    await agent.initialize()          # orchestrator initializes first...
    agent._initialized = True
    task = asyncio.create_task(agent.start())   # ...then starts the loop
    await until(lambda: len(cycles) >= 3)
    await agent.stop()
    await asyncio.wait_for(task, timeout=1)

    assert len(inits) == 1, "start() must not re-run initialize()"
    assert agent._listener_task is None


async def test_processing_error_does_not_stop_the_loop(redis):
    from agents.simulation_agent import SimulationAgent

    agent = SimulationAgent(redis)
    agent.process_interval = 0.01
    agent.error_backoff = 0.01
    calls = []

    async def flaky():
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("transient failure")

    agent.process = flaky
    task = asyncio.create_task(agent.start())
    await until(lambda: len(calls) >= 3)
    await agent.stop()
    await asyncio.wait_for(task, timeout=1)


async def test_a_bad_analysis_does_not_block_others(pipeline):
    """One malformed analysis must not stop the rest of the batch being simulated."""
    simulation, decision = pipeline["simulation"], pipeline["decision"]
    simulation.pending_analyses = [{"no_anomaly_key": True}, {"anomaly": anomaly("revenue")}]
    await simulation.process()
    # the good analysis (second) is still simulated even though the first was malformed
    await until(lambda: decision.pending_scenarios)
