# Kubernetes Liveness Probe — Troubleshooting

## 1. Purpose

This document covers troubleshooting of Kubernetes liveness probe failures.

The main troubleshooting question is:

> **Why is Kubernetes deciding that the container is unhealthy and restarting it?**

Remember:

```text
Liveness failure
      ↓
Container restart
```

But:

```text
Liveness failure ≠ Root Cause
```

The probe failure is often the symptom. We must identify why the application failed the health check.

---

# 2. Standard Troubleshooting Flow

```text
kubectl get pods
        ↓
Check RESTARTS
        ↓
kubectl describe pod
        ↓
Check State / Last State
        ↓
Check Reason / Exit Code
        ↓
Check Events
        ↓
Check liveness configuration
        ↓
Check application logs
        ↓
Check previous container logs
        ↓
Test application endpoint
        ↓
Find root cause
        ↓
Fix
        ↓
Verify stable Pod
```

---

# 3. Actual Lab — Liveness Failure

## Initial State

We created an Nginx Deployment with a liveness probe:

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 5
```

Initially:

```bash
kubectl get pods
```

showed:

```text
READY   STATUS    RESTARTS
1/1     Running   0
```

This confirmed that:

* Container was running
* Pod was Ready
* Nginx was responding
* Liveness probe was succeeding

---

# 4. Intentionally Breaking the Application

To test Kubernetes self-recovery, we stopped Nginx inside the container:

```bash
kubectl exec nginx-liveness-6fddbfc9-w59ds -- nginx -s stop
```

Nginx stopped responding on port 80.

Therefore:

```text
Nginx stopped
     ↓
HTTP / no longer responds
     ↓
Liveness probe fails
     ↓
Kubernetes detects repeated failure
     ↓
Container restarted
```

---

# 5. Verify the Restart

Check:

```bash
kubectl get pods
```

The restart count increased:

```text
RESTARTS
0 → 1
```

Then:

```bash
kubectl describe pod <pod-name>
```

Check:

```text
State
Last State
Restart Count
Events
```

The important observation was:

```text
Same Pod
     ↓
Container restarted
     ↓
Restart Count increased
```

The Pod itself was not recreated.

---

# 6. Container Restart vs Pod Recreation

This is an important troubleshooting distinction.

### Container restart

```text
Pod
 |
 └── Container
        ↓
      Restart
```

The Pod generally keeps:

* Same Pod name
* Same Pod identity
* Same Pod IP

The restart count increases.

### Pod recreation

```text
Old Pod
   ↓
Deleted
   ↓
New Pod
```

The new Pod can have:

* Different name
* Different IP
* New container instance

Therefore:

> A liveness failure normally causes a container restart inside the existing Pod.

---

# 7. Check Pod State

Use:

```bash
kubectl describe pod <pod-name>
```

Important fields:

```text
Containers:
  State:
  Last State:
  Ready:
  Restart Count:
```

Example investigation:

```text
State:
  Running

Last State:
  Terminated

Restart Count:
  1
```

This indicates the container had previously terminated and was restarted.

---

# 8. Check Events

Run:

```bash
kubectl get events --sort-by=.lastTimestamp
```

Or:

```bash
kubectl describe pod <pod-name>
```

Look at the Events section.

Events can help determine whether:

* Liveness probe failed
* Container restarted
* Image failed to pull
* Container failed to start
* Scheduling failed
* Other Kubernetes-level problems occurred

---

# 9. Check Application Logs

Run:

```bash
kubectl logs <pod-name>
```

If the container has restarted, also try:

```bash
kubectl logs <pod-name> --previous
```

`--previous` is useful for investigating the previous container instance after a restart.

However, previous logs may not always be available depending on the container runtime/log retention situation.

---

# 10. Check the Liveness Configuration

Use:

```bash
kubectl describe pod <pod-name>
```

Look for:

```text
Liveness:
  HTTP GET:
  Path:
  Port:
  Initial Delay:
  Timeout:
  Period:
  Failure Threshold:
```

Verify that these values match the actual application.

---

# 11. Scenario — Wrong HTTP Path

Suppose the application exposes:

```text
/
```

but the probe checks:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 80
```

If `/health` does not exist:

```text
GET /health
     ↓
HTTP 404
     ↓
Liveness failure
```

After repeated failures:

