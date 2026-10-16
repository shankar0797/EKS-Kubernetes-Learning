# Kubernetes Probes

## 1. What are Kubernetes Probes?

Kubernetes probes are health checks used by the kubelet to determine the state of an application container.

Kubernetes provides three main probes:

| Probe           | Main Question                             | Failure Action                        |
| --------------- | ----------------------------------------- | ------------------------------------- |
| Startup Probe   | Has the application started successfully? | Container can be restarted            |
| Readiness Probe | Can the application receive traffic?      | Pod is removed from Service endpoints |
| Liveness Probe  | Is the application still healthy/alive?   | Container is restarted                |

### Simple memory trick

```text
Startup   → "Has it started?"
Readiness → "Can it receive traffic?"
Liveness  → "Is it still alive?"
```

---

# 2. Why are probes required?

A container being `Running` does not necessarily mean that the application inside it is healthy.

Example:

```text
Container Running
       ↓
Application still starting
       ↓
Application not ready
       ↓
Traffic arrives
       ↓
Users receive errors
```

With probes:

```text
Container starts
       ↓
Startup Probe
       ↓
Application initialized
       ↓
Readiness Probe succeeds
       ↓
Traffic allowed
       ↓
Liveness continuously checks application
```

Probes are especially important in production environments where applications may:

* Take time to start
* Depend on databases
* Depend on external services
* Become temporarily unavailable
* Hang without the process actually stopping
* Require automatic recovery

---

# 3. Startup Probe

## Purpose

Startup probe determines whether an application has successfully started.

Example:

```yaml
startupProbe:
  httpGet:
    path: /
    port: 80
  failureThreshold: 12
  periodSeconds: 5
```

This allows approximately:

```text
12 × 5 = 60 seconds
```

for the application to start before the startup probe considers it failed.

## Why use it?

Consider a slow-starting application:

```text
Container starts
      ↓
JVM initialization
      ↓
Load configuration
      ↓
Database initialization
      ↓
Cache initialization
      ↓
Application ready
```

Without a startup probe, an aggressive liveness probe could restart the application before it finishes starting.

With startup probe:

```text
Startup Probe
      ↓
Wait for application startup
      ↓
Startup succeeds
      ↓
Liveness/Readiness take effect
```

---

# 4. Readiness Probe

## Purpose

Readiness determines whether the Pod should receive traffic.

Example:

```yaml
readinessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 5
```

If the probe succeeds:

```text
Pod → Ready
```

If it fails:

```text
Pod → NotReady
```

The container is normally **not restarted** because of a readiness failure.

Instead, when the Pod is behind a Service, Kubernetes removes the Pod from the Service's ready endpoints.

### Example

```text
              Service
                 |
        -------------------
        |        |        |
       Pod A    Pod B    Pod C
       Ready    Ready    NotReady
        |        |         X
        |        |       Traffic
        |        |
      Traffic  Traffic
```

---

# 5. Liveness Probe

## Purpose

Liveness determines whether the application is still functioning.

Example:

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 5
```

If the application repeatedly fails its liveness probe:

```text
Liveness failure
       ↓
Kubelet restarts container
```

Example scenario:

```text
Application starts
       ↓
Healthy
       ↓
Application hangs
       ↓
Liveness probe fails
       ↓
Container restarted
       ↓
Application recovers
```

---

# 6. Startup vs Readiness vs Liveness

This is one of the most important Kubernetes interview topics.

```text
                    Pod starts
                       |
                       v
                +--------------+
                |   STARTUP    |
                |    PROBE     |
                +------+-------+
                       |
                  Startup OK
                       |
             +---------+---------+
             |                   |
             v                   v
       +-----------+       +-----------+
       | READINESS |       | LIVENESS  |
       |   PROBE   |       |   PROBE   |
       +-----+-----+       +-----+-----+
             |                   |
             v                   v
       Traffic decision      Restart decision
