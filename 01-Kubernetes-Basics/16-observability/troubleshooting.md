# Kubernetes Observability -- Troubleshooting

## 1. Metrics API Not Available

### Symptom

``` bash
kubectl top nodes
```

returns:

``` text
error: Metrics API not available
```

### Check

``` bash
kubectl get pods -n kube-system | grep metrics-server
kubectl get apiservice v1beta1.metrics.k8s.io
```

### Fix on Minikube

``` bash
minikube addons enable metrics-server
```

Then:

``` bash
kubectl get pods -n kube-system | grep metrics-server
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl top nodes
```

Expected:

``` text
v1beta1.metrics.k8s.io   True
```

------------------------------------------------------------------------

## 2. Metrics Server Running but APIService False

### Symptom

The metrics-server Pod shows Running but:

``` text
v1beta1.metrics.k8s.io   False
```

or:

``` text
MissingEndpoints
```

### Troubleshoot

``` bash
kubectl describe apiservice v1beta1.metrics.k8s.io
kubectl describe pod -n kube-system <metrics-server-pod>
kubectl logs -n kube-system <metrics-server-pod>
```

Check:

-   readiness/liveness failures
-   Service endpoints
-   restart count
-   resource pressure

A Pod being `Running` does not necessarily mean it is `Ready` or its API
is usable.

------------------------------------------------------------------------

## 3. Metrics Server Became Unstable

### Symptoms

``` text
0/1 Running
```

or APIService becomes false.

### Root cause in this lab

The deliberately unsafe CPU/memory workloads consumed Minikube
resources. The Minikube container reached approximately 3 GiB / 3 GiB
and the control plane became unresponsive.

### Resolution

``` bash
kubectl delete pod cpu-test -n observability-lab
kubectl delete pod memory-test -n observability-lab
```

If Minikube is severely affected:

``` bash
minikube start
```

Verify:

``` bash
kubectl get nodes
kubectl get pods -n kube-system
kubectl top nodes
```

### Lesson

Always define reasonable resource requests and limits.

------------------------------------------------------------------------

## 4. Memory Test Shows OOMKilled

### Symptom

``` text
Reason: OOMKilled
Exit Code: 137
```

### Meaning

The container exceeded its available memory and was killed.

### Safer configuration

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

## 5. Prometheus UI Does Not Open

### Symptom

``` text
localhost:9090
ERR_CONNECTION_REFUSED
```

### Check the port

``` bash
sudo ss -ltnp | grep ':9090'
```

If a `kubectl` process is already listening, an existing port-forward is
active.

Test:

``` bash
curl -s http://127.0.0.1:9090/-/ready
```

Expected:

``` text
Prometheus Server is Ready.
```

If no port-forward exists:

``` bash
kubectl port-forward \
  -n monitoring \
  svc/monitoring-kube-prometheus-prometheus \
  9090:9090
```

Keep the terminal open.

------------------------------------------------------------------------

## 6. Port 9090 Already in Use

### Symptom

``` text
Unable to listen on port 9090
bind: address already in use
```

### Check

``` bash
sudo ss -ltnp | grep ':9090'
```

If an existing `kubectl` port-forward is present, do not start a second
one. Test it:

``` bash
curl -s http://127.0.0.1:9090/-/ready
```

------------------------------------------------------------------------

## 7. Prometheus Query Returns No Data

### Possible causes

1.  Wrong metric name.
2.  Metric is not being scraped.
3.  Time range is wrong.
4.  Application `/metrics` is not exposed.
5.  ServiceMonitor is not selecting the application.
6.  Target is down.

### Check

``` bash
kubectl get servicemonitor -n monitoring
```

Open:

``` text
http://localhost:9090/targets
```

The application target should be:

``` text
UP
```

Test the application metric endpoint directly:

``` bash
kubectl port-forward -n obs-app svc/obs-demo-app 8080:8080
curl http://127.0.0.1:8080/metrics
```

Confirm:

``` text
app_requests_total
```

exists.

------------------------------------------------------------------------

## 8. Application Metric Missing

Use this troubleshooting chain:

``` text
Application
   ↓
/metrics endpoint
   ↓
Service
   ↓
ServiceMonitor
   ↓
Prometheus target
   ↓
PromQL
```

Check:

``` bash
kubectl get pods -n obs-app
kubectl get svc -n obs-app
kubectl get servicemonitor -n monitoring
```

Then check:

``` text
http://localhost:9090/targets
```

------------------------------------------------------------------------

## 9. ServiceMonitor Target Missing

### Check

