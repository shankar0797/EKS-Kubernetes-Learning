# Kubernetes Observability -- Notes

## 1. What is Observability?

Observability helps us understand what is happening inside an
application and Kubernetes environment.

  -----------------------------------------------------------------------
  Signal                  Main question           Typical tools
  ----------------------- ----------------------- -----------------------
  Metrics                 What is happening?      Metrics Server,
                                                  Prometheus, Grafana

  Logs                    What happened / why?    kubectl logs, Fluent
                                                  Bit, Loki, ELK

  Traces                  Where did a request     OpenTelemetry, Jaeger,
                          spend time?             Tempo
  -----------------------------------------------------------------------

Core mental model:

``` text
Metrics → WHAT is happening?
Logs    → WHAT happened / WHY?
Traces  → WHERE did the request spend time?
```

Production flow:

``` text
Kubernetes / Application
        |
        +---- Metrics ----> Prometheus ----> Grafana
        |
        +---- Logs -------> Collector -----> Loki/ELK
        |
        +---- Traces -----> OpenTelemetry -> Jaeger/Tempo
        |
        +---- Alerts ------> Alertmanager
```

------------------------------------------------------------------------

## 2. Metrics Server

### What?

Metrics Server collects basic CPU and memory usage for Kubernetes nodes
and Pods.

### Why?

It enables:

``` bash
kubectl top nodes
kubectl top pods
```

and provides resource metrics used by HPA.

### Minikube

``` bash
minikube addons enable metrics-server
```

Verify:

``` bash
kubectl get pods -n kube-system | grep metrics-server
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl top nodes
kubectl top pods -A
```

### Metrics Server vs Prometheus

**Metrics Server:** basic CPU/memory metrics and HPA resource metrics.

**Prometheus:** broader application/Kubernetes metrics, historical
time-series data, PromQL, dashboards and alerting.

------------------------------------------------------------------------

## 3. Resource-Pressure Lab

We deliberately ran CPU and memory stress workloads. The unsafe memory
test continuously allocated memory:

``` yaml
apiVersion: v1
kind: Pod
metadata:
  name: memory-test
  namespace: observability-lab
spec:
  containers:
    - name: memory-test
      image: python:3.12-alpine
      command:
        - python
        - -c
        - |
          data = []
          while True:
              data.append("x" * 1024 * 1024)
```

The Minikube container reached approximately 3 GiB / 3 GiB and the
Kubernetes API became unresponsive.

After recovery the Pod showed:

``` text
OOMKilled
Exit Code: 137
QoS Class: BestEffort
```

### Lesson

A workload without resource requests and limits can starve the
node/control plane.

Safer test configuration:

``` yaml
resources:
  requests:
    cpu: "50m"
    memory: "32Mi"
  limits:
    cpu: "200m"
    memory: "128Mi"
```

------------------------------------------------------------------------

## 4. Prometheus

### What?

Prometheus is a time-series monitoring system.

It:

1.  Scrapes metrics.
2.  Stores metrics.
3.  Queries metrics with PromQL.
4.  Evaluates alert rules.
5.  Sends firing alerts to Alertmanager.

Architecture:

``` text
Application
    |
    | /metrics
    v
Service / Pod
    |
    v
Prometheus
    |
    +---- PromQL
    |
    +---- Alert Rules
    |
    v
Alertmanager
```

------------------------------------------------------------------------

## 5. kube-prometheus-stack

Installed with Helm:

``` bash
kubectl create namespace monitoring

helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts

helm repo update

helm install monitoring \
  prometheus-community/kube-prometheus-stack \
  -n monitoring
```

Check:

``` bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

Important components:

  Component             Purpose
  --------------------- ---------------------------------
  Prometheus            Collects/stores/queries metrics
  Prometheus Operator   Manages Prometheus resources
  ServiceMonitor        Defines scrape targets
  Grafana               Visualization/dashboards
  Alertmanager          Alert handling/routing
  node-exporter         Node/OS metrics
  kube-state-metrics    Kubernetes object-state metrics

------------------------------------------------------------------------

## 6. ServiceMonitor

A ServiceMonitor is a Kubernetes custom resource used by the Prometheus
Operator to define which Service endpoints should be scraped.

``` text
Application
   |
   v
Pod
   |
   v
Service
   |
   v
ServiceMonitor
   |
   v
