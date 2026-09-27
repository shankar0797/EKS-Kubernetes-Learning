# ReplicaSet Troubleshooting

## Incident 1 — Deleted Pod Was Automatically Recreated

### Symptom

A ReplicaSet-managed Pod was manually deleted.

```bash
kubectl delete pod <pod-name>
```

A new Pod appeared automatically.

### Investigation

```bash
kubectl get rs
```

The ReplicaSet still had:

```text
DESIRED = 2
CURRENT = 2
READY = 2
```

We then checked the Pod:

```bash
kubectl describe pod <pod-name>
```

and found:

```text
Controlled By: ReplicaSet/nginx-replicaset
```

### Root Cause

The Pod was managed by a ReplicaSet.

The ReplicaSet continuously maintains the configured desired replica count.

### Result

Deleting one Pod caused the ReplicaSet to create a replacement.

### Lesson

Do not assume a Pod is an independent resource. Always determine whether it is controlled by a Deployment, ReplicaSet, StatefulSet, Job, or another controller.

---

# Incident 2 — Desired Replicas Greater Than Current

### Symptom

Example:

```text
DESIRED   CURRENT   READY
3         2         2
```

### Investigation

```bash
kubectl describe rs <name>
kubectl get pods
kubectl get events --sort-by=.lastTimestamp
```

### Possible Root Causes

* Insufficient CPU
* Insufficient memory
* Node unavailable
* Taints
* Node selectors
* Affinity rules
* Resource quotas
* Scheduling constraints

### Troubleshooting Flow

```text
ReplicaSet
    ↓
Check desired/current
    ↓
Describe ReplicaSet
    ↓
Check Events
    ↓
Check Pods
    ↓
Check Nodes
    ↓
Identify scheduling constraint
    ↓
Fix
    ↓
Verify replica count
```

---

# Incident 3 — Pods Exist but Are Not Ready

### Symptom

```text
DESIRED   CURRENT   READY
3         3         0
```

### Investigation

```bash
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Possible Causes

* ImagePullBackOff
* CrashLoopBackOff
* Readiness probe failure
* Application startup failure
* Configuration problem
* Dependency unavailable

### Key Principle

The ReplicaSet may have successfully created the Pods while the application inside those Pods is unhealthy.

---

# Incident 4 — Selector/Label Investigation

### ReplicaSet

```text
Selector:
app=nginx
```

### Managed Pods

```text
app=nginx
```

### Independent Pod

```text
app=web
```

The independent Pod was not managed by the ReplicaSet because its label did not match the ReplicaSet selector.

### Commands

```bash
kubectl get pods --show-labels
kubectl describe rs <name>
kubectl describe pod <name>
```

### Lesson

Labels and selectors form an important relationship throughout Kubernetes.

The same mechanism will later be used heavily with Services.

---

# Incident 5 — Pod Ownership Investigation

### Command

```bash
kubectl describe pod <pod-name>
```

Look for:

```text
Controlled By: ReplicaSet/<name>
```

Or:

```bash
kubectl get pod <pod-name> \
-o jsonpath='{.metadata.ownerReferences[0].kind}{" / "}{.metadata.ownerReferences[0].name}{"\n"}'
```

Example:

```text
ReplicaSet / nginx-replicaset
```

### Why this matters

Before manually deleting or modifying a Pod in production, determine whether a controller manages it.

Deleting a controller-managed Pod may simply cause Kubernetes to recreate it.

---

# Production Troubleshooting Workflow

```bash
kubectl get rs
```

↓

```bash
kubectl describe rs <name>
```

↓

```bash
kubectl get pods
```

↓

```bash
kubectl describe pod <name>
```

↓

```bash
kubectl logs <name>
```

↓

```bash
kubectl get events --sort-by=.lastTimestamp
```

↓

```bash
kubectl get nodes
```

↓

Identify root cause

↓

Fix

↓

Verify:

```bash
kubectl get rs
kubectl get pods
```

---

# Key Interview Principle

Do not troubleshoot only from the ReplicaSet.

Think in layers:

```text
Deployment
    ↓
ReplicaSet
    ↓
Pod
    ↓
Container
    ↓
Application
```

Find the layer where the desired state and actual state diverge.

