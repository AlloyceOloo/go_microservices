# Spark Aggregation Job

PySpark batch job that reads completed orders from MySQL and aggregates revenue metrics into the PostgreSQL data warehouse.

## What it computes

| Target table | Aggregation |
|---|---|
| `revenue_by_ambassador` | Total ambassador revenue + order count, grouped by ambassador email and date |
| `revenue_by_product` | Total product revenue + units sold, grouped by product title and date |
| `daily_order_summary` | Daily totals: order count, admin revenue, ambassador revenue |
| `pipeline_metadata` | `last_spark_run` timestamp — surfaced by Grafana |

## Running manually (RAM-safe)

```bash
# From go_microservices/ — stop core services first to free RAM
docker compose down

# Run Spark as a one-shot container (exits when done, ~512 MB)
docker compose --profile pipeline run --rm spark-job
```

## Running the unit tests locally

```bash
pip install pyspark==3.5.* pytest
pytest spark/tests/ -v
```

## Data sources

| Source | Connection |
|---|---|
| MySQL `ambassador.orders` | `MYSQL_HOST:3306` |
| MySQL `ambassador.order_items` | same |
| PostgreSQL `warehouse` | `WAREHOUSE_HOST:5432` |

All connection details are read from environment variables — see `../.env.example`.