Prometheus
```

Our application target showed two endpoints:

``` text
10.244.0.57:8080/metrics   UP
10.244.0.58:8080/metrics   UP
```

This proved Prometheus was successfully scraping both application Pods.

------------------------------------------------------------------------

## 7. Prometheus Target Health

Useful URL:

``` text
http://localhost:9090/targets
```

Target:

``` text
UP
```

means Prometheus successfully scraped the target.

The generated metric:

``` promql
up
```

normally means:

``` text
1 = scrape succeeded
0 = scrape failed
```

`up=0` means the scrape failed; it does not automatically mean the
application itself is completely down.

------------------------------------------------------------------------

## 8. Application Metrics

The demo application exposed:

``` text
/metrics
```

and application metrics including:

``` text
app_requests_total
app_request_duration_seconds_sum
app_request_duration_seconds_count
```

Example:

``` text
app_requests_total{status="500", ...}
```

This allowed Prometheus to monitor application behavior.

------------------------------------------------------------------------

## 9. PromQL

PromQL is Prometheus Query Language.

Examples used:

``` promql
app_requests_total
```

``` promql
app_requests_total{status="500"}
```

``` promql
sum(app_requests_total)
```

``` promql
sum(increase(app_requests_total{status="500"}[5m]))
```

Mental model:

``` text
Metric + Labels + Functions/operators = Useful monitoring information
```

The goal of the lab was understanding the monitoring flow rather than
memorizing every PromQL function.

------------------------------------------------------------------------

## 10. Grafana

Grafana is the visualization/dashboard layer.

``` text
Application
    |
    v
Prometheus
    |
    v
Grafana
    |
    v
Dashboard
```

Access:

``` text
http://localhost:3000
```

### Dashboard created

**Panel 1 -- Total Application Requests**

``` promql
sum(app_requests_total)
```

Title:

``` text
Total Application Requests
```

**Panel 2 -- HTTP 500 Errors**

``` promql
sum(app_requests_total{status="500"})
```

Title:

``` text
HTTP 500 Errors
```

A latency panel was also created using request-duration sum/count
metrics.

------------------------------------------------------------------------

## 11. Logging

Logs are records of application/system events.

Metrics can tell us:

``` text
HTTP 500 errors increased.
```

Logs help answer:

``` text
What happened?
What error occurred?
```

Kubernetes logging flow:

``` text
Application
    |
stdout / stderr
    |
Container
    |
Kubernetes
    |
kubectl logs
```

Important commands:

``` bash
kubectl logs <pod>
kubectl logs <pod> -c <container>
kubectl logs -f <pod>
kubectl logs <pod> --previous
```

`--previous` is especially useful for CrashLoopBackOff.

### Centralized logging

Production architecture:

``` text
Pods
  |
  v
Log Collector
  |
  v
Centralized Storage
  |
  +---- Loki ----> Grafana
  |
  +---- Elasticsearch ----> Kibana
```

Common collectors:

``` text
Fluent Bit
Fluentd
Vector
Promtail
```

------------------------------------------------------------------------

## 12. Alerting

An alert represents a condition that requires attention.

Example:

``` text
HTTP 500 errors >= 5 in 5 minutes
```

Architecture:

``` text
Metric
  |
  v
Prometheus
  |
  | evaluates rule
  v
Alert
  |
  v
Alertmanager
```

------------------------------------------------------------------------

## 13. Prometheus Alert Rule Lab

We created:

``` text
ObsDemoHighHTTP500
```

Rule:

``` promql
sum(increase(app_requests_total{status="500"}[5m])) >= 5
```

Duration:

``` text
for: 30s
```

Meaning: the condition must remain true for 30 seconds before the alert
becomes firing.

Summary:

``` text
OBS demo application has high HTTP 500 errors
```

Description:

``` text
The application generated 5 or more HTTP 500 responses in the last 5 minutes.
```

Severity:

``` text
warning
```

------------------------------------------------------------------------

## 14. Alert Lifecycle

``` text
INACTIVE
   |
   | condition becomes true
   v
PENDING
   |
   | condition remains true for 30s
   v
FIRING
   |
   v
Alertmanager
```

If the condition becomes false before the `for` duration:

``` text
PENDING → INACTIVE
```

------------------------------------------------------------------------

## 15. Alertmanager

Alertmanager receives firing alerts from Prometheus.

Main responsibilities:

``` text
Grouping
Silencing
Inhibition
Routing
Notification handling
```

Access:

``` text
http://localhost:9093
```

Our custom alert successfully appeared as:

``` text
alertname="ObsDemoHighHTTP500"
severity="warning"
```

This proved the complete alerting pipeline.

------------------------------------------------------------------------

## 16. End-to-End Alerting Lab

Generate ten HTTP 500 requests:

``` bash
for i in {1..10}; do
  kubectl run alert-now-$i \
    -n obs-app \
    --image=curlimages/curl:8.10.1 \
    --restart=Never \
    -- curl -s http://obs-demo-app/api/error >/dev/null