```

### Startup

```text
Has application started?
```

### Readiness

```text
Should traffic be sent to this Pod?
```

### Liveness

```text
Should this container be restarted?
```

---

# 7. Probe Types

Kubernetes supports different mechanisms for performing health checks.

## HTTP GET

Common for web applications.

```yaml
httpGet:
  path: /health
  port: 8080
```

Kubernetes sends an HTTP request to the application.

A successful HTTP response generally indicates a successful probe.

Example:

```text
GET /health
       ↓
HTTP 200
       ↓
Probe successful
```

---

## TCP Socket

Checks whether a TCP connection can be established.

```yaml
tcpSocket:
  port: 8080
```

Useful when the application does not expose an HTTP health endpoint.

Important:

```text
TCP connection successful
```

does not necessarily mean:

```text
Application is fully healthy
```

It only proves that something is accepting the TCP connection.

---

## Exec

Runs a command inside the container.

Example:

```yaml
exec:
  command:
    - cat
    - /tmp/healthy
```

If the command exits with code `0`:

```text
Probe successful
```

If it exits with a non-zero code:

```text
Probe failed
```

---

# 8. Important Probe Parameters

## `initialDelaySeconds`

Time to wait before the first probe.

```yaml
initialDelaySeconds: 10
```

Flow:

```text
Container starts
       ↓
Wait 10 seconds
       ↓
First probe
```

---

## `periodSeconds`

How frequently the probe runs.

```yaml
periodSeconds: 5
```

Means approximately:

```text
Check every 5 seconds
```

---

## `timeoutSeconds`

How long Kubernetes waits for a probe response.

```yaml
timeoutSeconds: 2
```

If the application doesn't respond within the timeout, the probe fails.

---

## `failureThreshold`

Number of consecutive failures before the probe is considered failed.

```yaml
failureThreshold: 3
```

Conceptually:

```text
FAIL
FAIL
FAIL
 ↓
Threshold reached
 ↓
Failure action
```

---

## `successThreshold`

Number of consecutive successful probes required to consider the probe successful.

```yaml
successThreshold: 1
```

For example:

```text
PASS
PASS
 ↓
Ready
```

---

# 9. Complete Probe Example

Example Deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3

  selector:
    matchLabels:
      app: web-app

  template:
    metadata:
      labels:
        app: web-app

    spec:
      containers:
        - name: nginx
          image: nginx:1.29

          ports:
            - containerPort: 80

          startupProbe:
            httpGet:
              path: /
              port: 80
            failureThreshold: 12
            periodSeconds: 5

          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5

          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
```

---

# 10. Commands Used in the Probe Lab

## Apply Deployment

```bash
kubectl apply -f readiness-deployment.yaml
```

## Check Pods

```bash
kubectl get pods
```

## Detailed Pod information

```bash
kubectl describe pod <pod-name>
```

## Check logs

```bash
kubectl logs <pod-name>
```

## Check previous container logs

```bash
kubectl logs <pod-name> --previous
```

## Execute command inside Pod

```bash
kubectl exec -it <pod-name> -- /bin/sh
```

## Check probe configuration

```bash
kubectl describe pod <pod-name>
```

Look for:

```text
Readiness:
Liveness:
Startup:
```

## Check restart count

```bash
kubectl get pods
```

Example:

```text
NAME                  READY   STATUS    RESTARTS
nginx-liveness-xxx    1/1     Running   1
```

---

# 11. Actual Readiness Probe Lab

We created an Nginx Deployment with:

```yaml
readinessProbe:
  httpGet:
    path: /
    port: 80
```

The probe initially worked.

We intentionally changed the path to:

```yaml
path: /does-not-exist
```

Nginx returned:

```text
HTTP 404
```

Kubernetes therefore reported:

```text
Readiness probe failed:
HTTP probe failed with statuscode: 404
```

The Pod showed:

```text
0/1 Running
```

Important:

```text
Running ≠ Ready
```

The container itself was still running.

---

# 12. How we diagnosed the Readiness failure

First:

```bash
kubectl get pods
```

Observed:

```text
0/1 Running
```

Then:

```bash
kubectl describe pod <pod-name>
```

