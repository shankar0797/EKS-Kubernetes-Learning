# Kubernetes CrashLoopBackOff — Troubleshooting

## 1. Standard Troubleshooting Flow

When a Pod shows:

```text
CrashLoopBackOff
```

follow this sequence:

```text
kubectl get pods
        ↓
kubectl describe pod
        ↓
Check State
        ↓
Check Last State
        ↓
Check Reason
        ↓
Check Exit Code
        ↓
Check Restart Count
        ↓
Check Events
        ↓
kubectl logs
        ↓
kubectl logs --previous
        ↓
Check command/image
        ↓
Check environment
        ↓
Check ConfigMap/Secret
        ↓
Check probes
        ↓
Check resources
        ↓
Check permissions
        ↓
Check dependencies/network
        ↓
Find root cause
        ↓
Fix
        ↓
Verify
```

---

# 2. Scenario 1 — Application Command Exits With Error

## Symptom

Pod:

```text
READY   STATUS             RESTARTS
0/1     CrashLoopBackOff   5
```

---

## Check Pod

```bash
kubectl describe pod <pod-name>
```

We found:

```text
Last State:
  Terminated

Reason:
  Error

Exit Code:
  1
```

---

## Check Logs

```bash
kubectl logs <pod-name>
```

Output:

```text
Application starting...
```

The container command was:

```yaml
command:
  - /bin/sh
  - -c
  - "echo 'Application starting...'; exit 1"
```

---

## Root Cause

The application command intentionally exited with:

```text
exit 1
```

Therefore the container terminated.

Kubernetes restarted it.

The cycle repeated.

---

## Fix

Changed the command to keep Nginx running:

```yaml
command:
  - /bin/sh
  - -c
  - "echo 'Application started successfully'; nginx -g 'daemon off;'"
```

---

## Verification

```bash
kubectl get pods
```

Result:

```text
1/1 Running
```

---

# 3. Scenario 2 — Missing Environment Variable

## Symptom

Pod:

```text
CrashLoopBackOff
```

---

## Logs

```bash
kubectl logs <pod-name>
```

Output:

```text
Application starting...
Checking DATABASE_URL...
ERROR: DATABASE_URL is not configured
```

---

## Root Cause

Required environment variable:

```text
DATABASE_URL
```

was not configured.

The application intentionally exited when the value was missing.

---

## Fix

Added:

```yaml
env:
  - name: DATABASE_URL
    value: "postgresql://db.example.internal:5432/orders"
```

---

## Verification

```bash
kubectl get pods
```

Result:

```text
1/1 Running
```

Restart count stabilized.

---

# 4. Scenario 3 — Wrong ConfigMap

## Symptom

Pod repeatedly crashed.

---

## Check Logs

```bash
kubectl logs <pod-name>
```

Output:

```text
Application starting...
Environment: production
Database host: wrong-database.internal
Database port: 5432
ERROR: Cannot connect to database at wrong-database.internal
```

---

## Investigation

We inspected the ConfigMap:

```bash
kubectl get configmap application-config -o yaml
```

The value was:

```yaml
DATABASE_HOST: "wrong-database.internal"
```

The application expected:

```text
postgres.database.svc.cluster.local
```

---

## Root Cause

Incorrect ConfigMap value.

---

## Fix

Changed:

```yaml
DATABASE_HOST: "postgres.database.svc.cluster.local"
```

Then restarted the Deployment:

```bash
kubectl rollout restart deployment crash-configmap
```

---

## Verification

```bash
kubectl get pods
```

Result:

```text
1/1 Running
```

Logs:

```text
Application starting...
Environment: production
Database host: postgres.database.svc.cluster.local
Database port: 5432
Database connection successful
```

---

# 5. ConfigMap Environment Variable Lesson

When ConfigMap data is injected as environment variables:

```yaml
env:
  - name: DATABASE_HOST
    valueFrom:
      configMapKeyRef:
        name: application-config
        key: DATABASE_HOST
```

