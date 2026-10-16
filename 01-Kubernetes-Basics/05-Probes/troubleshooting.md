# Kubernetes Probes — Troubleshooting

## 1. Troubleshooting Philosophy

When a Pod is not Ready or is repeatedly restarting, don't immediately change the probe configuration.

First determine:

```text
What is failing?
       ↓
Probe?
       ↓
Application?
       ↓
Port?
       ↓
Endpoint?
       ↓
Dependency?
       ↓
Resources?
```

Basic flow:

```text
kubectl get pods
        ↓
kubectl describe pod
        ↓
Check Events
        ↓
Check logs
        ↓
Check probe configuration
        ↓
Test application manually
        ↓
Identify root cause
        ↓
Fix
        ↓
Verify
```

---

# 2. Scenario 1 — Readiness Probe Failed with HTTP 404

## Symptom

Pod showed:

```text
0/1 Running
```

The container itself was running, but the Pod was not Ready.

---

## Initial Check

```bash
kubectl get pods
```

Observed:

```text
READY   STATUS
0/1     Running
```

Important:

```text
Running ≠ Ready
```

---

## Describe the Pod

```bash
kubectl describe pod <pod-name>
```

Check the Events section.

We found:

```text
Readiness probe failed:
HTTP probe failed with statuscode: 404
```

---

## Investigation

The readiness probe was configured as:

```yaml
readinessProbe:
  httpGet:
    path: /does-not-exist
    port: 80
```

The Nginx application does not provide that path.

Therefore:

```text
GET /does-not-exist
        ↓
HTTP 404
        ↓
Readiness probe fails
        ↓
Pod remains NotReady
```

---

## Manual Verification

Test the valid endpoint:

```bash
kubectl exec -it <pod-name> -- /bin/sh
```

Then:

```bash
wget -S -O - http://127.0.0.1/
```

The root endpoint returned HTTP 200.

The configured path returned HTTP 404.

---

## Root Cause

Incorrect readiness probe path.

```text
Configured:
/does-not-exist

Actual:
/ 
```

---

## Fix

Changed:

```yaml
path: /does-not-exist
```

to:

```yaml
path: /
```

---

## Verification

```bash
kubectl get pods
```

Pod became:

```text
1/1 Running
```

The readiness probe succeeded.

---

## Learning

A readiness probe failure does not normally restart the container.

It tells Kubernetes:

```text
"This Pod should not receive traffic right now."
```

---

# 3. Scenario 2 — Understanding `Running 0/1`

This was observed during the readiness failure.

Example:

```text
READY   STATUS
0/1     Running
```

Meaning:

```text
Container process → Running
Application readiness → Failed
```

Do not immediately assume the container crashed.

Check:

```bash
kubectl describe pod <pod-name>
```

Look at:

```text
Readiness
Events
```

---

# 4. Scenario 3 — Liveness Probe Failure

## Baseline

The Nginx Pod initially showed:

```text
READY   STATUS    RESTARTS
1/1     Running   0
```

The liveness probe was:

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Intentional Failure

We stopped Nginx inside the container:

```bash
kubectl exec <pod-name> -- nginx -s stop
```

The application stopped responding to the health check.

---

## What Kubernetes Detected

The liveness probe started failing.

Kubernetes restarted the container.

Restart count changed:

```text
0 → 1
```

---

## Verification

```bash
kubectl get pods
```

Then:

```bash
kubectl describe pod <pod-name>
```

We could see:

```text
Restart Count: 1
```

The Pod itself remained the same Pod.

---

## Important Observation

Container restart:

```text
Same Pod
Same Pod name
Usually same Pod IP
Restart Count increases
```

Pod recreation:

```text
New Pod
Potentially new Pod name
Potentially new Pod IP
```

This distinction is important during production troubleshooting.

---

# 5. Scenario 4 — Startup Probe

We configured:

```yaml
startupProbe:
  httpGet:
    path: /
    port: 80
  failureThreshold: 12
  periodSeconds: 5
```

Maximum configured failure window:

```text
12 × 5 = 60 seconds
```

