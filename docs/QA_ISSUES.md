# AutoIntel QA log: issues found and resolved

Each entry is written so it can be pasted into a GitHub Issue. All items marked **Fixed** have a regression test.

Run the suites:

```bash
pip install -r backend/requirements-dev.txt
python -m pytest                      # 78 backend tests (agents, pub/sub, REST, WebSocket)
cd frontend && npm test               # 72 tests (reconnecting WebSocket client, adapters)
cd frontend && npm run typecheck && npm run build
```

Try it end to end without Docker: `python -m backend.dev_server` (fakeredis), `cd backend && python production_server.py`, `cd frontend && npm run dev`, then open the **Live Agent Pipeline** tab.

## Pipeline (Observer → Analyst → Simulation → Decision → Governance)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| P1 | Blocker | Backend imported `backend.core.*` but the files lived in `backend/docs/core/`; no `__init__.py` files, so `backend.main` could not be imported | Fixed |
| P2 | Blocker | Stage 3 did not exist: `simulation_agent.py` was empty, and all five `enhanced_*` agents call `super().__init__("name")` (signature that no longer exists) and instantiate at import time. Nothing ever sent `scenarios_ready` | Fixed: new `SimulationAgent` |
| P3 | High | Analyst called async `_calculate_analysis_confidence()` without `await`, putting a coroutine in the message | Fixed |
| P4 | High | Governance used `timedelta` without importing it; `NameError` on every human-approval request | Fixed |
| P5 | High | Analyst/Decision/Governance iterated their inbox then `.clear()`ed it after `await`s; messages arriving mid-cycle were silently dropped | Fixed |
| P6 | High | Restricted-scenario policy (`price_optimization`) compared against names like "Price Optimization"; never matched, so risky scenarios could auto-approve | Fixed |
| P7 | High | Decisions had no ID, so human approvals could not be tied to a decision | Fixed |
| P8 | High | Financial impact used the absolute metric level as the benefit (105 orders became $105,000) | Fixed (improvement × unit value − cost; unit values in `METRIC_UNIT_VALUE_USD` are **assumptions to review**) |
| P9 | High | `roi_threshold` was never applied; money-losing scenarios could be recommended | Fixed; if nothing pays off the decision is flagged for human review |
| P10 | High | Observer fed its own previous output back as the next baseline, compounding the daily multiplier: metrics decayed to 0 in minutes (205 alerts in ~5 min in a live run) | Fixed |
| P11 | Medium | A persistent violation re-alerted (and spawned a new decision) every cycle | Fixed: per-metric cooldown (900 s) |
| P12 | Medium | `BaseAgent.start()` re-ran `initialize()`; no clean stop; unmatched interval (`AGENT_UPDATE_INTERVAL` was ignored) | Fixed |
| P13 | Medium | One malformed message aborted the whole batch in Analyst/Simulation | Fixed |
| P14 | Medium | Manual trigger compared against `current × 0.8`, so a revenue drop was "expected" to be lower | Fixed (uses metric baseline) |
| P15 | Medium | Human-approved decisions were never executed; approvals did not leave the queue, could be applied twice, and the audit log kept showing "pending" | Fixed |

