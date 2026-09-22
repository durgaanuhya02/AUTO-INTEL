# AUTO-INTEL Cloud Architecture

## Platform Decision: AWS

### Why AWS over GCP or Azure

| Factor | AWS | GCP | Azure |
|---|---|---|---|
| ECS Fargate | ✅ Best fit for persistent asyncio agent loops | Cloud Run scales to zero (breaks Redis pub/sub) | Container Apps — good but less mature |
| Managed Airflow | MWAA — battle-tested, native S3/IAM | Cloud Composer — good but $$$$ | Data Factory — different paradigm entirely |
| MLflow hosting | EC2/ECS + RDS/S3 — clean native fit | Vertex AI (different SDK, vendor lock-in) | Azure ML (own experiment format) |
| ElastiCache Redis | ✅ Cluster mode, Multi-AZ, native VPC | Memorystore — works but fewer options | Azure Cache — works |
| Overall ecosystem | Most widely documented for this stack | Best for pure ML/data workloads | Best if already Microsoft shop |

**Decision: AWS** — ECS Fargate for agents, MWAA for Airflow, RDS PostgreSQL, ElastiCache Redis, S3 for models/data, MLflow on ECS backed by RDS+S3.

---

## Full Architecture Diagram

```
Internet
    │
Route 53 (DNS)
    │
CloudFront (CDN + WAF)
    │
Application Load Balancer
    ├── /api/*  → ECS Fargate: FastAPI Backend (2 tasks, auto-scale 2-10)
    ├── /*      → ECS Fargate: Next.js Frontend (1 task)
    ├── /mlflow → ECS Fargate: MLflow Tracking Server (1 task)
    └── /ws     → ECS Fargate: FastAPI Backend (WebSocket upgrade)

ECS Fargate Cluster (auto-intel-cluster)
    ├── backend-service         (FastAPI + All 5 Agents + asyncio loops)
    ├── frontend-service        (Next.js)
    └── mlflow-service          (MLflow Tracking Server)

Data Layer
    ├── RDS PostgreSQL 15       (Multi-AZ, db.r6g.large)
    │   ├── auto_intel DB       (main app: metrics, alerts, decisions)
    │   └── mlflow DB           (MLflow experiment metadata)
    ├── ElastiCache Redis 7     (cluster mode, cache.r6g.large x 3 nodes)
    │   └── Redis pub/sub channels for all agent messaging
    └── S3 Buckets
        ├── auto-intel-models   (trained .pkl / XGBoost model files)
        ├── auto-intel-data     (Olist CSV files, training datasets)
        ├── auto-intel-mlflow   (MLflow artifact store)
        └── auto-intel-airflow  (MWAA DAG files, logs)

Orchestration
    └── MWAA (Managed Airflow)
        ├── DAG: ml_retraining_weekly
        ├── DAG: daily_bi_report
        ├── DAG: data_quality_checks
        ├── DAG: governance_audit_export
        └── DAG: model_performance_monitor

Observability
    ├── CloudWatch Logs         (all container logs)
    ├── CloudWatch Metrics      (ECS CPU/memory, RDS, ElastiCache)
    ├── CloudWatch Alarms       (SNS → email/Slack on threshold breach)
    └── X-Ray                   (distributed tracing for FastAPI)

Security
    ├── VPC (private subnets for RDS, ElastiCache, ECS)
    ├── Security Groups         (least-privilege ingress/egress)
    ├── IAM Roles               (ECS task roles — no hardcoded keys)
    ├── Secrets Manager         (OPENAI_API_KEY, DB passwords, Redis URL)
    └── WAF                     (CloudFront — rate limiting, OWASP rules)
```

---

## Port Map

| Service | Internal Port | External |
|---|---|---|
| FastAPI Backend | 8000 | ALB :443 /api/* |
| Next.js Frontend | 3000 | ALB :443 /* |
| MLflow Server | 5000 | ALB :443 /mlflow |
| PostgreSQL | 5432 | Private only |
| Redis | 6379 | Private only |
| MWAA Airflow UI | 443 | MWAA managed endpoint |

---

## Cost Estimate (monthly, production)

| Service | Spec | ~Cost/month |
|---|---|---|
| ECS Fargate (backend x2) | 2 vCPU, 4GB each | $120 |
| ECS Fargate (frontend) | 0.5 vCPU, 1GB | $15 |
| ECS Fargate (MLflow) | 1 vCPU, 2GB | $30 |
| RDS PostgreSQL Multi-AZ | db.r6g.large | $200 |
| ElastiCache Redis x3 | cache.r6g.large | $180 |
| MWAA (small) | mw1.small | $300 |
| S3 (all buckets ~50GB) | Standard | $10 |
| ALB | Per LCU | $25 |
| CloudFront | 100GB transfer | $15 |
| Secrets Manager | 5 secrets | $2 |
| CloudWatch | Logs + Metrics | $30 |
| **Total** | | **~$927/month** |
