import random
import time
import threading
from flask import Flask, jsonify
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
app = Flask(__name__)
# Prometheus metrics
REQUESTS_TOTAL = Counter(
    "demo_requests_total",
    "Total number of demo requests",
    ["endpoint", "method", "status"]
)
ERRORS_TOTAL = Counter(
    "demo_errors_total",
    "Total number of demo errors",
    ["endpoint", "error_type"]
)
REQUEST_LATENCY_SECONDS = Histogram(
    "demo_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"],
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5)
)
QUEUE_DEPTH = Gauge(
    "demo_queue_depth",
    "Synthetic queue depth",
    ["queue_name"]
)
ACTIVE_USERS = Gauge(
    "demo_active_users",
    "Synthetic active users"
)
CPU_TEMP = Gauge(
    "demo_cpu_temp_celsius",
    "Synthetic CPU temperature"
)
def background_metric_updates():
    while True:
        ACTIVE_USERS.set(random.randint(20, 200))
        CPU_TEMP.set(round(random.uniform(45.0, 85.0), 2))
        QUEUE_DEPTH.labels(queue_name="orders").set(random.randint(0, 50))
        QUEUE_DEPTH.labels(queue_name="payments").set(random.randint(0, 30))
        QUEUE_DEPTH.labels(queue_name="shipping").set(random.randint(0, 20))
        # Generate synthetic traffic
        for endpoint in ["/", "/api/orders", "/api/payments", "/api/shipping"]:
            request_count = random.randint(1, 8)
            for _ in range(request_count):
                method = random.choice(["GET", "POST"])
                status = random.choices(["200", "200", "200", "500"], weights=[70, 15, 10, 5])[0]
                latency = random.uniform(0.05, 1.5)
                REQUESTS_TOTAL.labels(endpoint=endpoint, method=method, status=status).inc()
                REQUEST_LATENCY_SECONDS.labels(endpoint=endpoint).observe(latency)
                if status == "500":
                    ERRORS_TOTAL.labels(endpoint=endpoint, error_type="server_error").inc()
        time.sleep(5)
@app.route("/")
def home():
    return jsonify({"message": "Demo app is running"})
@app.route("/health")
def health():
    return jsonify({"status": "ok"})
@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
if __name__ == "__main__":
    thread = threading.Thread(target=background_metric_updates, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=8000)