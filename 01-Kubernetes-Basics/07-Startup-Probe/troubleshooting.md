# Kubernetes Startup Probe — Troubleshooting

## 1. Troubleshooting Objective

When a Pod fails to start because of a startup probe, determine:

```text
Is the application actually starting?
        ↓
Is the probe checking the correct endpoint?
        ↓
Is it checking the correct port?
        ↓
Does the application need more startup time?
        ↓
Is the application itself failing?
```

---

# 2. Standard Troubleshooting Flow

```text
kubectl get pods
        ↓
Check STATUS / READY / RESTARTS
        ↓
kubectl describe pod
        ↓
Check Startup Probe
        ↓
Check Events
        ↓
Check application logs
        ↓
Check previous logs
        ↓
Verify path
        ↓
Verify port
        ↓
Verify startup time
        ↓
Verify timeout/threshold
        ↓
Fix root cause
        ↓
Verify Pod becomes Ready
```

---

# 3. Actual Startup Probe Lab

We created:

```text
Deployment
    |
    └── nginx-startup
             |
             └── Nginx
```

Startup probe:

```yaml
startupProbe:
  httpGet:
    path: /
    port: 80
  failureThreshold: 12
  periodSeconds: 5
```

We also configured:

```text
Readiness Probe
Liveness Probe
```

The Pod successfully became:

```text
1/1 Running
```

This confirmed the startup probe configuration was valid.

---

# 4. Startup Probe Failure — What It Means

Suppose:

```text
Startup probe failed
```

This means Kubernetes has not yet determined that the application has successfully started.

It does **not automatically mean that the application is permanently broken**.

Possible causes:

```text
Wrong path
Wrong port
Slow startup
Application crash
Dependency problem
Timeout too short
Failure threshold too low
```

---

# 5. Scenario — Wrong Startup Path

Suppose:

```yaml
startupProbe:
  httpGet:
    path: /does-not-exist
    port: 80
```

Nginx returns:

```text
HTTP 404
```

Flow:

```text
GET /does-not-exist
        ↓
HTTP 404
        ↓
Startup probe fails
        ↓
Application never reaches successful startup state
```

### Troubleshooting

```bash
kubectl describe pod <pod-name>
```

Check Events.

Then test the application endpoint.

If:

```text
/
```

returns HTTP 200, but:

```text
/does-not-exist
```

returns HTTP 404, the probe path is incorrect.

### Root Cause

Incorrect startup probe path.

### Fix

Use the correct endpoint.

---

# 6. Scenario — Wrong Startup Port

Application:

```text
Listening on 8080
```

Probe:

```yaml
startupProbe:
  httpGet:
    path: /
    port: 80
```

Result:

```text
Connection refused
```

or:

```text
Timeout
```

### Troubleshooting

Run:

```bash
kubectl describe pod <pod-name>
```

Verify:

```text
Startup probe port
Application listening port
```

The probe port must match the port where the application is actually listening.

---

# 7. Scenario — Startup Takes Longer Than Expected

Suppose:

```text
Application startup = 120 seconds
```

Configuration:

```yaml
failureThreshold: 12
periodSeconds: 5
```

Approximate startup window:

```text
12 × 5 = 60 seconds
```

The application may not become healthy before the startup window expires.

Possible result:

```text
Startup probe fails
       ↓
Container restart
       ↓
Application starts again
       ↓
Startup fails again
```

Eventually:

```text
CrashLoopBackOff
```

---

# 8. Fixing Slow Startup

Increase the startup window based on actual application behavior.

For example:

```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 10
  failureThreshold: 18
```

Approximate window:

```text
18 × 10 = 180 seconds
```

Do not blindly increase the values.

First measure actual startup time.

---

# 9. Scenario — Application Is Actually Crashing

A startup probe may be completely correct while the application itself is broken.

Example:

```text
Container starts
      ↓
Application initialization
      ↓
Missing environment variable
      ↓
Application exits
      ↓
Startup probe cannot succeed
```

Check:

```bash
kubectl logs <pod-name>
```

and:

```bash
kubectl describe pod <pod-name>
```

Look at:

```text
State
Last State
Reason
Exit Code
Events
```

The root cause may be an application configuration issue rather than the startup probe.

---

# 10. Scenario — Startup Probe and Liveness Conflict

Suppose:

```text
Application startup = 90 seconds
```

and:

```text
Liveness starts too early
```

Without startup protection:

```text
Application starting
      ↓
Liveness fails
      ↓
Container restarted
      ↓
Application starts again
      ↓
Liveness fails
```

With startup probe:

```text
Application starting
      ↓
Startup probe
      ↓
Wait
      ↓
Startup succeeds
      ↓
Liveness begins
```

This is the primary reason startup probes are useful.

---

# 11. Scenario — Startup Probe Keeps Failing

Run:

```bash
kubectl get pods
```

Then:

```bash
kubectl describe pod <pod-name>
```

Look for:

```text
Startup probe failed
```

Then:

```bash
kubectl logs <pod-name>
```

If the container restarted:

```bash
kubectl logs <pod-name> --previous
```

Check:

```text
Application startup error
```

Then verify:

```text
Probe path
Probe port
Startup time
Timeout
Failure threshold
Application dependencies
```

---

# 12. How to Test the Endpoint

If the container contains an HTTP client such as `curl` or `wget`, you can test from inside the container.

Example:

```bash
kubectl exec -it <pod-name> -- /bin/sh
```

Then:

```bash
wget -S -O - http://127.0.0.1:80/
```

For images that do not contain diagnostic tools, don't assume the application is broken.

Use:

```bash
kubectl describe pod
kubectl logs
kubectl get events
```

or an appropriate debugging container/tool.

---

# 13. Scenario — Probe Timeout

Suppose:

```yaml
timeoutSeconds: 1
```

but the application's startup endpoint takes two seconds to respond.

Result:

```text
1 second
   ↓
Timeout
   ↓
Probe failure
```

### Fix

Tune the timeout based on actual application response behavior.

For example:

```yaml
timeoutSeconds: 3
```

But investigate why the endpoint is slow before simply increasing the timeout.

---

# 14. Scenario — Failure Threshold Too Low

Example:

```yaml
failureThreshold: 1
```

One temporary failure causes startup to be considered failed immediately.

Potential flow:

```text
Temporary startup delay
       ↓
One probe failure
       ↓
Startup failure
       ↓
Restart
```

A suitable threshold should account for expected startup behavior.

---

# 15. Scenario — Startup Endpoint Is Not Appropriate

Suppose the application exposes:

```text
/health
```

but that endpoint depends on a database that is not available during initial application startup.

The startup probe may fail even though the application process itself is initializing correctly.

Consider whether the startup endpoint represents the correct startup condition.

Separate health endpoints can sometimes be useful:

```text
/health/startup
/health/ready
/health/live
```

The exact implementation depends on the application.

---

# 16. Troubleshooting Commands

### Check Pods

```bash
kubectl get pods
```

### Watch startup

```bash
kubectl get pods -w
```

### Describe Pod

```bash
kubectl describe pod <pod-name>
```

### Logs

```bash
kubectl logs <pod-name>
```

### Previous logs

```bash
kubectl logs <pod-name> --previous
```

### Events

```bash
kubectl get events --sort-by=.lastTimestamp
```

### Deployment

```bash
kubectl describe deployment nginx-startup
```

---

# 17. Production Troubleshooting Checklist

```text
[ ] Check Pod status
[ ] Check READY count
[ ] Check restart count
[ ] Check startup probe configuration
[ ] Check probe path
[ ] Check probe port
[ ] Check timeout
[ ] Check failureThreshold
[ ] Check initialDelaySeconds if configured
[ ] Check application logs
[ ] Check previous container logs
[ ] Check Events
[ ] Check actual application startup time
[ ] Check application dependencies
[ ] Check CPU/memory
[ ] Check whether the application is crashing
[ ] Fix root cause
[ ] Verify startup succeeds
[ ] Verify readiness
[ ] Verify liveness
```

---

# 18. Production Incident Example

### Symptom

Application Pods repeatedly restart during deployment.

```text
Pod A → Restarting
Pod B → Restarting
Pod C → Starting
```

### Step 1

```bash
kubectl get pods
```

### Step 2

```bash
kubectl describe pod <pod-name>
```

Events show:

```text
Startup probe failed
```

### Step 3

Check logs:

```bash
kubectl logs <pod-name>
kubectl logs <pod-name> --previous
```

### Step 4

Application logs show:

```text
Application initialization takes approximately 100 seconds
```

### Step 5

Current startup configuration allows only:

```text
60 seconds
```

### Root Cause

Startup probe window is shorter than the application's actual startup time.

### Fix

Tune the startup probe based on measured startup behavior.

### Verification

```bash
kubectl get pods
```

Confirm:

```text
READY   STATUS
1/1     Running
```

and restart count remains stable.

---

# 19. Important Diagnostic Principle

Do not automatically conclude:

```text
Startup probe failed
        ↓
Increase failureThreshold
```

Instead:

```text
Startup probe failed
        ↓
Why?
        ↓
Wrong endpoint?
Wrong port?
Application crash?
Slow startup?
Dependency?
Timeout?
Configuration?
        ↓
Fix actual cause
```

---

# 20. Interview Scenario

### Question

**A newly deployed application is repeatedly restarting and Events show startup probe failures. How do you troubleshoot it?**

Answer:

> I first check the Pod with `kubectl describe pod` and review the Events. Then I check application logs and previous container logs to determine whether the application itself is failing during initialization. I verify the startup probe path, port, timeout and failure threshold against the actual application. I also measure the application's startup time. If the application is healthy but takes longer to initialize than the configured startup window, I tune the startup probe appropriately. I then verify that startup succeeds, the Pod becomes Ready, and the restart count stabilizes.

---

# 21. Interview Scenario

### Question

**Why would you use a startup probe instead of only increasing `initialDelaySeconds` on liveness?**

Answer:

> A startup probe explicitly separates the application startup phase from ongoing health monitoring. It is more appropriate when startup can be slow or variable because liveness does not need to begin evaluating the application until startup succeeds.

---

# 22. Interview Scenario

### Question

**Startup probe keeps failing but the application process is running. What would you check?**

Check:

```text
1. HTTP path
2. Port
3. Application response
4. Startup endpoint
5. Response time
6. Timeout
7. Failure threshold
8. Application logs
9. Dependencies
10. Actual startup duration
```

---

# 23. Key Lessons

```text
Startup Probe
      ↓
Protects slow startup
      ↓
Startup succeeds
      ↓
Readiness + Liveness take over
```

Remember:

```text
Startup
→ Has it started?

Readiness
→ Can it receive traffic?

Liveness
→ Is it still healthy?
```

Most important commands:

```bash
kubectl get pods
kubectl describe pod <pod>
kubectl logs <pod>
kubectl logs <pod> --previous
kubectl get events --sort-by=.lastTimestamp
```

Most important production principle:

> **Don't use a startup probe to hide a broken application. Use it to give a healthy but slow-starting application enough time to initialize.**