We checked the Events section.

Found:

```text
Readiness probe failed:
HTTP probe failed with statuscode: 404
```

Then tested the application endpoint.

The root endpoint:

```text
/
```

returned:

```text
HTTP 200
```

The incorrect endpoint:

```text
/does-not-exist
```

returned:

```text
HTTP 404
```

Root cause:

```text
Incorrect readinessProbe path
```

Fix:

```yaml
readinessProbe:
  httpGet:
    path: /
    port: 80
```

After fixing:

```text
Pod → 1/1 Running
```

---

# 13. Actual Liveness Probe Lab

We created an Nginx Deployment with:

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 80
```

The Pod initially showed:

```text
READY   STATUS    RESTARTS
1/1     Running   0
```

We intentionally stopped Nginx:

```bash
kubectl exec <pod-name> -- nginx -s stop
```

The liveness probe then failed.

Kubernetes restarted the container.

The restart count changed:

```text
0 → 1
```

Important observation:

```text
Pod name remained the same
Pod IP remained the same
Container restarted
Restart Count increased
```

This demonstrates the difference between:

```text
Container restart
```

and:

```text
Pod recreation
```

---

# 14. Actual Startup Probe Lab

We created a Deployment containing:

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

We also configured readiness and liveness probes.

The important flow is:

```text
Container starts
      ↓
Startup probe checks application
      ↓
Startup succeeds
      ↓
Readiness determines traffic eligibility
      ↓
Liveness monitors ongoing health
```

---

# 15. Important Difference: Probe Failure Actions

| Probe     |               Container Restart? |                         Traffic Removed? |
| --------- | -------------------------------: | ---------------------------------------: |
| Startup   | Yes, if startup ultimately fails |                            Pod not ready |
| Readiness |                               No |                                      Yes |
| Liveness  |                              Yes | Pod becomes unavailable while restarting |

The most important interview answer:

> **Readiness controls traffic; liveness controls restart; startup protects slow application startup.**

---

# 16. Probe Troubleshooting Flow

When a Pod is not becoming Ready:

```text
kubectl get pods
        ↓
READY = 0/1?
        ↓
kubectl describe pod
        ↓
Check probe configuration
        ↓
Check Events
        ↓
Check application logs
        ↓
Check endpoint manually
        ↓
Verify port
        ↓
Verify path
        ↓
Verify application is listening
        ↓
Fix probe/application
        ↓
Verify Ready
```

For liveness failures:

```text
kubectl get pods
        ↓
Restart count increasing?
        ↓
kubectl describe pod
        ↓
Check Last State
        ↓
Check Events
        ↓
Check logs
        ↓
Check probe configuration
        ↓
Determine why health check fails
        ↓
Fix root cause
```

---

# 17. Common Probe Mistakes

### Wrong HTTP path

```yaml
path: /health
```

while the application only exposes:

```text
/
```

Result:

```text
404
```

---

### Wrong port

Application:

```text
8080
```

Probe:

```yaml
port: 80
```

Result:

```text
Connection refused / timeout
```

---

### Probe starts too early

Application takes:

```text
60 seconds
```

but probe starts after:

```text
5 seconds
```

This can cause failures.

Use:

```text
startupProbe
```

or appropriate timing.

---

### Liveness probe too aggressive

If an application temporarily becomes slow:

```text
Liveness fails
       ↓
Container restarted
       ↓
Application starts
       ↓
Still slow
       ↓
Restart again
```

This can create a restart loop.

A liveness probe should detect genuine application failure, not normal temporary slowness.

---

### Readiness used as liveness

Readiness should answer:

```text
Can I receive traffic?
```

It should not automatically be treated as:

```text
Restart me
```

---

# 18. Production Example

Imagine an enterprise order application:

```text
ECS/EKS Application
        |
        +---- Database
        |
        +---- Redis
        |
        +---- External APIs
```

During startup:

```text
Load configuration
      ↓
Connect DB
      ↓
Connect Redis
      ↓
Initialize application
      ↓