the value is loaded when the container starts.

Therefore:

```text
ConfigMap updated
      ↓
Existing container
      ↓
Doesn't automatically restart
```

For environment-variable configuration, use:

```bash
kubectl rollout restart deployment <deployment>
```

when the application needs to reload the value.

---

# 6. Scenario 4 — Missing Secret

This scenario is particularly important because it initially looked like a container problem but was actually a configuration problem.

## Symptom

Pod:

```text
0/1 CreateContainerConfigError
```

---

## Describe Pod

```bash
kubectl describe pod <pod-name>
```

Events showed:

```text
secret "database-credentials" not found
```

---

## Important Observation

There was:

```text
No container ID
No application logs
No exit code
```

Why?

Because the container never started.

Therefore this was:

```text
CreateContainerConfigError
```

not:

```text
CrashLoopBackOff
```

---

## Root Cause

Required Secret did not exist.

---

## Fix

Created the Secret:

```bash
kubectl create secret generic database-credentials \
  --from-literal=username=appuser \
  --from-literal=password='DemoPassword123!'
```

---

## Verification

The container was then able to start.

### Production note

Do not use plaintext credentials like this for production workloads.

Use appropriate secret-management mechanisms such as:

```text
AWS Secrets Manager
+
EKS integration
```

---

# 7. Scenario 5 — OOMKilled

## Symptom

Pod repeatedly restarted.

Describe output showed:

```text
State:
  Terminated

Reason:
  OOMKilled

Exit Code:
  137
```

---

## Application Behavior

The Python application continuously allocated memory.

Resource limit:

```yaml
resources:
  limits:
    memory: "64Mi"
```

Application eventually consumed more than the limit.

---

## Flow

```text
Application
      ↓
Memory increases
      ↓
64Mi limit reached
      ↓
Container killed
      ↓
Restart
      ↓
Memory increases again
      ↓
Killed again
```

Eventually:

```text
CrashLoopBackOff
```

---

## Root Cause

Memory exhaustion.

The important diagnosis was:

```text
OOMKilled = Root Cause
CrashLoopBackOff = Result
```

---

## Troubleshooting

Check:

```bash
kubectl describe pod <pod-name>
```

Look for:

```text
Reason: OOMKilled
Exit Code: 137
```

Also check resource configuration.

Do not simply increase the limit without investigating:

* Memory leak
* Application behavior
* Traffic
* Memory requirements
* Scaling
* Resource sizing

---

# 8. Scenario 6 — Permission Denied

## Symptom

Application attempted to write:

```text
/etc/config.txt
```

The container was configured to run as:

```text
UID 1000
GID 1000
```

---

## Check Permissions

Inside the container:

```bash
id
```

Result:

```text
uid=1000 gid=1000
```

Check:

```bash
ls -ld /etc
```

Result showed root ownership:

```text
drwxr-xr-x root root /etc
```

---

## Application Output

```text
Application starting...
Running as user: uid=1000 gid=1000 groups=1000
Trying to write application file...
/bin/sh: can't create /etc/config.txt: Permission denied
```

---

## Root Cause

User 1000 does not have permission to write to root-owned `/etc`.

This is a Linux filesystem permission problem.

Kubernetes itself was not arbitrarily denying the write.

---

# 9. Important Shell Behavior

The original script continued after the write failure because it did not contain:

```bash
set -e
```

Therefore:

```text
Write fails
   ↓
Shell continues
   ↓
"Application started successfully"
   ↓
Process stays alive
```

The Pod could therefore remain Running even though an important command failed.

This is an important debugging lesson.

---

# 10. Correct Approach

For a script where command failure should terminate the application:

```bash
set -e
```

Example:

```yaml
command:
  - /bin/sh
  - -c
  - |
    set -e

    echo "Application starting..."

    echo "application configuration" > /etc/config.txt

    echo "Application started successfully"

    while true; do
      sleep 30
    done
```

Then a failed write causes the shell to exit.

---

# 11. Production Fix for Permission Problems