This gives the application time to start.

After startup succeeds:

```text
Startup
   ↓
Readiness/Liveness become relevant
```

---

# 6. Troubleshooting a Failed Readiness Probe

Use:

```bash
kubectl get pods
```

If:

```text
0/1 Running
```

then:

```bash
kubectl describe pod <pod-name>
```

Check:

```text
Readiness:
Events:
```

Then:

```bash
kubectl logs <pod-name>
```

Verify:

```text
Application running?
Correct port?
Correct endpoint?
```

Test from inside the container where possible:

```bash
kubectl exec -it <pod-name> -- /bin/sh
```

Then test the endpoint.

---

# 7. Troubleshooting a Failed Liveness Probe

First:

```bash
kubectl get pods
```

Look at:

```text
RESTARTS
```

If restart count is increasing:

```bash
kubectl describe pod <pod-name>
```

Check:

```text
Last State
Reason
Exit Code
Restart Count
Liveness
Events
```

Then:

```bash
kubectl logs <pod-name>
kubectl logs <pod-name> --previous
```

The `--previous` option is particularly useful when the previous container instance has already been restarted and its logs are available.

---

# 8. Troubleshooting a Startup Probe

If the application never becomes ready:

```bash
kubectl describe pod <pod-name>
```

Check whether:

```text
Startup probe failed
```

Possible causes:

* Application takes longer than configured startup window
* Wrong HTTP path
* Wrong port
* Application failed to start
* Application dependency unavailable
* Application is listening on another interface/port
* Probe configuration incorrect

---

# 9. Wrong Port Scenario

Application:

```text
Listening on 8080
```

Probe:

```yaml
httpGet:
  path: /
  port: 80
```

Result:

```text
Probe failure
```

Troubleshooting:

```bash
kubectl describe pod <pod-name>
```

Then verify what port the application is actually listening on.

The `containerPort` declaration alone does not make an application listen on that port.

Example:

```yaml
ports:
  - containerPort: 80
```

does not force the application to listen on port 80.

The application itself must listen there.

---

# 10. Wrong HTTP Path Scenario

Application supports:

```text
/
```

Probe checks:

```text
/health
```

If `/health` doesn't exist:

```text
HTTP 404
```

Probe fails.

Solution:

```text
Use a real health endpoint
```

For production applications, a dedicated health endpoint is usually better than using an arbitrary application page.

---

# 11. Slow Startup Scenario

Application takes:

```text
60 seconds
```

But liveness starts checking too early.

Potential flow:

```text
Application starting
       ↓
Liveness check
       ↓
FAIL
       ↓
Container restart
       ↓
Application starts again
       ↓
Liveness check
       ↓
FAIL
       ↓
Restart
```

Possible result:

```text
CrashLoopBackOff
```

Better approach:

```text
Startup Probe
       ↓
Allow application to initialize
       ↓
Startup succeeds
       ↓
Liveness takes over
```

---

# 12. Liveness Probe Too Aggressive

Bad configuration:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 2
  failureThreshold: 1
  timeoutSeconds: 1
```

If the application has a temporary 2-second delay:

```text
Temporary slowness
      ↓
Probe timeout
      ↓
Liveness failure
      ↓
Restart
```

Repeated restarts can make the incident worse.

### Production principle

Liveness should detect genuine application failure, not normal temporary slowness.

---

# 13. Readiness vs Liveness Troubleshooting

| Situation                              | Likely Probe                               |
| -------------------------------------- | ------------------------------------------ |
| Pod running but `0/1`                  | Readiness                                  |
| Restart count increasing               | Liveness / application failure             |
| Application takes a long time to start | Startup                                    |
| HTTP 404                               | Wrong endpoint/path                        |
| Connection refused                     | Wrong port/application not listening       |
| Timeout                                | Application slow/unavailable/network issue |
| Container never starts                 | Investigate container/config before probes |

---

# 14. Probe Troubleshooting Commands

### Check Pods

```bash
kubectl get pods
```

### Detailed information

```bash
kubectl describe pod <pod-name>
```

### Application logs

```bash
kubectl logs <pod-name>
```

### Previous container logs

```bash
kubectl logs <pod-name> --previous
```

### Enter container

```bash
kubectl exec -it <pod-name> -- /bin/sh
```

### Check Deployment

```bash
kubectl get deployment
```

### Check ReplicaSets

```bash
kubectl get rs
```

### Check events

```bash
kubectl get events --sort-by=.lastTimestamp
```

---

# 15. Production Troubleshooting Flow

## Application is not receiving traffic

```text
Check Pod
   ↓
