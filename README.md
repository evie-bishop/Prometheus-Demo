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
  .env.example
  README.md
```

Prerequisites

```text
Docker Desktop
Elastic deployment with Prometheus remote write support
Kibana access
API key with write access to metrics-*
```

Configuration

All runtime configuration is driven from `.env`. Image versions, ports,
container names, and the Elasticsearch endpoint/API key are pinned there.
`.env.example` is the canonical template - change defaults via PR. Local
secrets go in `.env` (gitignored).

```bash
cp .env.example .env
# edit .env and set ES_ENDPOINT and ES_API_KEY
```

Pinned defaults (change via PR to `.env.example`):

```text
PYTHON_IMAGE=python:3.14-slim
PROMETHEUS_IMAGE=prom/prometheus:v3.11.3
ALLOY_IMAGE=grafana/alloy:v1.16.0
```

Python package versions are pinned in `app/requirements.txt`
(flask 3.1.3, prometheus_client 0.25.0).

How configs consume env vars:

- `alloy/config.alloy` reads `ES_ENDPOINT`, `ES_API_KEY`, `APP_TARGET`,
  and `SCRAPE_JOB_NAME` natively via `sys.env(...)`.
- `prometheus/prometheus.yml` is a template containing `__PLACEHOLDER__`
  tokens. The compose entrypoint renders it to `/tmp/prometheus.yml`
  with `sed` at container start.

Run the demo

By default `.env` sets `COMPOSE_PROFILES=prometheus,alloy`, so both ingestion
paths come up together:

```bash
docker compose up --build
```

To run just one path, override the profile on the command line:

```bash
docker compose --profile prometheus up --build   # Prometheus only
docker compose --profile alloy up --build        # Alloy only
```

Note: with both profiles active the same app metrics are written to
Elasticsearch twice - once via Prometheus (`job=demo-python-app`) and once
via Alloy (whatever `SCRAPE_JOB_NAME` is set to). That's intentional for
the demo comparison; pick a single profile if you want a single write path.

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

Prometheus mode: in Prometheus, check Status > Targets and confirm the app
target is UP.

Alloy mode: check the Alloy logs:

```bash
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

```bash
docker compose down
```
