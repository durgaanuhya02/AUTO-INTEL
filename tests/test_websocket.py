"""WebSocket tests: protocol handling, real-time push from Redis pub/sub, and resilience."""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

import pytest

from tests.conftest import anomaly


def recv_until(ws, wanted, timeout=5.0):
    """Read frames until one of type `wanted` arrives; fail (rather than hang) on timeout."""
    deadline = time.time() + timeout
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise AssertionError(f"no {wanted!r} frame within {timeout}s")
            future = pool.submit(ws.receive_json)
            try:
                message = future.result(timeout=remaining)
            except FutureTimeout:
                raise AssertionError(f"no {wanted!r} frame within {timeout}s")
            if message.get("type") == wanted:
                return message
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def test_ping_gets_pong(app_client):
    with app_client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "ping"})
        assert recv_until(ws, "pong")["type"] == "pong"


@pytest.mark.parametrize("payload", ["not json", "[1, 2]", '"a string"', "42", "null"])
def test_malformed_input_gets_an_error_and_keeps_the_connection_alive(app_client, payload):
    """Regression: any valid-JSON non-object crashed the handler with AttributeError."""
    with app_client.websocket_connect("/ws") as ws:
        ws.send_text(payload)
        assert recv_until(ws, "error")["error"] in {"invalid_json", "invalid_message"}
        ws.send_json({"type": "ping"})
        assert recv_until(ws, "pong")


def test_unknown_message_type_is_reported(app_client):
    with app_client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "nope"})
        assert recv_until(ws, "error")["error"] == "unknown_message_type"


@pytest.mark.parametrize("bad", [
    {"metric_type": "not_a_metric", "current_value": 1},
    {"metric_type": "revenue", "current_value": "lots"},
    {"metric_type": "revenue", "current_value": True},
    {"metric_type": "revenue", "current_value": None},
])
def test_trigger_analysis_validates_input(app_client, bad):
    with app_client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "trigger_analysis", **bad})
        error = recv_until(ws, "error")["error"]
        assert error in {"invalid_metric_type", "invalid_current_value"}


def test_trigger_analysis_reaches_the_analyst(app_client, live_pipeline):
    from agents.agent_orchestrator import orchestrator

    with app_client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "trigger_analysis", "metric_type": "revenue", "current_value": 5150})
        reply = recv_until(ws, "analysis_triggered")
        assert reply["result"]["status"] == "triggered"

    async def analyst_saw_it():
        deadline = asyncio.get_event_loop().time() + 3
        analyst = orchestrator.agents["analyst"]
        while asyncio.get_event_loop().time() < deadline:
            if any(a["current_value"] == 5150 for a in analyst.pending_anomalies):
                return True
            await asyncio.sleep(0.02)
        return False

    assert app_client.portal.call(analyst_saw_it)


def test_new_alert_is_pushed_in_real_time(app_client, live_pipeline):
    """Observer alert -> Redis 'alerts' channel -> WebSocket 'new_alert' frame."""
    from agents.agent_orchestrator import orchestrator

    async def raise_alert():
        observer = orchestrator.agents["observer"]
        (violation,) = await observer._check_thresholds({"revenue": 733.0})
        await observer._create_alert(violation)

    with app_client.websocket_connect("/ws") as ws:
        app_client.portal.call(raise_alert)
        frame = recv_until(ws, "new_alert")
        assert frame["data"]["current_value"] == 733.0
        assert frame["data"]["severity"] == "high"
        assert frame["timestamp"]


def test_new_decision_is_pushed_in_real_time(app_client, live_pipeline):
    """Governance review -> Redis 'decisions' channel -> WebSocket 'new_decision' frame."""
    with app_client.websocket_connect("/ws") as ws:
        live_pipeline(anomaly("revenue", current=4711.0, expected=15000.0))
        frame = recv_until(ws, "new_decision")
        assert frame["data"]["action"] == "request_human_approval"
        assert frame["data"]["decision_id"] != "pending"


def test_agent_messages_are_forwarded_as_agent_updates(app_client, live_pipeline):
    with app_client.websocket_connect("/ws") as ws:
        live_pipeline(anomaly("revenue", current=4712.0, expected=15000.0))
        update = recv_until(ws, "agent_update")
        assert update["data"]["message_type"] in {"approval_requested", "insights_generated", "metrics_update"}


def test_every_connected_client_receives_the_broadcast(app_client, live_pipeline):
    from agents.agent_orchestrator import orchestrator

    async def raise_alert():
        observer = orchestrator.agents["observer"]
        (violation,) = await observer._check_thresholds({"revenue": 734.0})
        await observer._create_alert(violation)

    with app_client.websocket_connect("/ws") as a, app_client.websocket_connect("/ws") as b:
        app_client.portal.call(raise_alert)
        assert recv_until(a, "new_alert")["data"]["current_value"] == 734.0
        assert recv_until(b, "new_alert")["data"]["current_value"] == 734.0


def test_disconnected_clients_are_removed(app_client):
    import backend.main as main

    before = len(main.manager.active_connections)
    with app_client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "ping"})
        recv_until(ws, "pong")
        assert len(main.manager.active_connections) == before + 1
    deadline = time.time() + 2
    while time.time() < deadline and len(main.manager.active_connections) != before:
        time.sleep(0.02)
    assert len(main.manager.active_connections) == before


# ---- ConnectionManager / supervisor units (no app needed) ------------------------------

class FakeSocket:
    def __init__(self, behaviour="ok"):
        self.behaviour, self.sent = behaviour, []

    async def send_text(self, text):
        if self.behaviour == "hang":
            await asyncio.sleep(3600)
        if self.behaviour == "error":
            raise RuntimeError("connection closed")
        self.sent.append(text)


async def test_stalled_client_does_not_delay_or_block_other_clients(monkeypatch):
    import backend.main as main

    monkeypatch.setattr(main, "SEND_TIMEOUT_SECONDS", 0.1)
    manager = main.ConnectionManager()
    healthy, stalled, broken = FakeSocket(), FakeSocket("hang"), FakeSocket("error")
    manager.active_connections = [stalled, healthy, broken]

    started = time.monotonic()
    await manager.broadcast({"type": "x"})
    assert time.monotonic() - started < 1.0, "one slow client must not stall the broadcast"

    assert healthy.sent, "healthy client must still receive the message"
    assert manager.active_connections == [healthy], "stalled and broken clients must be dropped"


async def test_broadcast_with_no_clients_is_a_noop():
    import backend.main as main

    await main.ConnectionManager().broadcast({"type": "x"})


async def test_supervised_task_restarts_after_a_crash():
    import backend.main as main

    calls = []
    done = asyncio.Event()

    async def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("redis went away")
        done.set()

    main.spawn_supervised("flaky", flaky, restart_delay=0.01)
    await asyncio.wait_for(done.wait(), timeout=2)
    assert len(calls) == 3


async def test_supervised_task_is_tracked_and_cancellable():
    import backend.main as main

    async def forever():
        await asyncio.sleep(3600)

    task = main.spawn_supervised("forever", forever)
    assert task in main.background_tasks
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    await asyncio.sleep(0)
    assert task not in main.background_tasks
