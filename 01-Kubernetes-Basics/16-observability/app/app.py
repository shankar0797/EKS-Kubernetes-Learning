from flask import Flask, jsonify, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "app_requests_total",
    "Total application requests",
    ["endpoint", "method", "status"]
)

REQUEST_LATENCY = Histogram(
    "app_request_duration_seconds",
    "Application request latency",
    ["endpoint"]
)

@app.route("/health")
def health():
    return jsonify(status="healthy")

@app.route("/api/orders")
def orders():
    start = time.time()
    response = jsonify(
        orders=[
            {"id": 101, "status": "created"},
            {"id": 102, "status": "processing"}
        ]
    )
    REQUEST_COUNT.labels("/api/orders", "GET", "200").inc()
    REQUEST_LATENCY.labels("/api/orders").observe(time.time() - start)
    return response

@app.route("/api/slow")
def slow():
    start = time.time()
    time.sleep(5)
    REQUEST_COUNT.labels("/api/slow", "GET", "200").inc()
    REQUEST_LATENCY.labels("/api/slow").observe(time.time() - start)
    return jsonify(message="slow response completed")

@app.route("/api/error")
def error():
    REQUEST_COUNT.labels("/api/error", "GET", "500").inc()
    app.logger.error("Intentional application error triggered")
    return jsonify(error="internal application error"), 500

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