```text
Liveness failure
     ↓
Container restart
```

### Root Cause

Incorrect liveness endpoint.

### Fix

Use the correct application health endpoint.

---

# 12. Scenario — Wrong Port

Suppose:

```text
Application → port 8080
```

but:

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 80
```

Kubernetes checks the wrong port.

Possible result:

```text
Connection refused
```

or timeout.

### Troubleshooting

Check:

```bash
kubectl describe pod <pod-name>
```

Then verify:

* Application listening port
* Probe port
* Container configuration
* Application logs

Important:

```yaml
containerPort: 80
```

does **not** force an application to listen on port 80.

It is primarily metadata/documentation for the container port.

---

# 13. Scenario — Application Starts Slowly

Suppose an application requires:

```text
60 seconds
```

to initialize.

But the liveness probe begins checking too early.

Possible flow:

```text
Application starting
       ↓
Liveness probe
       ↓
FAIL
       ↓
Container restart
       ↓
Application starts again
       ↓
FAIL
       ↓
Restart
```

This can eventually produce:

```text
CrashLoopBackOff
```

### Better Solution

Use a startup probe:

```yaml
startupProbe:
  httpGet:
    path: /
    port: 80
  failureThreshold: 12
  periodSeconds: 5
```

This gives approximately:

```text
12 × 5 = 60 seconds
```

for startup.

---

# 14. Scenario — Liveness Probe Too Aggressive

Example:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 2
  timeoutSeconds: 1
  failureThreshold: 1
```

Suppose the application temporarily takes 1.5 seconds to respond.

The probe can fail even though the application is functioning.

Result:

```text
Temporary slowness
       ↓
Probe timeout
       ↓
Liveness failure
       ↓
Container restart
```

Repeated restarts can make the application less stable.

### Production Principle

Don't make liveness more aggressive than the application's normal behavior requires.

---

# 15. Scenario — Dependency Failure

Consider:

```text
Application
     |
     └── PostgreSQL
```

If the database temporarily becomes unavailable and the liveness endpoint directly depends on the database:

```text
Database unavailable
       ↓
Health endpoint fails
       ↓
Liveness fails
       ↓
Application restarted
```

If all replicas behave the same way, this can make the incident worse.

Therefore, carefully distinguish:

```text
Liveness
→ Is the application process itself functioning?

Readiness
→ Can this instance safely receive traffic?
```

Dependency failures often belong in readiness logic, depending on the application's architecture.

---

# 16. Scenario — Application Is Actually Crashing

Not every restart is caused by liveness.

The application itself may crash because of:

* Invalid configuration
* Missing environment variable
* Missing Secret
* Application bug
* Dependency failure
* OOMKilled
* Permission problem

Check:

```bash
kubectl describe pod <pod-name>
```

Look at:

```text
Last State:
Reason:
Exit Code:
```

Then:

```bash
kubectl logs <pod-name> --previous
```

Determine whether:

```text
Application crashed
```

or:

```text
Liveness probe caused restart
```

---

# 17. Important Difference — OOMKilled vs Liveness Failure

Example:

```text
Reason: OOMKilled
Exit Code: 137
```

This means the container exceeded its memory limit and was killed.

Do not incorrectly conclude:

```text
Liveness caused the restart
```

Always inspect:

```text
Reason
Exit Code
Events
```

before deciding on the root cause.

---

# 18. Minimal Container Troubleshooting

During our Nginx lab, we encountered a common container troubleshooting issue.

The minimal Nginx image did not contain:

```text
ps
```

This is normal.

Minimal images often don't contain utilities such as:

```text
ps
curl
netstat
bash
```

Therefore, if:

```bash
kubectl exec <pod> -- ps
```

returns:

```text
command not found
```

it does not automatically indicate an application problem.

Use Kubernetes-native checks first:

```bash
kubectl describe pod <pod>
kubectl logs <pod>
kubectl get events --sort-by=.lastTimestamp
```

---

# 19. Production Troubleshooting Checklist

When restart count is increasing:

