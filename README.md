# JUMO Data Platform

A full-stack microservices data platform demonstrating the complete JUMO data engineering stack: **Go microservices · Kafka · PySpark · Airflow · PostgreSQL warehouse · React BI dashboard · Kubernetes · GitHub Actions CI/CD · Prometheus · Grafana**.

Built on Ubuntu 26, designed to run safely on 4 GB RAM using Docker Compose profiles.

---

## Architecture

```
React Frontend :3000
  ├── Admin Panel       → admin-service :8002
  ├── Ambassador Portal → ambassador-service :8003
  └── Analytics (BI)    → analytics-service :8005

checkout-service :8004
  ├── Stripe payment processing
  └── Kafka producer → orders.completed

Kafka :9092
  └── email-service (consumer) → SMTP notifications

analytics-service :8005
  └── reads PostgreSQL warehouse_db

PySpark job (batch)
  └── MySQL ambassador_db → aggregates → PostgreSQL warehouse_db

Airflow :8080
  └── daily DAG: run Spark → DQ checks → email report

Prometheus :9090 ← /metrics from all Go services
Grafana :3001   ← pre-built platform-overview dashboard
```

---

## Service Map

| Service | Port | Stack | Description |
|---|---|---|---|
| `users` | 8001 | Go, Fiber, MySQL | Auth — register, login, JWT |
| `admin` | 8002 | Go, Fiber, MySQL, Redis | Admin panel API |
| `ambassador` | 8003 | Go, Fiber, MySQL, Redis | Ambassador portal API |
| `checkout` | 8004 | Go, Fiber, MySQL, Stripe, Kafka | Order creation + event publishing |
| `analytics` | 8005 | Go, Fiber, PostgreSQL | BI read API for warehouse data |
| `email` | — | Go, Kafka consumer, SMTP | Async transactional emails |
| `spark-job` | — | Python, PySpark | Batch revenue aggregation |
| `airflow` | 8080 | Python, Airflow 2.8 | Pipeline orchestration + DQ |
| `prometheus` | 9090 | Prometheus | Metrics scraping |
| `grafana` | 3001 | Grafana | Monitoring dashboards |

---

## Quickstart

```bash
git clone <this-repo>
cd go_microservices

# 1. Configure environment
cp .env.example .env
# Edit .env: add your STRIPE_KEY

# 2. Start core services (~2 GB RAM)
docker compose up

# 3. Seed sample data (wait for DB healthy first)
docker compose exec admin go run src/commands/populateUsers.go
docker compose exec admin go run src/commands/populateProducts.go

# 4. Open the frontend
open http://localhost:3000
```

---

## RAM-Safe Docker Compose Profiles

**4 GB machine — never run all profiles simultaneously.**

```bash
# Core only — all Go services + DBs + Redis (~2 GB)
docker compose up

# Core + Kafka + email service (~2.4 GB)
docker compose --profile kafka up

# Spark batch job (one-shot, exits when done, ~2.5 GB)
docker compose down   # stop core first
docker compose --profile pipeline run --rm spark-job

# Airflow UI (~2.5 GB — stop core first)
docker compose --profile pipeline up airflow
# Open: http://localhost:8080  (user: airflow / airflow)

# Monitoring dashboard (~2.3 GB — stop core first)
docker compose --profile monitoring up
# Grafana: http://localhost:3001  (user: admin / admin)
# Prometheus: http://localhost:9090
```

---

## Technology Stack

| Category | Technology |
|---|---|
| Languages | Go 1.24, Python 3.11, TypeScript |
| API framework | Fiber v2 |
| ORM | GORM |
| Auth | JWT (dgrijalva/jwt-go) |
| Payment | Stripe |
| Streaming | Apache Kafka (KRaft, Bitnami) |
| Batch processing | Apache Spark 3.5 (PySpark) |
| Orchestration | Apache Airflow 2.8 |
| Databases | MySQL 8, PostgreSQL 15 |
| Cache | Redis 7 |
| Frontend | React 17, TypeScript, C3.js |
| Monitoring | Prometheus, Grafana |
| Containerisation | Docker, Docker Compose v2 |
| CI/CD | GitHub Actions → GHCR |
| Kubernetes | K8s manifests (k8s/) |

---

## CI/CD

GitHub Actions workflows in `.github/workflows/`:

| Workflow | Trigger | What it does |
|---|---|---|
| `ci-go-*.yml` | push / PR | go vet + go build per service |
| `ci-react-frontend.yml` | push / PR | npm ci + npm test + docker build |
| `ci-spark.yml` | push / PR | pytest spark/tests/ |
| `cd-docker-push.yml` | merge to main | build all images → push to GHCR |

---

## Kubernetes

Manifests in `k8s/` — apply to any cluster:
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml   # fill in base64 values first
kubectl apply -f k8s/infra/
kubectl apply -f k8s/users/
kubectl apply -f k8s/admin/
kubectl apply -f k8s/ambassador/
kubectl apply -f k8s/checkout/
kubectl apply -f k8s/analytics/
kubectl apply -f k8s/email/
kubectl apply -f k8s/react-frontend/
kubectl apply -f k8s/ingress.yaml
```

See [`k8s/README.md`](k8s/README.md) for full details.

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).
