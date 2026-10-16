# Kubernetes CrashLoopBackOff

## 1. What is CrashLoopBackOff?

`CrashLoopBackOff` means Kubernetes is repeatedly starting a container, the container is failing, and Kubernetes is progressively waiting longer before restarting it again.

The important point:

> **CrashLoopBackOff is usually a symptom, not the root cause.**

Example:

```text
Application starts
      ↓
Application crashes
      ↓
Kubernetes restarts container
      ↓
Application crashes again
      ↓
Repeated failures
      ↓
Backoff increases
      ↓
CrashLoopBackOff
```

---

# 2. Simple Mental Model

Remember:

```text
Crash
  ↓
Restart
  ↓
Crash
  ↓
Restart
  ↓
Repeated failures
  ↓
Backoff
  ↓
CrashLoopBackOff
```

Therefore, don't ask:

> "How do I fix CrashLoopBackOff?"

Ask:

> **"Why is the container crashing?"**

---

# 3. Common Root Causes

A container can enter CrashLoopBackOff because of:

```text
Application crash
Incorrect command
Incorrect arguments
Missing environment variable
Wrong ConfigMap
Missing Secret
Bad configuration
Permission denied
Dependency unavailable
Liveness probe failure
OOMKilled
Application bug
Incorrect image behavior
```

---

# 4. CrashLoopBackOff vs Other Pod States

| Status                     | Meaning                         | First Investigation  |
| -------------------------- | ------------------------------- | -------------------- |
| Pending                    | Pod not scheduled/started       | `describe` + Events  |
| ContainerCreating          | Container setup in progress     | `describe`           |
| CreateContainerConfigError | Container configuration problem | Events               |
| ErrImagePull               | Image cannot be pulled          | Events               |
| ImagePullBackOff           | Repeated image pull failure     | Events               |
| CrashLoopBackOff           | Container repeatedly crashes    | Logs + describe      |
| Running 0/1                | Running but not Ready           | Readiness            |
| Running 1/1                | Running and Ready               | Normal               |
| OOMKilled                  | Container exceeded memory limit | Resources + describe |

Important distinction:

```text
CreateContainerConfigError
→ Container never started

CrashLoopBackOff
→ Container started and repeatedly failed
```

---

# 5. Standard CrashLoop Troubleshooting Flow

Use this sequence:

```text
kubectl get pods
       ↓
kubectl describe pod
       ↓
Check State / Last State
       ↓
Check Reason / Exit Code
       ↓
Check Events
       ↓
kubectl logs
       ↓
kubectl logs --previous
       ↓
Inspect command/image/env/config/secret
       ↓
Check probes
       ↓
Check resources
       ↓
Check dependencies
       ↓
Find root cause
       ↓
Fix
       ↓
Verify stable Pod
```

---

# 6. Step 1 — Check Pods

```bash
kubectl get pods
```

Example:

```text
NAME              READY   STATUS             RESTARTS
crashloop-demo    0/1     CrashLoopBackOff   5
```

Important information:

```text
READY
STATUS
RESTARTS
```

A high restart count is a strong indication that the container is repeatedly failing.

---

# 7. Step 2 — Describe the Pod

```bash
kubectl describe pod <pod-name>
```

Check:

```text
State
Last State
Reason
Exit Code
Restart Count
Events
```

Example:

```text
State:
  Waiting
  Reason: CrashLoopBackOff

Last State:
  Terminated
  Reason: Error
  Exit Code: 1

Restart Count: 5
```

This tells us that the container previously started, terminated with an error, and Kubernetes is backing off before restarting it.

---

# 8. Step 3 — Check Logs

```bash
kubectl logs <pod-name>
```

Application logs often reveal the actual root cause.

Example:

```text
Application starting...
ERROR: DATABASE_URL is not configured
```

This is much more useful than simply seeing:

```text
CrashLoopBackOff
```

---

# 9. Step 4 — Check Previous Container Logs

When the container has already restarted:

```bash
kubectl logs <pod-name> --previous
```

This is particularly useful when the previous container instance produced the error before restarting.

Example:

```text
Application starting...
Connecting to database...
ERROR: connection refused
```

---

# 10. Our Basic CrashLoop Lab

We created a Deployment where the container intentionally exited:

```yaml
command:
  - /bin/sh
  - -c
  - "echo 'Application starting...'; exit 1"
```

The container behavior was:

```text
Start
 ↓
Print message
 ↓
exit 1
 ↓
Container terminates
 ↓
Kubernetes restarts
 ↓
exit 1
 ↓
Repeat
```

Eventually:

```text
CrashLoopBackOff
```

---

# 11. Actual Root Cause of Basic CrashLoop

Logs:

```text
Application starting...
```

Container command:

```text
exit 1
```

Therefore:

```text
Root Cause = Application command intentionally exited with status 1
```

The fix was to run Nginx in the foreground:

```yaml
command:
  - /bin/sh
  - -c
  - "echo 'Application started successfully'; nginx -g 'daemon off;'"
```