```text
[ ] Check kubectl get pods
[ ] Check Restart Count
[ ] Run kubectl describe pod
[ ] Check State
[ ] Check Last State
[ ] Check Reason
[ ] Check Exit Code
[ ] Check Events
[ ] Check liveness configuration
[ ] Check application logs
[ ] Check previous logs
[ ] Verify probe path
[ ] Verify probe port
[ ] Verify timeout
[ ] Verify failureThreshold
[ ] Check startup time
[ ] Check CPU/memory
[ ] Check dependencies
[ ] Determine root cause
[ ] Fix
[ ] Verify restart count stabilizes
```

---

# 20. Production Incident Example

### Symptom

Several application Pods are repeatedly restarting.

```text
Pod A → RESTARTS 15
Pod B → RESTARTS 13
Pod C → RESTARTS 16
```

### Step 1 — Check Pods

```bash
kubectl get pods
```

### Step 2 — Describe one Pod

```bash
kubectl describe pod <pod-name>
```

### Step 3 — Check Events

Look for:

```text
Liveness probe failed
```

### Step 4 — Check logs

```bash
kubectl logs <pod-name>
kubectl logs <pod-name> --previous
```

### Step 5 — Test health endpoint

Verify:

```text
Path
Port
Response
Latency
```

### Step 6 — Check application

Investigate:

```text
CPU
Memory
Database
Redis
Network
Application errors
```

### Step 7 — Determine root cause

For example:

```text
Application became unresponsive because of high memory usage.
```

### Step 8 — Fix the actual problem

Don't simply increase the liveness threshold without understanding the cause.

### Step 9 — Verify

```bash
kubectl get pods
```

Confirm:

```text
READY = 1/1
STATUS = Running
```

and restart count stops increasing.

---

# 21. Common Mistakes

## Mistake 1 — Immediately changing the probe

Bad approach:

```text
Probe failed
    ↓
Increase timeout
    ↓
Problem solved?
```

Better:

```text
Probe failed
    ↓
Find why endpoint failed
    ↓
Check application
    ↓
Check configuration
    ↓
Check resources
    ↓
Then tune probe if necessary
```

---

## Mistake 2 — Treating every restart as a probe failure

Always check:

```bash
kubectl describe pod <pod-name>
```

Look at:

```text
Reason
Exit Code
Events
```

---

## Mistake 3 — Using liveness for every dependency

A temporary database outage should not automatically cause every application container to restart.

---

## Mistake 4 — Making liveness too aggressive

Very short:

```text
timeoutSeconds
periodSeconds
failureThreshold
```

can cause unnecessary restarts.

---

# 22. Interview Questions

### Q1. How do you troubleshoot a Pod with increasing restart count?

```text
kubectl get pods
kubectl describe pod <pod>
kubectl logs <pod>
kubectl logs <pod> --previous
```

Then check:

* Last State
* Reason
* Exit Code
* Events
* Liveness configuration
* Application logs
* Resource usage

---

### Q2. How do you know whether liveness caused the restart?

Check:

```bash
kubectl describe pod <pod-name>
```

and inspect:

```text
Events
Last State
Reason
```

Then correlate with the liveness configuration and application logs.

---

### Q3. What if liveness is failing but the application appears healthy?

Check:

1. Probe path
2. Probe port
3. HTTP response
4. Timeout
5. Failure threshold
6. Application response latency
7. Startup time
8. Application logs

---

### Q4. What if the application is slow during startup?

Use a `startupProbe` so that liveness doesn't restart the container before initialization completes.

---

### Q5. Does liveness failure create a new Pod?

Normally no.

The kubelet restarts the container inside the existing Pod.

---

### Q6. What does increasing Restart Count tell you?

It tells you that the container has restarted. It does not by itself identify the root cause.

---

### Q7. What is the first command you run for repeated restarts?

A good first check is:

```bash
kubectl get pods
```

Then immediately investigate the affected Pod with:

```bash
kubectl describe pod <pod-name>
```

---

# 23. Final Troubleshooting Mindset

The most important lesson from the lab:

```text
Restarting
    ↓
Don't assume
    ↓
Observe
    ↓
Describe
    ↓
Events
    ↓
Logs
    ↓
Previous logs
    ↓
Inspect probe
    ↓
Test application
    ↓
Find root cause
    ↓
Fix
    ↓
Verify
```

### Remember

```text
Readiness
→ Controls traffic

Liveness
→ Controls container recovery

Startup
→ Protects slow startup
```

And:

> **A liveness probe failure is an observation made by Kubernetes, not necessarily the underlying cause of the incident.**