Do not simply run everything as root.

Instead:

```text
Application
     ↓
Need writable directory
     ↓
Use appropriate writable path
     ↓
Volume if required
     ↓
Correct ownership/permissions
```

For persistent or shared data, use appropriate Kubernetes storage mechanisms.

---

# 12. Scenario 7 — Database Dependency Unavailable

## Symptom

Application repeatedly crashes.

Logs may show:

```text
Application starting...
Checking database connectivity...
ERROR: Cannot connect to database
```

---

## Troubleshooting

Check:

```bash
kubectl get svc
```

Does the database Service exist?

Then:

```bash
kubectl get pods
```

Is the database Pod running?

Check endpoints:

```bash
kubectl get endpoints
```

Then investigate:

```text
DNS
Service
Endpoints
Port
NetworkPolicy
Credentials
Database health
```

---

## Flow

```text
Application
      ↓
Database connection
      ↓
Connection fails
      ↓
Application exits
      ↓
Container restarts
      ↓
Repeated failure
      ↓
CrashLoopBackOff
```

---

# 13. Scenario 8 — Liveness Probe Causes Restart Loop

A Pod may be healthy, but the liveness probe may be incorrectly configured.

Example:

```yaml
livenessProbe:
  httpGet:
    path: /does-not-exist
    port: 80
```

Nginx returns:

```text
404
```

Then:

```text
Liveness failure
      ↓
Container restart
      ↓
Application starts
      ↓
Liveness failure again
      ↓
Restart
```

Eventually:

```text
CrashLoopBackOff
```

---

## Root Cause

Incorrect liveness probe configuration.

---

## Fix

Use the actual health endpoint.

Then verify:

```bash
kubectl get pods
```

and confirm the restart count stabilizes.

---

# 14. CrashLoopBackOff Investigation Matrix

| Observation               | Likely Area                       |
| ------------------------- | --------------------------------- |
| Exit Code 1               | Application/command/config        |
| OOMKilled                 | Memory                            |
| Exit Code 137 + OOMKilled | Memory                            |
| Liveness failures         | Probe/application                 |
| Missing env variable      | Configuration                     |
| Wrong DB host             | ConfigMap/config                  |
| Missing Secret            | Container configuration           |
| Permission denied         | Linux filesystem/security context |
| Connection refused        | Dependency/port/network           |
| Image pull failure        | Image/registry                    |
| Container never starts    | Container config/runtime          |

---

# 15. Production Decision Tree

```text
CrashLoopBackOff
      |
      v
describe pod
      |
      +---- Last State = OOMKilled
      |          ↓
      |       Memory
      |
      +---- Liveness failures
      |          ↓
      |       Probe/application
      |
      +---- Exit Code 1
      |          ↓
      |       Application/config/command
      |
      +---- Permission denied
      |          ↓
      |       User/filesystem
      |
      +---- Dependency error
      |          ↓
      |       DB/service/network
      |
      +---- Missing configuration
                 ↓
          ConfigMap/Secret/env
```

---

# 16. What NOT to Do

When you see:

```text
CrashLoopBackOff
```

don't immediately:

```text
❌ Delete the Pod
❌ Increase memory blindly
❌ Increase probe thresholds blindly
❌ Restart everything
❌ Change random configuration
```

Instead:

```text
Observe
 ↓
Collect evidence
 ↓
Find root cause
 ↓
Apply targeted fix
 ↓
Verify
```

---

# 17. Production Troubleshooting Checklist

```text
[ ] kubectl get pods
[ ] Check READY
[ ] Check STATUS
[ ] Check RESTARTS
[ ] kubectl describe pod
[ ] Check State
[ ] Check Last State
[ ] Check Reason
[ ] Check Exit Code
[ ] Check Events
[ ] kubectl logs
[ ] kubectl logs --previous
[ ] Check command/entrypoint
[ ] Check environment variables
[ ] Check ConfigMaps
[ ] Check Secrets
[ ] Check probes
[ ] Check memory/CPU
[ ] Check securityContext
[ ] Check dependencies
[ ] Check Services
[ ] Check DNS/networking
[ ] Fix root cause
[ ] Verify Pod
[ ] Verify restart count stabilizes
```

