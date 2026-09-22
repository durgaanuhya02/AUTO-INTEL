"""Run the full agent backend locally WITHOUT Docker, Redis or PostgreSQL.

Redis is replaced by fakeredis (in-process, same pub/sub semantics). Use this to try the
dashboard end to end on a laptop; use docker-compose for anything resembling production.

    pip install fakeredis
    python -m backend.dev_server            # http://localhost:8000
    AGENT_UPDATE_INTERVAL=3 python -m backend.dev_server   # faster agent cycles for demos
"""
import fakeredis
import uvicorn

import backend.core.database as database

database.redis_client = fakeredis.aioredis.FakeRedis()

from backend.main import app  # noqa: E402  (must import after Redis is patched)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
