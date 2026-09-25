"""Replay the Olist days through the five-agent pipeline and measure it.

The agents are the production classes, talking over Redis pub/sub (fakeredis, in-process, so no
network time is included). One cycle = one Olist day. For every day the Observer processes the metrics;
when it raises an anomaly the remaining stages are driven in order (Analyst -> Simulation -> Decision ->
Governance), each waiting for the previous stage's message to arrive over pub/sub.

Reported: per-stage wall-clock latency, number of anomalies per metric, chosen actions, approval
outcomes. The OpenAI client is disabled, so the Analyst uses its rule-based fallback. The governance
clock is frozen at 12:00 so the business-hours rule does not depend on when the script is run.

Run:  python evaluation/run_pipeline.py
"""
from __future__ import annotations

import asyncio
import collections
import time
from datetime import datetime as real_datetime

import fakeredis
import numpy as np
import pandas as pd

from common import RESULTS, hardware, save_json
import agents.governance_agent as governance_module
from agents.observer_agent import REPLAY_START, ObserverAgent
from agents.analyst_agent import AnalystAgent
from agents.simulation_agent import SimulationAgent
from agents.decision_agent import DecisionAgent
from agents.governance_agent import GovernanceAgent
from backend.services.olist_metrics import daily_metrics, load_olist, customer_rfm

STAGES = [("analyst", "pending_anomalies"), ("simulation", "pending_analyses"),
          ("decision", "pending_scenarios"), ("governance", "pending_decisions")]


class NoonDatetime(real_datetime):
    @classmethod
    def utcnow(cls):
        return real_datetime(2018, 1, 15, 12, 0, 0)


async def wait_for(predicate, timeout=5.0):
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.0005)
    return False


async def replay():
    governance_module.datetime = NoonDatetime
    redis = fakeredis.aioredis.FakeRedis()
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

    observer = agents["observer"]
    clock = [0.0]
    observer._now = lambda: clock[0]   # one cycle = one day, so the 15-min cooldown never spans days
    feed = daily_metrics()
    n_days = len(feed) - REPLAY_START

    timings = collections.defaultdict(list)
    records = []
    for i in range(n_days):
        day = feed.index[REPLAY_START + i]
        t0 = time.perf_counter()
        await observer.process()
        timings["observer"].append(time.perf_counter() - t0)
        clock[0] += 86400

        if not await wait_for(lambda: agents["analyst"].pending_anomalies, timeout=0.05):
            continue
        anomaly = agents["analyst"].pending_anomalies[0]
        t_chain = time.perf_counter()
        ok = True
        for name, attr in STAGES:
            if not await wait_for(lambda: getattr(agents[name], attr)):
                ok = False
                break
            t = time.perf_counter()
            await agents[name].process()
            timings[name].append(time.perf_counter() - t)
        timings["chain_after_observer"].append(time.perf_counter() - t_chain)
        if not ok:
            records.append({"date": day, "metric": anomaly["metric_type"], "completed": False})
            continue
        entry = agents["governance"].audit_log[-1]
        records.append({
            "date": day, "metric": anomaly["metric_type"], "severity": str(anomaly["severity"]),
            "source": "threshold" if "violation_type" in anomaly else "detector",
            "current": anomaly["current_value"],
            "reference": anomaly.get("expected_value", anomaly.get("threshold_value")),
            "scenario": entry["recommended_scenario"], "score": entry["confidence_score"],
            "financial_impact": entry["financial_impact"], "action": entry["action"],
            "violations": [v["rule"] for v in entry["policy_result"]["violations"]],
            "completed": True,
        })

    for agent in agents.values():
        await agent.stop()
    await redis.aclose()
    return n_days, timings, pd.DataFrame(records)


def component_latency() -> dict:
    """Cold-start costs of the data layer (measured once each)."""
    load_olist.cache_clear()
    daily_metrics.cache_clear()
    customer_rfm.cache_clear()
    out = {}
    t = time.perf_counter(); load_olist(); out["load_csvs_s"] = time.perf_counter() - t
    t = time.perf_counter(); daily_metrics(); out["daily_metrics_s"] = time.perf_counter() - t
    t = time.perf_counter(); customer_rfm(); out["rfm_s"] = time.perf_counter() - t
    return out


def stats_ms(values):
    a = np.asarray(values) * 1000
    return {"mean_ms": float(a.mean()), "std_ms": float(a.std()), "p50_ms": float(np.median(a)),
            "p95_ms": float(np.percentile(a, 95)), "n": int(len(a))}


def main():
    cold = component_latency()
    n_days, timings, records = asyncio.run(replay())
    records.to_csv(RESULTS / "pipeline_decisions.csv", index=False)
    done = records[records["completed"]]

    summary = {
        "hardware": hardware(),
        "days_replayed": n_days,
        "anomalies": int(len(records)),
        "chains_completed": int(len(done)),
        "anomalies_by_metric": records["metric"].value_counts().to_dict(),
        "anomalies_by_source": done["source"].value_counts().to_dict(),
        "severity": done["severity"].value_counts().to_dict(),
        "scenarios": done["scenario"].value_counts().to_dict(),
        "actions": done["action"].value_counts().to_dict(),
        "violation_counts": pd.Series([v for vs in done["violations"] for v in vs])
                              .value_counts().to_dict(),
        "latency": {name: stats_ms(v) for name, v in timings.items()},
        "cold_start": cold,
    }
    save_json("pipeline.json", summary)
    for k, v in summary.items():
        print(k, ":", v)


if __name__ == "__main__":
    main()
