# Kubernetes Liveness Probe

## 1. What is a Liveness Probe?

A liveness probe is a Kubernetes health check used to determine whether an application inside a container is still functioning.

The basic question is:

> **"Is the application still alive and should Kubernetes continue running this container?"**

If the liveness probe repeatedly fails, Kubernetes restarts the container.

```text
Application
     |
     v
Liveness Probe
     |
     +---- Success → Continue running
     |
     +---- Repeated failure
                |
                v
        Container restarted
```

---

# 2. Why is Liveness Required?

A container can be `Running` while the application inside it is unhealthy.

For example:

```text
Container process
      ↓
Still running
      ↓
Application thread deadlocked
      ↓
Application not responding
```

From the operating system's perspective:

```text
Process = Running
```

But from the application's perspective:

```text
Application = Unhealthy
```

A liveness probe allows Kubernetes to detect this condition and recover automatically.

---

# 3. Real Production Example

Consider an API application:

```text
Order API
    |
    +--- Database
    |
    +--- Redis
    |
    +--- External APIs
```

The application starts successfully:

```text
Healthy
   ↓
Running for several hours
   ↓
Application thread becomes stuck
   ↓
API stops responding
   ↓
Container process still exists
```

Without liveness:

```text
Users
  ↓
Application
  ↓
Requests fail
```

With liveness:

```text
Users
  ↓
Application unhealthy
  ↓
Liveness probe fails
  ↓
Kubernetes restarts container
  ↓
Application initializes
  ↓
Service recovers
```

---

# 4. Basic Liveness Probe

Example:

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 5
```

This means:

```text
Wait 5 seconds
     ↓
Check /
     ↓
Port 80
     ↓
Repeat every 5 seconds
```

If the check repeatedly fails, Kubernetes restarts the container.

---

# 5. HTTP Liveness Probe

For HTTP applications:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
```

Kubernetes performs an HTTP request:

```text
GET /health
```

If the application returns an appropriate successful response:

```text
Probe = Success
```

If the endpoint repeatedly fails:

```text
Probe = Failure
        ↓
Container restart
```

---

# 6. TCP Liveness Probe

A TCP probe checks whether a connection can be established to a port.

```yaml
livenessProbe:
  tcpSocket:
    port: 8080
  periodSeconds: 10
```

Flow:

```text
Kubernetes
     |
     v
TCP :8080
     |
     +---- Connection succeeds → Healthy
     |
     +---- Connection fails → Probe failure
```

Important:

TCP only verifies connectivity to the port.

It does not necessarily prove that the application is functioning correctly.

---

# 7. Exec Liveness Probe

An Exec probe runs a command inside the container.

Example:

```yaml
livenessProbe:
  exec:
    command:
      - cat
      - /tmp/healthy
```

If the command exits with:

```text
exit code 0
```

the probe succeeds.

If the command exits with:

```text
non-zero exit code
```

the probe fails.

---

# 8. Important Liveness Parameters

## `initialDelaySeconds`

Time before the first liveness check.

```yaml
initialDelaySeconds: 10
```

Flow:

```text
Container starts
      ↓
Wait 10 seconds
      ↓
First liveness check
```

---

## `periodSeconds`

Frequency of checks.

```yaml
periodSeconds: 5
```

Means approximately every five seconds.

---

## `timeoutSeconds`

Maximum time allowed for a probe response.

```yaml
timeoutSeconds: 2
```

If the probe does not respond within the timeout, it is considered failed.

---

## `failureThreshold`

Number of consecutive failures before Kubernetes takes action.

```yaml
failureThreshold: 3
```

Conceptually:

```text
Failure 1
Failure 2
Failure 3
   ↓
Threshold reached
   ↓
Container restarted
```

---

## `successThreshold`

Number of consecutive successful checks required for success.

For liveness probes, this is normally `1`.

---

# 9. Complete Liveness Example

```yaml
apiVersion: apps/v1
kind: Deployment

metadata:
  name: nginx-liveness

spec:
  replicas: 1

  selector:
    matchLabels:
      app: nginx-liveness

  template:
    metadata:
      labels:
        app: nginx-liveness

    spec:
      containers:
        - name: nginx
          image: nginx:1.29

          ports:
            - containerPort: 80

          livenessProbe:
            httpGet:
              path: /
              port: 80

            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
```

---

# 10. Our Actual Liveness Lab

We created:

```text
Deployment
    |
    └── nginx-liveness
             |
             └── Nginx container
```

The probe was:

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 5
```

The initial Pod state was:

```text
READY   STATUS    RESTARTS
1/1     Running   0
```

This confirmed:

```text
Container running
Application responding
Liveness probe succeeding
```

---

# 11. Intentionally Breaking the Application

To test liveness recovery, we intentionally stopped Nginx inside the container:

```bash
kubectl exec <pod-name> -- nginx -s stop
```

Nginx stopped responding.

The liveness probe then began failing.

Kubernetes detected the failure and restarted the container.

The restart count changed:

```text
0 → 1
```

---

# 12. What We Learned From the Lab

The important observation was:

```text
Pod did NOT need to be recreated
```

Instead:

```text
Same Pod
    |
    +--- Same Pod name
    |
    +--- Same Pod IP
    |
    +--- Container restarted
    |
    +--- Restart Count increased