done
```

Flow:

``` text
10 HTTP 500 requests
        |
        v
app_requests_total{status="500"}
        |
        v
Prometheus
        |
        v
increase(...[5m]) >= 5
        |
        v
wait 30 seconds
        |
        v
ObsDemoHighHTTP500 = FIRING
        |
        v
Alertmanager
```

------------------------------------------------------------------------

## 17. Tracing

Tracing follows an individual request across services.

Example:

``` text
API Gateway       100ms
     |
     v
Order Service     200ms
     |
     v
Payment Service   4.5s  ← bottleneck
     |
     v
Database          100ms
```

Tools:

``` text
OpenTelemetry
Jaeger
Tempo
```

------------------------------------------------------------------------

## 18. Metrics vs Logs vs Traces

``` text
Metrics → What is happening?

Logs → What happened / why?

Traces → Where did the request spend time?
```

Example:

``` text
Metric: HTTP 500 rate increased
Log: Database connection failed
Trace: Payment Service took 4.5 seconds
```

------------------------------------------------------------------------

## 19. Monitoring vs Observability

**Monitoring** watches known conditions.

Example:

``` text
CPU > 80%
```

**Observability** helps investigate unknown problems.

Example:

``` text
Why did checkout become slow?

Metric → latency increased
Log → payment API timeout
Trace → payment service spent 4.5 seconds
```

------------------------------------------------------------------------

## 20. Interview Explanation

> I implemented Kubernetes observability using Metrics Server for basic
> resource metrics and Prometheus for application and cluster metrics. I
> used ServiceMonitor to expose application metrics to Prometheus and
> Grafana for visualization. I worked with Kubernetes logs and
> understood centralized logging with collectors such as Fluent Bit and
> storage such as Loki or Elasticsearch. I created a Prometheus alert
> rule for five or more HTTP 500 errors within five minutes. When the
> condition remained true for 30 seconds, Prometheus changed the alert
> to firing and sent it to Alertmanager.

------------------------------------------------------------------------

## 21. Interview Q&A

### What is Prometheus?

A time-series monitoring system that scrapes, stores and queries metrics
and evaluates alert rules.

### What is Metrics Server?

A Kubernetes component providing basic CPU and memory metrics, commonly
used by `kubectl top` and HPA.

### Metrics Server vs Prometheus?

Metrics Server focuses on basic Kubernetes resource metrics. Prometheus
provides broader persistent time-series monitoring, PromQL and alerting.

### What is ServiceMonitor?

A Prometheus Operator CRD describing Kubernetes endpoints that should be
scraped.

### What is Grafana?

A visualization and dashboard platform that can query Prometheus and
other data sources.

### What is Alertmanager?

A component that receives Prometheus alerts and handles grouping,
routing, silencing and inhibition.

### What is `kubectl logs --previous`?

It retrieves logs from the previous container instance, especially
useful after a restart or CrashLoopBackOff.

### What does `up=1` mean?

The last Prometheus scrape succeeded.

### What does `up=0` mean?

The last Prometheus scrape failed.

### Metrics vs logs?

Metrics provide numerical measurements; logs provide event details.

### Metrics vs traces?

Metrics show aggregate system behavior; traces follow individual
requests across services.

------------------------------------------------------------------------

## 22. Cheat Sheet

``` text
Metrics Server
    ↓
CPU / Memory
    ↓
kubectl top / HPA

Prometheus
    ↓
Scrape / Store / Query
    ↓
PromQL / Alert Rules

ServiceMonitor
    ↓
Tells Prometheus what to scrape

Grafana
    ↓
Dashboards / Visualization

Logs
    ↓
kubectl logs
    ↓
Centralized logging in production

Alertmanager
    ↓
Group / Route / Silence / Inhibit

Tracing
    ↓
OpenTelemetry
    ↓
Jaeger / Tempo
```

Useful UIs:

``` text
Grafana       http://localhost:3000
Prometheus    http://localhost:9090
Alertmanager  http://localhost:9093
```

Final mental model:

``` text
             Kubernetes / Application
                       |
       +---------------+---------------+
       |               |               |
     Metrics          Logs           Traces
       |               |               |
   Prometheus      Collector      OpenTelemetry
       |               |               |
    Grafana        Loki/ELK       Jaeger/Tempo
       |
  Alert Rules
       |
 Alertmanager
       |
 Notifications
```