``` bash
kubectl get servicemonitor -n monitoring
kubectl describe servicemonitor <name> -n monitoring
```

Verify:

-   Prometheus selector
-   ServiceMonitor labels
-   Service selector
-   Service port name
-   `/metrics` path
-   namespace selection

Remember:

``` text
Prometheus selector
      ↓
ServiceMonitor
      ↓
Service
      ↓
Pod
      ↓
/metrics
```

A ServiceMonitor does not automatically scrape every Pod.

------------------------------------------------------------------------

## 10. Prometheus Target DOWN

Open:

``` text
http://localhost:9090/targets
```

Inspect the scrape error.

Common causes:

``` text
Connection refused
404
Timeout
DNS failure
Wrong port
Wrong path
```

Test from inside Kubernetes:

``` bash
kubectl run curl-test \
  -n obs-app \
  --rm -it \
  --image=curlimages/curl:8.10.1 \
  -- curl -v http://obs-demo-app:8080/metrics
```

------------------------------------------------------------------------

## 11. Grafana Dashboard Shows No Data

Open:

``` text
http://localhost:3000
```

Check:

1.  Datasource is Prometheus.
2.  Query works directly in Prometheus.
3.  Dashboard time range includes recent data.
4.  Panel query is correct.

Example:

``` promql
sum(app_requests_total)
```

If it works in Prometheus but not Grafana, investigate the Grafana
datasource/time range/panel configuration.

------------------------------------------------------------------------

## 12. Grafana Panel Looks Empty

Check the time selector.

Try:

``` text
Last 15 minutes
```

or:

``` text
Last 1 hour
```

Then refresh.

------------------------------------------------------------------------

## 13. Custom Alert Shows INACTIVE

The alert rule was:

``` promql
sum(increase(app_requests_total{status="500"}[5m])) >= 5
```

It is only true when at least five new HTTP 500 responses occurred
during the previous five minutes.

Generate fresh errors:

``` bash
for i in {1..10}; do
  kubectl run alert-now-$i \
    -n obs-app \
    --image=curlimages/curl:8.10.1 \
    --restart=Never \
    -- curl -s http://obs-demo-app/api/error >/dev/null
done
```

Wait 30--60 seconds and check:

``` text
http://localhost:9090/alerts
```

------------------------------------------------------------------------

## 14. Alert Stays PENDING

### Symptom

``` text
PENDING
```

### Reason

The rule has:

``` text
for: 30s
```

The condition must remain true for 30 seconds.

Lifecycle:

``` text
INACTIVE
   ↓
condition true
   ↓
PENDING
   ↓
30 seconds
   ↓
FIRING
```

If the condition becomes false first:

``` text
PENDING → INACTIVE
```

------------------------------------------------------------------------

## 15. Alert Fires in Prometheus but Not Alertmanager

Check Prometheus:

``` text
http://localhost:9090/alerts
```

Confirm:

``` text
ObsDemoHighHTTP500
FIRING
```

Then check:

``` text
http://localhost:9093/#/alerts
```

If Alertmanager is unreachable:

``` bash
sudo ss -ltnp | grep ':9093'
```

Start port-forward if required:

``` bash
kubectl port-forward \
  -n monitoring \
  svc/monitoring-kube-prometheus-alertmanager \
  9093:9093
```

Test:

``` bash
curl -I http://127.0.0.1:9093
```

------------------------------------------------------------------------

## 16. SSH Tunnel Shows Connection Refused

### Symptom

Windows SSH prints:

``` text
channel ...: open failed: connect failed: Connection refused
```

### Meaning

The SSH tunnel exists, but the EC2-side destination port is not
listening.

Example:

``` text
Windows localhost:9093
       ↓ SSH
EC2 127.0.0.1:9093
       ↓
No process listening
```

### Fix

On EC2:

``` bash
kubectl port-forward \
  -n monitoring \
  svc/monitoring-kube-prometheus-alertmanager \
  9093:9093
```

For Prometheus:

``` bash
kubectl port-forward \
  -n monitoring \
  svc/monitoring-kube-prometheus-prometheus \
  9090:9090
```

Keep the port-forward terminal open.

------------------------------------------------------------------------

## 17. Alertmanager Shows Other Alerts but Not Custom Alert

Alertmanager may show:

``` text
Watchdog
KubeJobFailed
TargetDown
KubeControllerManagerInstanceUnreachable
```

while:

``` text
ObsDemoHighHTTP500
```

is missing.

This does not automatically mean Alertmanager is broken.

Check Prometheus:

``` text
http://localhost:9090/alerts
```