```

This is a very important Kubernetes concept.

---

# 13. Container Restart vs Pod Recreation

### Container restart

```text
Pod
 |
 └── Container
       ↓
     Restart
```

The Pod remains.

### Pod recreation

```text
Old Pod
   ↓
Deleted
   ↓
New Pod
```

The new Pod can have:

* New Pod name
* New Pod IP
* New container instance

A liveness failure normally causes a **container restart**, not a new Pod.

---

# 14. How Liveness Works Internally

The kubelet on the worker node performs the health check.

Simplified flow:

```text
Kubernetes API
      |
      v
Pod scheduled to node
      |
      v
Kubelet
      |
      v
Liveness Probe
      |
      v
Container
      |
      +---- Healthy
      |
      +---- Repeated failure
                  |
                  v
          Container restarted
```

The kubelet is responsible for managing the container lifecycle on the node.

---

# 15. Liveness and Deployment

Suppose:

```text
Deployment
    |
    └── ReplicaSet
           |
           └── Pod
                 |
                 └── Container
```

If the liveness probe fails:

```text
Container restarted
```

The Deployment does not necessarily create another Pod because the Pod itself still exists.

The Deployment/ReplicaSet maintains the desired number of Pods.

---

# 16. Liveness vs Readiness

This distinction is critical.

| Feature             | Readiness               | Liveness                   |
| ------------------- | ----------------------- | -------------------------- |
| Main question       | Can it receive traffic? | Is it still healthy?       |
| Failure effect      | Pod becomes NotReady    | Container restarted        |
| Traffic removed     | Yes                     | During restart/unavailable |
| Container restarted | No                      | Yes                        |
| Primary purpose     | Traffic control         | Recovery                   |

Memory trick:

```text
Readiness → Traffic
Liveness  → Restart
```

---

# 17. Liveness vs Startup

| Feature          | Startup                   | Liveness                      |
| ---------------- | ------------------------- | ----------------------------- |
| Purpose          | Detect successful startup | Detect ongoing health         |
| Main question    | Has application started?  | Is application still healthy? |
| Used mainly for  | Slow startup              | Runtime failures              |
| Protects against | Premature restarts        | Hung/unhealthy application    |

Typical flow:

```text
Container starts
      ↓
Startup Probe
      ↓
Startup succeeds
      ↓
Liveness starts controlling health
```

---

# 18. When NOT to Use an Aggressive Liveness Probe

Suppose an application temporarily becomes slow because of:

```text
High CPU
Database latency
Garbage collection
Temporary network issue
```

An overly aggressive liveness probe may do this:

```text
Temporary slowness
       ↓
Liveness fails
       ↓
Restart
       ↓
Application starts again
       ↓
Still under load
       ↓
Liveness fails
       ↓
Restart again
```

This can create a restart loop.

Therefore:

> Liveness should identify genuine application failure, not normal temporary slowness.

---

# 19. Good Liveness Endpoint

A liveness endpoint should generally answer:

```text
"Is this application process capable of serving requests?"
```

Example:

```text
GET /health/live
```

Avoid making liveness depend on every external dependency.

For example:

```text
Application
    |
    +--- Database
    +--- Redis
    +--- External API
```

If the database temporarily becomes unavailable, blindly failing liveness could restart every application instance.

Depending on architecture, readiness may be more appropriate for dependency availability.

---

# 20. Useful Commands

### Check Pods

```bash
kubectl get pods
```

### Watch Pods

```bash
kubectl get pods -w
```

### Describe Pod

```bash
kubectl describe pod <pod-name>
```

### Check logs

```bash
kubectl logs <pod-name>
```

### Check previous container logs

```bash
kubectl logs <pod-name> --previous
```

### Execute command

```bash
kubectl exec <pod-name> -- nginx -s stop
```

### Check Deployment

```bash
kubectl get deployment
```

### Check events

```bash
kubectl get events --sort-by=.lastTimestamp
```

---

# 21. One-Minute Interview Explanation

> A liveness probe is used to determine whether an application inside a container is still healthy. If the liveness probe repeatedly fails, the kubelet restarts the container. In my lab, I deployed Nginx with an HTTP liveness probe on port 80. Initially the Pod was `1/1 Running` with restart count zero. I intentionally stopped Nginx using `kubectl exec`, which caused the health check to fail. Kubernetes automatically restarted the container and the restart count increased. The Pod itself remained the same, which demonstrates the difference between a container restart and Pod recreation. In production, I would make the liveness probe specific to genuine application failure and avoid overly aggressive checks that can cause unnecessary restart loops.