kubectl get pods
   ↓
0/1?
   ↓
kubectl describe pod
   ↓
Readiness failure?
   ↓
Check Events
   ↓
Check endpoint
   ↓
Check port
   ↓
Check application logs
   ↓
Fix
   ↓
Verify Ready
```

---

## Application repeatedly restarting

```text
kubectl get pods
       ↓
RESTARTS increasing?
       ↓
kubectl describe pod
       ↓
Last State / Reason / Exit Code
       ↓
kubectl logs
       ↓
kubectl logs --previous
       ↓
Check liveness
       ↓
Check application
       ↓
Check resources
       ↓
Find root cause
       ↓
Fix
```

---

# 16. Common Misdiagnosis

### Mistake 1

Seeing:

```text
0/1 Running
```

and assuming:

```text
Container crashed
```

Not necessarily.

It may simply be a readiness failure.

---

### Mistake 2

Seeing:

```text
Restart Count: 1
```

and assuming a new Pod was created.

Not necessarily.

The container may simply have restarted inside the same Pod.

---

### Mistake 3

Immediately increasing probe timings.

First determine why the probe is failing.

---

### Mistake 4

Using liveness to check external dependencies.

For example:

```text
Application
     ↓
Database temporarily unavailable
     ↓
Liveness fails
     ↓
Application restarts
```

Repeated restarts may make recovery harder.

Often readiness is more appropriate for dependency availability, depending on the application's architecture.

---

# 17. Interview Scenarios

### Scenario 1

**Pod is `Running` but `0/1`. What do you check?**

Answer:

```text
I first check kubectl describe pod and Events.
If the container is running but Ready is false, I investigate the readiness probe.
I verify the configured path, port, application endpoint and application logs.
```

---

### Scenario 2

**Pod restart count keeps increasing.**

Answer:

```text
I check kubectl describe pod for Last State, Reason and Exit Code.
Then I check current and previous logs.
I inspect liveness probe configuration and application behavior to determine whether Kubernetes is restarting the container because of failed health checks or whether the application itself is crashing.
```

---

### Scenario 3

**Readiness probe returns 404.**

Answer:

```text
I verify the configured HTTP path against the application's actual endpoint.
A 404 generally indicates that the endpoint being checked doesn't exist.
I correct the path and verify that the Pod becomes Ready.
```

---

### Scenario 4

**Liveness probe continuously fails after deployment.**

Check:

```text
1. Application actually started?
2. Correct port?
3. Correct path?
4. Application logs?
5. Startup time?
6. Startup probe required?
7. Probe timeout/threshold appropriate?
```

---

### Scenario 5

**Application takes two minutes to start.**

Answer:

```text
I would consider using a startup probe so that Kubernetes allows the application sufficient time to initialize before liveness and readiness checks control its lifecycle.
```

---

# 18. Key Lessons

```text
Startup
→ Protect slow startup

Readiness
→ Control traffic

Liveness
→ Recover unhealthy containers
```

Remember:

```text
Running ≠ Ready
```

and:

```text
Container restart ≠ Pod recreation
```

Most important troubleshooting commands:

```bash
kubectl get pods
kubectl describe pod <pod>
kubectl logs <pod>
kubectl logs <pod> --previous
kubectl exec -it <pod> -- /bin/sh
kubectl get events --sort-by=.lastTimestamp
```

The troubleshooting mindset is:

```text
Observe
  ↓
Describe
  ↓
Events
  ↓
Logs
  ↓
Test
  ↓
Root Cause
  ↓
Fix
  ↓
Verify
```