Start API
```

Use:

```text
Startup Probe
```

to protect slow startup.

Use:

```text
Readiness Probe
```

to prevent traffic until:

```text
DB connection available
Redis available
Application initialized
```

Use:

```text
Liveness Probe
```

to detect:

```text
Application deadlock
Application process stuck
Unrecoverable application state
```

---

# 19. Interview Q&A

### Q1. What are Kubernetes probes?

Probes are health checks used by Kubernetes to determine the state of a container/application.

---

### Q2. What are the three main probes?

Startup, Readiness, and Liveness.

---

### Q3. Difference between readiness and liveness?

Readiness determines whether traffic should be sent to the Pod.

Liveness determines whether the container should be restarted.

---

### Q4. Does readiness failure restart the container?

No.

The Pod becomes NotReady and is removed from the Service's ready endpoints.

---

### Q5. What happens when liveness fails?

After the configured failure threshold, Kubernetes restarts the container.

---

### Q6. Why do we need startup probes?

To protect slow-starting applications from being restarted by liveness checks before initialization completes.

---

### Q7. Can we use startup, readiness and liveness together?

Yes. This is common for applications that have slow startup and need both traffic management and ongoing health monitoring.

---

### Q8. What happens if readiness probe returns HTTP 404?

The readiness probe fails and the Pod becomes NotReady.

---

### Q9. What does `0/1 Running` mean?

The container is running, but the Pod is not Ready.

---

### Q10. What does `1/1 Running` mean?

The container is running and Ready.

---

### Q11. What happens if the liveness probe fails?

The kubelet restarts the container according to the probe configuration.

---

### Q12. What is `initialDelaySeconds`?

The delay before Kubernetes performs the first probe.

---

### Q13. What is `periodSeconds`?

The interval between probe checks.

---

### Q14. What is `failureThreshold`?

The number of consecutive failures required before Kubernetes considers the probe failed.

---

### Q15. What is `timeoutSeconds`?

The maximum time Kubernetes waits for a probe response.

---

### Q16. What are common probe types?

HTTP, TCP socket, and Exec.

---

### Q17. When would you use TCP probe?

When you need to verify that an application is accepting TCP connections but don't have a suitable HTTP health endpoint.

---

### Q18. When would you use Exec probe?

When health can be determined using a command inside the container.

---

### Q19. How do you troubleshoot a failed readiness probe?

```bash
kubectl get pods
kubectl describe pod <pod>
kubectl logs <pod>
```

Then check:

* Probe path
* Port
* Application status
* Events
* Endpoint response

---

### Q20. How do you troubleshoot increasing restart counts?

Check:

```bash
kubectl describe pod <pod>
kubectl logs <pod>
kubectl logs <pod> --previous
```

Then inspect:

* Liveness probe
* Application logs
* Exit code
* Last State
* Events
* Resources

---

### Q21. Does a failed liveness probe create a new Pod?

Normally the kubelet restarts the container within the existing Pod. A container restart is different from Pod recreation.

---

### Q22. Why shouldn't liveness probes be too aggressive?

Because temporary slowness can cause unnecessary restarts and potentially create a restart loop.

---

### Q23. What is the most important difference between probes?

```text
Startup   → Startup protection
Readiness → Traffic control
Liveness  → Recovery/restart
```

---

# 20. One-Minute Interview Explanation

> Kubernetes probes are health checks used to monitor application containers. We have three main probes: startup, readiness, and liveness. Startup is useful for slow-starting applications and prevents liveness from restarting the container during initialization. Readiness determines whether the Pod should receive traffic; if readiness fails, the container normally continues running but the Pod is removed from the Service's ready endpoints. Liveness checks whether the application is still healthy and can restart the container when it repeatedly fails. In my lab, I intentionally configured an incorrect readiness endpoint, received HTTP 404 probe failures, diagnosed it using `kubectl describe pod` and Events, corrected the endpoint, and verified the Pod became Ready. I also tested liveness by stopping Nginx and observed the container restart count increase.