Search:

``` text
ObsDemoHighHTTP500
```

If:

``` text
INACTIVE
```

generate fresh HTTP 500 errors.

If:

``` text
FIRING
```

but Alertmanager does not show it, investigate Prometheus → Alertmanager
communication.

------------------------------------------------------------------------

## 18. Rule Exists but Does Not Fire

Test the metric:

``` promql
app_requests_total{status="500"}
```

Then:

``` promql
increase(app_requests_total{status="500"}[5m])
```

Then:

``` promql
sum(increase(app_requests_total{status="500"}[5m])) >= 5
```

This isolates:

``` text
Metric exists?
      ↓
Increase detected?
      ↓
Threshold reached?
      ↓
Rule firing?
```

------------------------------------------------------------------------

## 19. Application Logs Troubleshooting

Basic:

``` bash
kubectl logs <pod> -n obs-app
```

Follow:

``` bash
kubectl logs -f <pod> -n obs-app
```

Previous container:

``` bash
kubectl logs <pod> -n obs-app --previous
```

Specific container:

``` bash
kubectl logs <pod> -n obs-app -c <container>
```

For CrashLoopBackOff, always check:

``` bash
kubectl logs <pod> --previous
kubectl describe pod <pod>
```

------------------------------------------------------------------------

## 20. Minikube Becomes Unresponsive

### Symptoms

``` bash
kubectl get pods
```

hangs or fails.

### Check

``` bash
docker stats minikube
free -h
```

If Minikube is consuming nearly all allocated resources, resource
exhaustion may be the cause.

Remove the resource-heavy workload first.

If recovery is required:

``` bash
minikube start
```

Then:

``` bash
kubectl get nodes
kubectl get pods -A
```

------------------------------------------------------------------------

## 21. Observability Troubleshooting Decision Tree

``` text
Problem
  |
  +-- CPU/Memory metrics unavailable?
  |       └── Check Metrics Server
  |
  +-- Prometheus metric missing?
  |       ├── Check /metrics
  |       ├── Check Service
  |       ├── Check ServiceMonitor
  |       └── Check target health
  |
  +-- Grafana no data?
  |       ├── Check Prometheus query
  |       ├── Check datasource
  |       └── Check time range
  |
  +-- Alert inactive?
  |       ├── Check expression
  |       ├── Check metric value
  |       ├── Check threshold
  |       └── Check for duration
  |
  +-- Alert not in Alertmanager?
          ├── Confirm Prometheus = FIRING
          ├── Check Alertmanager port-forward
          └── Check Prometheus → Alertmanager communication
```

------------------------------------------------------------------------

## 22. Production Troubleshooting Order

``` text
1. Check application availability
2. Check Pods
3. Check metrics
4. Check logs
5. Check recent deployments/config changes
6. Check traces for distributed applications
7. Check infrastructure dependencies
8. Identify root cause
9. Fix
10. Verify metrics/logs/alerts return to normal
```

------------------------------------------------------------------------

## 23. Interview Troubleshooting Example

### Problem

Application returns HTTP 500 errors.

### Investigation

``` text
Grafana
  ↓
HTTP 500 metric increased
  ↓
Prometheus
  ↓
Alert fired
  ↓
Alertmanager
  ↓
Application logs
  ↓
Root cause
```

### Interview answer

> I would first confirm the increase through application metrics. Then I
> would inspect the firing alert and application logs. If the
> application is distributed across multiple services, I would use
> tracing to identify where the request failed or became slow. After
> resolving the issue, I would verify that the error metric dropped and
> the alert returned to inactive.

------------------------------------------------------------------------

## 24. Final Observability Architecture

``` text
                    Users
                      |
                      v
                Kubernetes App
                      |
        +-------------+-------------+
        |             |             |
        v             v             v
     Metrics         Logs         Traces
        |             |             |
        v             v             v
   Prometheus      Collector    OpenTelemetry
        |             |             |
        v             v             v
     Grafana        Loki/ELK     Jaeger/Tempo
        |
        v
   Alert Rules
        |
        v
  Alertmanager
        |
        v
 Notifications
```

## Final checklist

-   [x] Metrics Server
-   [x] Prometheus
-   [x] ServiceMonitor
-   [x] Application metrics
-   [x] PromQL basics
-   [x] Grafana
-   [x] Dashboard
-   [x] Kubernetes logs
-   [x] Alert rules
-   [x] Alertmanager
-   [x] Custom HTTP 500 alert
-   [x] End-to-end firing alert
-   [x] Tracing concepts
-   [x] Observability troubleshooting