## Backend (FastAPI REST + WebSocket, Redis pub/sub)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| B1 | Blocker | `app.add_middleware()` inside a startup handler raises `RuntimeError` on Starlette ≥ 0.24, including the pinned version; the app could never start | Fixed |
| B2 | Blocker | SQLAlchemy model attribute named `metadata` is reserved; import failed | Fixed (`meta_data`, same column) |
| B3 | Critical | `eval()` on Redis data in `/alerts`, `/dashboard` and the WebSocket forwarder (code execution). Alerts were also written as Python `repr`, so `eval` always failed and **no alert ever reached the dashboard** | Fixed (JSON end to end) |
| B4 | High | Real-time alerts/decisions never reached WebSocket clients: the forwarder listened on Redis channels `alerts`/`decisions` that nothing published to | Fixed |
| B5 | High | Rate limiter keyed entries by whole-second timestamp; a burst collapsed to one entry and the limit was unreachable; check-then-add was not atomic | Fixed (atomic sliding window) |
| B6 | High | Limiter raised `HTTPException` inside middleware, which surfaces as 500 instead of 429 | Fixed |
| B7 | High | `/health` returned 200 with `"unhealthy"` body; `curl -f` / ALB checks in the ECS and compose files could never fail | Fixed (503 for unhealthy/critical) |
| B8 | High | `/approve-decision` published `from_agent: "human"`, not a valid `AgentType`; governance rejected every approval | Fixed |
| B9 | Medium | Approve endpoint accepted unknown/already-resolved IDs and turned its own 404 into a 500 | Fixed |
| B10 | Medium | WebSocket handler crashed on valid JSON that was not an object; no input validation; no heartbeat | Fixed |
| B11 | Medium | One stalled client blocked broadcasts to everyone | Fixed (concurrent, 5 s timeout) |
| B12 | Medium | Background tasks were unreferenced `create_task`s that died permanently on the first exception (e.g. a Redis blip) | Fixed (supervised restart) |
| B13 | Medium | Dashboard alert contract mismatch (`id`, `created_at` missing) silently emptied the alerts list; decision IDs used salted `hash()` | Fixed |

## Dashboard (Next.js + TypeScript)

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| F1 | Critical | No component used WebSockets; `useWebSocket` and `wsClient` were dead code. The page read only the analytics server (:8001), which has no agents | Fixed: shared reconnecting client + new **Live Agent Pipeline** tab |
| F2 | Critical | `AlertPanel`/`DecisionPanel`/`AgentStatus` substituted hardcoded fake data (e.g. "Revenue Anomaly Detected, 94.5%") on any error | Fixed: last real data + visible error banner |
| F3 | High | Those components were not rendered anywhere | Fixed |
| F4 | High | Naive UTC timestamps parsed as local time ("last activity 5h ago") | Fixed |
| F5 | High | Old hook gave up after 5 reconnects, re-created its callback on every retry, and reconnected after intentional close | Fixed: unlimited capped backoff + jitter, heartbeat, stale-connection detection |
| F6 | High | Approve / Reject buttons had no handlers | Fixed |
| F7 | Medium | Agent stats the backend does not report (performance, uptime, tasks, alert confidence) are shown as "—" instead of invented numbers | Fixed |
| F8 | Low | `EnterpriseAnalytics.tsx` and `ProductionDashboard.tsx` are truncated mid-expression and unimported; excluded from `tsc` | **Open**: restore from source control or delete |

## Open items (not fixed here)

- **O1**: The dashboard shell shows "Connection Error" for the whole UI, including the Live tab, whenever the analytics server (:8001) is down. The live tab should not depend on it.
- **O2**: The old "AI Agents" tab shows three hardcoded agents with an always-green pulsing dot.
- **O3**: `approval_queue` is unbounded and never expires (`max_pending_approvals` / `approval_timeout_hours` are defined but unused).
- **O4**: `/health` returns 503 when PostgreSQL is down even though the agent pipeline only needs Redis. Decide whether Postgres alone should pull an instance out of the load balancer.
- **O5**: `production_server.py` prints emoji at startup and crashes on Windows consoles (`cp1252`); run with `PYTHONUTF8=1`.
- **O6**: `start_no_docker.bat` does not work (no Redis, wrong import path). Use `python -m backend.dev_server`.
- **O7**: Not verified here: real Redis/PostgreSQL (Docker daemon was not running), the AWS deployment, and continuous 24/7 operation. Tests use fakeredis, which implements the same pub/sub protocol.
- **O8**: A GitHub token is embedded in the parent repo's `origin` URL. Rotate it and reset the remote.
