# Airflow DAG — Order Pipeline

Daily orchestration DAG that:
1. Triggers the Spark aggregation job
2. Runs data quality checks (order counts + revenue totals) between MySQL source and PostgreSQL warehouse
3. Sends an HTML email quality report to `DQ_ALERT_EMAIL`

## Starting Airflow (RAM-safe)

```bash
# Stop core services first to free RAM
cd go_microservices
docker compose down

# Start Airflow standalone (uses SQLite — saves ~300 MB vs PostgreSQL)
docker compose --profile pipeline up airflow
```

Open the Airflow UI at **http://localhost:8080**  
Default credentials: `airflow` / `airflow`

## Triggering the DAG manually

```bash
# From the UI: DAGs → order_pipeline → Trigger DAG
# Or from CLI:
docker compose --profile pipeline exec airflow airflow dags trigger order_pipeline
```

## DAG graph

```
run_spark_job
    │
    ├─ check_order_counts ──┐
    │                        ├─ build_report → send_quality_report
    └─ check_revenue_totals ┘
```

## Data quality thresholds

| Check | Threshold |
|---|---|
| Order count delta | ≤ 1% of MySQL source count |
| Revenue total delta | ≤ $0.01 absolute |

## Environment variables

| Variable | Description |
|---|---|
| `MYSQL_HOST` | MySQL host (ambassador_db) |
| `MYSQL_USER` / `MYSQL_PASS` | MySQL credentials |
| `MYSQL_DB` | Source database name |
| `WAREHOUSE_HOST` | PostgreSQL warehouse host |
| `WAREHOUSE_USER` / `WAREHOUSE_PASS` | Warehouse credentials |
| `DQ_ALERT_EMAIL` | Recipient for quality report emails |
| `SMTP_HOST` / `SMTP_PORT` | SMTP relay (Mailhog for local dev) |
