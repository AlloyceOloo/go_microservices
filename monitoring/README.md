# Monitoring — Prometheus + Grafana

Metrics scraping and dashboards for the JUMO Data Platform.

## Starting monitoring (RAM-safe)

```bash
# Stop core services first to free RAM
cd go_microservices
docker compose down

# Start monitoring stack (~2.3 GB with core)
docker compose --profile monitoring up
```

| UI | URL | Credentials |
|---|---|---|
| Grafana | http://localhost:3001 | admin / admin |
| Prometheus | http://localhost:9090 | — |

## Dashboard panels

The pre-built **JUMO Platform Overview** dashboard (`platform-overview.json`) includes:

| Panel | Metric |
|---|---|
| HTTP Request Rate | `rate(http_requests_total[5m])` per service |
| HTTP Error Rate | `rate(http_requests_total{status=~"5.."}[5m])` per service |
| Kafka Throughput | `kafka_server_brokertopicmetrics_messagesin_total` for `orders.completed` |
| Warehouse Row Counts | `pg_stat_user_tables_n_live_tup` via postgres_exporter |
| Last Spark Run | `pipeline_metadata` table — updated by Spark job on each run |

## Adding metrics to a new Go service

Each service exposes `/metrics` via `fiberprometheus/v2`:

```go
import "github.com/ansrivas/fiberprometheus/v2"

prom := fiberprometheus.New("my-service")
prom.RegisterAt(app, "/metrics")
app.Use(prom.Middleware)
```

Then add a scrape job to `monitoring/prometheus.yml`:
```yaml
- job_name: my-service
  static_configs:
    - targets: ['my-service:8000']
```