After fixing:

```text
1/1 Running
```

---

# 12. Exit Codes

Exit codes provide useful troubleshooting information.

Example:

```text
Exit Code: 1
```

Usually indicates a generic application error.

Example:

```text
Exit Code: 137
```

Often indicates SIGKILL (`128 + 9`), and if the reason is `OOMKilled`, the container exceeded its memory limit.

Important:

> Do not identify the root cause from the exit code alone. Always check `Reason`, Events, logs, and resource configuration.

---

# 13. Scenario — Missing Environment Variable

We created:

```yaml
env:
  # DATABASE_URL intentionally missing
```

Application logic checked:

```text
DATABASE_URL
```

and exited if it was absent.

Logs showed:

```text
Application starting...
Checking DATABASE_URL...
ERROR: DATABASE_URL is not configured
```

Root cause:

```text
Required environment variable missing
```

Fix:

```yaml
env:
  - name: DATABASE_URL
    value: "postgresql://db.example.internal:5432/orders"
```

After fixing:

```text
1/1 Running
```

---

# 14. Scenario — Wrong ConfigMap

We created a ConfigMap:

```yaml
DATABASE_HOST: "wrong-database.internal"
```

The application expected:

```text
postgres.database.svc.cluster.local
```

Logs showed:

```text
Application starting...
Environment: production
Database host: wrong-database.internal
Database port: 5432
ERROR: Cannot connect to database at wrong-database.internal
```

Root cause:

```text
Incorrect configuration value
```

Fix:

```yaml
DATABASE_HOST: "postgres.database.svc.cluster.local"
```

Then we restarted the Deployment:

```bash
kubectl rollout restart deployment crash-configmap
```

The new Pod became:

```text
1/1 Running
```

and logs showed:

```text
Database connection successful
```

---

# 15. ConfigMap Environment Variable Important Detail

When a ConfigMap is injected as an environment variable:

```yaml
env:
  - name: DATABASE_HOST
    valueFrom:
      configMapKeyRef:
        name: application-config
        key: DATABASE_HOST
```

the value is loaded when the container starts.

Updating the ConfigMap does not automatically restart an existing container.

Therefore, for environment-variable based configuration, a rollout restart is commonly used:

```bash
kubectl rollout restart deployment <deployment>
```

Mounted ConfigMap files behave differently and can be updated by Kubernetes; the application still needs to reload the configuration if appropriate.

---

# 16. Scenario — Missing Secret

We configured a Deployment to use:

```yaml
secretKeyRef:
  name: database-credentials
```

but intentionally did not create the Secret.

The Pod showed:

```text
CreateContainerConfigError
```

Events showed:

```text
secret "database-credentials" not found
```

Important:

This was **not CrashLoopBackOff**.

Why?

```text
Secret missing
   ↓
Container configuration cannot be created
   ↓
Container never starts
```

Therefore there is no application crash log.

This demonstrates an important troubleshooting distinction.

---

# 17. Fixing the Missing Secret

We created:

```bash
kubectl create secret generic database-credentials \
  --from-literal=username=appuser \
  --from-literal=password='DemoPassword123!'
```

After the required Secret existed, the container could start.

Production note:

> Don't hardcode production credentials in manifests or command history. Use appropriate secret-management solutions such as AWS Secrets Manager with suitable EKS integration.

---

# 18. Scenario — OOMKilled

We created a Python application with:

```yaml
resources:
  requests:
    memory: "32Mi"
  limits:
    memory: "64Mi"
```

The application continuously allocated memory.

Eventually:

```text
State:
  Terminated

Reason:
  OOMKilled

Exit Code:
  137
```

Restart count increased.

---

# 19. Understanding OOMKilled

Flow:

```text
Application
     ↓
Memory usage increases
     ↓
Memory limit reached
     ↓
Kernel kills container
     ↓
Container restarts
     ↓
Application allocates memory again
     ↓
OOMKilled again
```

Eventually:

```text
CrashLoopBackOff
```

Important:

```text
OOMKilled = Root cause
CrashLoopBackOff = Result/symptom
```

Don't simply say:

> "CrashLoopBackOff caused the problem."

The actual problem may be memory exhaustion.

---

# 20. QoS Class From Our OOM Lab

We configured:

```text
requests.memory = 32Mi
limits.memory   = 64Mi
```

Because the request and limit differed, the Pod had:

```text
QoS Class: Burstable
```

This is useful when investigating resource-related incidents.

---

# 21. Scenario — Permission Denied

We configured:

```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 1000
```

The container attempted:

```bash
echo "application configuration" > /etc/config.txt
```

But `/etc` was owned by root:

```text
drwxr-xr-x root root /etc
```

The application received:

```text
Permission denied
```

Root cause:

```text
Non-root user attempted to write to a root-owned directory
```

---

# 22. Important Shell Behavior We Discovered

The script initially did not contain:

```bash
set -e
```

Therefore, after:

