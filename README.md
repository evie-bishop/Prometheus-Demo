# Prometheus to Elasticsearch Demo
This demo shows:
- a simple Python app exposing synthetic Prometheus metrics
- Prometheus scraping the app
- Prometheus sending metrics to Elasticsearch using `remote-write
- Kibana querying the metrics with PromQL
- a dashboard exported as a saved object
- alert queries packaged for reuse

## Project structure


```text
Prometheus-Demo/
  app/
    app.py
    requirements.txt
  prometheus/
    prometheus.yml
  alerts/
    dev-tools-queries.http
  saved-objects/
    prometheus-remote-write-demo-dashboard.ndjson
  Dockerfile
  docker-compose.yml
  README.md
```

## Preqs
Docker Desktop
Elastic deployment with Prometheus remote write support
Kibana access
API key with write access to metrics-*

## Confirgure Prometheus
Edit prometheus/prometheus.yml and set your Elasticsearch endpoint and API key:

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

## Run the Demo
From the project root:

docker compose up --build

## Verify
App:
http://localhost:8000/
http://localhost:8000/metrics

Prometheus:
http://localhost:9090
In Prometheus, check Status > Targets and confirm the app target is UP.

Verify in Kibana
Set the time range to Last 15 minutes or Last 1 hour.

Try:

TS metrics-*

Example PromQL queries:

✄𐘗sql code block:✄𐘗
PROMQL demo_active_users
PROMQL demo_cpu_temp_celsius
PROMQL sum(rate(demo_requests_total[1m]))
PROMQL sum by (status) (rate(demo_requests_total[1m]))
PROMQL sum by (endpoint) (rate(demo_errors_total[5m]))
PROMQL demo_queue_depth

## Dashboard
Import the saved object from:
saved-objects/prometheus-remote-write-demo-dashboard.ndjson

## Alerts
Alert queries are packaged in:
alerts/dev-tools-queries.http

Example alert conditions:
PROMQL step=60 metric_value=(sum(rate(demo_errors_total[5m])))
| WHERE metric_value > 0

PROMQL step=60 metric_value=(max(demo_queue_depth))
| WHERE metric_value > 40

PROMQL step=60 metric_value=(max(demo_cpu_temp_celsius))
| WHERE metric_value > 75

## Stop the demo
docker compose down




