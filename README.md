Prometheus to Elasticsearch Demo

This demo shows:

- a simple Python app exposing synthetic Prometheus metrics
- Twos ways of scraping the metrics:
  - Prometheus scraping the app and sending metrics to Elasticsearch using `remote_write`
  - Grafana Alloy scraping the app directly and sending metrics to Elasticsearch without Prometheus
- Kibana querying the metrics with PromQL
- a dashboard exported as a saved object
- alert queries packaged for reuse

Project structure

```text
Prometheus-Demo/
  app/
    app.py
    requirements.txt
  prometheus/
    prometheus.yml
  alloy/
    config.alloy
  alerts/
    dev-tools-queries.http
  saved-objects/
    prometheus-remote-write-demo-dashboard.ndjson
  Dockerfile
  docker-compose.yml
  README.md
```

Prerequisites
```text
Docker Desktop
Elastic deployment with Prometheus remote write support
Kibana access
API key with write access to metrics-*
```


Configure Prometheus
Edit prometheus/prometheus.yml and set your Elasticsearch endpoint and API key:

```text
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: "demo-python-app"
    static_configs:
      - targets: ["demo-app:8000"]

remote_write:
  - url: "https://YOUR_ES_ENDPOINT/_prometheus/api/v1/write"
    authorization:
      type: ApiKey
      credentials: YOUR_API_KEY
```


Configure Alloy
Edit alloy/config.alloy and set your Elasticsearch endpoint and API key:

```text
prometheus.scrape "demo_app" {
  targets = [
    {
      __address__ = "demo-app:8000",
      job         = "demo-python-app-alloy",
    },
  ]

  forward_to = [prometheus.remote_write.elastic.receiver]
}

prometheus.remote_write "elastic" {
  endpoint {
    url = "https://YOUR_ES_ENDPOINT/_prometheus/api/v1/write"

    headers = {
      Authorization = "Api Key YOUR_API_KEY",
    }
  }
}
```

Run the demo
Prometheus ingestion path
```text
docker compose --profile prometheus up --build
```

Alloy ingestion path
```text
docker compose --profile alloy up --build
```

Verify
App:
```text
http://localhost:8000/
http://localhost:8000/metrics
```

Prometheus:
```text
http://localhost:9090
```

Alloy:
```text
http://localhost:12345
```

Prometheus mode
In Prometheus, check Status > Targets and confirm the app target is UP.

Alloy mode
Check the Alloy logs:

```text
docker logs demo-alloy
```

You should see Alloy start successfully and initialize:
prometheus.scrape.demo_app
prometheus.remote_write.elastic

Verify in Kibana
Set the time range to Last 15 minutes or Last 1 hour.
Try:
```text
TS metrics-*
```

Example PromQL queries:
```text
PROMQL demo_active_users
PROMQL demo_cpu_temp_celsius
PROMQL sum(rate(demo_requests_total[1m]))
PROMQL sum by (status) (rate(demo_requests_total[1m]))
PROMQL sum by (endpoint) (rate(demo_errors_total[5m]))
PROMQL demo_queue_depth
```

To prove Alloy is scraping without Prometheus, use:
```text
PROMQL sum by (job) (rate(demo_requests_total[1m]))
```

Dashboard
Import the saved object from:
```text
saved-objects/prometheus-remote-write-demo-dashboard.ndjson
```

Alerts
Alert queries are packaged in:
```text
alerts/dev-tools-queries.http
```

Example alert conditions:
```text
PROMQL step=60 metric_value=(sum(rate(demo_errors_total[5m])))
| WHERE metric_value > 0

PROMQL step=60 metric_value=(max(demo_queue_depth))
| WHERE metric_value > 40

PROMQL step=60 metric_value=(max(demo_cpu_temp_celsius))
| WHERE metric_value > 75
```

Stop the demo
```text
docker compose down
```