```bash
echo "application configuration" > /etc/config.txt
```

failed, the shell continued executing.

The Pod therefore remained:

```text
Running
```

even though the write operation failed.

This is an important troubleshooting lesson:

> A command failure inside a shell script does not necessarily terminate the container.

Using:

```bash
set -e
```

can cause the script to exit when a command fails, depending on shell behavior.

---

# 23. Scenario — Database/Dependency Unavailable

An application may depend on:

```text
Application
     |
     └── PostgreSQL
```

If PostgreSQL is unavailable:

```text
Application starts
     ↓
Attempts DB connection
     ↓
Connection fails
     ↓
Application exits
     ↓
Container restarts
     ↓
Repeated failure
```

Eventually:

```text
CrashLoopBackOff
```

Troubleshooting:

```bash
kubectl describe pod <pod>
kubectl logs <pod>
kubectl get svc
kubectl get pods
```

Then investigate:

```text
Database Service
Service endpoints
DNS
Database Pod
NetworkPolicy
Port
Credentials
Database availability
```

---

# 24. CrashLoopBackOff Does Not Always Mean Application Code Bug

Possible root causes include:

```text
Application bug
Configuration
Environment variable
ConfigMap
Secret
Command
Arguments
Permissions
Memory
Dependency
Probe
Image
Filesystem
```

Therefore:

> Never jump directly to changing the application code.

Start with evidence.

---

# 25. CrashLoopBackOff and Probes

A liveness probe can itself cause repeated container restarts.

Example:

```text
Application healthy
      ↓
Incorrect liveness path
      ↓
HTTP 404
      ↓
Liveness fails
      ↓
Container restarted
      ↓
Starts again
      ↓
Liveness fails again
```

Eventually:

```text
CrashLoopBackOff
```

Therefore, when troubleshooting CrashLoopBackOff, always check probe configuration.

---

# 26. CrashLoopBackOff vs OOMKilled

### CrashLoopBackOff

```text
Repeated container failures
```

### OOMKilled

```text
Container exceeded memory limit
```

Possible relationship:

```text
OOMKilled
   ↓
Container restarts
   ↓
Repeated OOMKilled
   ↓
CrashLoopBackOff
```

So:

```text
OOMKilled = root cause
CrashLoopBackOff = resulting state
```

---

# 27. CrashLoopBackOff vs CreateContainerConfigError

### CreateContainerConfigError

Example:

```text
Secret missing
```

Flow:

```text
Pod
 ↓
Container configuration
 ↓
Missing Secret
 ↓
Container never starts
```

### CrashLoopBackOff

Flow:

```text
Pod
 ↓
Container starts
 ↓
Application fails
 ↓
Container exits
 ↓
Restart
 ↓
Repeated failure
```

This distinction is extremely important.

---

# 28. Production Troubleshooting Decision Tree

```text
Pod unhealthy
     |
     v
kubectl get pods
     |
     +---- Pending
     |       ↓
     |   Scheduling/resources
     |
     +---- ImagePullBackOff
     |       ↓
     |   Image problem
     |
     +---- CreateContainerConfigError
     |       ↓
     |   Secret/Config/container config
     |
     +---- CrashLoopBackOff
             ↓
         describe pod
             ↓
         logs
             ↓
         previous logs
             ↓
       +-----+-----+------+------+
       |     |     |      |      |
      App   Env   Probe  OOM   Dependency
```

---

# 29. Most Important Commands

```bash
kubectl get pods
```

```bash
kubectl describe pod <pod-name>
```

```bash
kubectl logs <pod-name>
```

```bash
kubectl logs <pod-name> --previous
```

```bash
kubectl get events --sort-by=.lastTimestamp
```

```bash
kubectl get deployment
```

```bash
kubectl describe deployment <deployment-name>
```

```bash
kubectl get rs
```

```bash
kubectl get svc
```

```bash
kubectl get pods -A
```

---

# 30. Root Cause Categories

When troubleshooting, classify the problem:

```text
1. Application
2. Configuration
3. Secret
4. Environment
5. Command/entrypoint
6. Probe
7. Resource
8. Permission
9. Dependency
10. Networking
```

This makes production troubleshooting much faster.

---

# 31. One-Minute Interview Explanation

> CrashLoopBackOff means a container is repeatedly starting and failing, and Kubernetes is progressively backing off before restarting it. I don't treat CrashLoopBackOff as the root cause. I first run `kubectl get pods`, then `kubectl describe pod` to check State, Last State, Reason, Exit Code, Restart Count and Events. I check current and previous logs to understand why the application exits. Then I investigate configuration, environment variables, ConfigMaps, Secrets, probes, resources, permissions and dependencies. In my lab I reproduced CrashLoopBackOff using an invalid command, missing environment variable, incorrect ConfigMap, OOMKilled condition, permission issue and dependency failure. I also learned that a missing Secret produces `CreateContainerConfigError`, because the container never starts, which is different from CrashLoopBackOff.