---

# 18. Interview Scenario — Production CrashLoop

### Question

**A production application suddenly enters CrashLoopBackOff. What steps will you follow?**

Answer:

> First I check `kubectl get pods` to confirm the status and restart count. Then I run `kubectl describe pod` and check the current state, last state, reason, exit code and Events. I collect application logs and previous container logs. Based on the evidence, I investigate the command, environment variables, ConfigMaps, Secrets, probes, memory/CPU, permissions and external dependencies. I identify the actual root cause, apply a targeted fix, and verify that the Pod becomes Ready and the restart count stabilizes.

---

# 19. Interview Scenario — CrashLoop vs CreateContainerConfigError

### Question

**How is CreateContainerConfigError different from CrashLoopBackOff?**

Answer:

> In CreateContainerConfigError, the container generally cannot be created because of a configuration problem such as a missing Secret. The application never starts, so there may be no application logs or container exit code. In CrashLoopBackOff, the container has started and repeatedly terminates, so I investigate application logs, Last State, exit code, probes and Events.

---

# 20. Interview Scenario — OOMKilled

### Question

**A Pod shows CrashLoopBackOff and Last State is OOMKilled. What do you do?**

Answer:

> I treat OOMKilled as the immediate root cause rather than CrashLoopBackOff. I check the container memory limit, actual application memory behavior, logs, workload/traffic and whether there is a memory leak. I then determine whether the appropriate solution is application optimization, resource adjustment, or scaling rather than blindly increasing the memory limit.

---

# 21. Interview Scenario — Liveness

### Question

**Can a liveness probe cause CrashLoopBackOff?**

Yes.

If the liveness probe is incorrectly configured or too aggressive:

```text
Liveness fails
    ↓
Container restarted
    ↓
Liveness fails again
    ↓
Repeated restarts
    ↓
CrashLoopBackOff
```

---

# 22. Interview Scenario — Missing Secret

### Question

**A Pod shows CreateContainerConfigError and Events say Secret not found. What do you do?**

Check:

```bash
kubectl get secret
kubectl describe pod <pod>
```

Verify:

* Secret name
* Namespace
* Secret key
* Deployment reference

Create or correct the Secret, then verify the Pod starts.

---

# 23. Key Lessons From Our Labs

We reproduced several real-world failure patterns:

```text
1. Application exits with code 1
2. Missing environment variable
3. Wrong ConfigMap
4. Missing Secret
5. OOMKilled
6. Permission denied
7. Database/dependency unavailable
8. Liveness probe failure
```

The biggest lesson:

```text
CrashLoopBackOff
       ↓
Not the root cause
       ↓
Investigate why the container is terminating
```

The most important commands:

```bash
kubectl get pods
kubectl describe pod <pod>
kubectl logs <pod>
kubectl logs <pod> --previous
kubectl get events --sort-by=.lastTimestamp
```

---

# 24. Final Mental Model

```text
                 Pod Problem
                     |
                     v
              kubectl get pods
                     |
                     v
             What is the STATUS?
                     |
        +------------+-------------+
        |            |             |
        v            v             v
    Pending       Config        CrashLoop
                     |             |
                     |             v
                     |        describe pod
                     |             |
                     |             v
                     |          logs
                     |             |
                     |             v
                     |       previous logs
                     |             |
                     |             v
                     |       Find root cause
                     |
                     v
              Events/config
```

### Production mindset

> **Don't troubleshoot the status name. Troubleshoot the event that caused the status.**

For CrashLoopBackOff:

```text
Status
  ↓
State
  ↓
Last State
  ↓
Reason
  ↓
Exit Code
  ↓
Events
  ↓
Logs
  ↓
Root Cause
  ↓
Fix
  ↓
Verify
```
