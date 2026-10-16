# Advanced Kubernetes — Troubleshooting

> GitHub-ready troubleshooting notes. Troubleshooting scenarios will be added as each Advanced Kubernetes concept is covered.

---

# 01. Pod Disruption Budget (PDB)

## Scenario 1 — Pods are not being evicted during `kubectl drain`

### Symptom

A node drain appears to be blocked or eviction is taking longer than expected.

### First checks

```bash
kubectl get pdb -A
kubectl describe pdb <pdb-name> -n <namespace>
kubectl get pods -n <namespace> -o wide
kubectl get nodes
```

### What to inspect

Check:

- `minAvailable`
- `maxUnavailable`
- Number of matching Pods
- Number of currently available Pods
- PDB selector
- Whether the selector actually matches the intended Pods

### Common root cause

The PDB may be protecting too much of the workload.

Example:

```text
6 replicas
PDB minAvailable = 6
```

There is effectively no room for a voluntary disruption while all six Pods are required to remain available.

### Resolution approach

Review whether the availability requirement is realistic.

For example:

```yaml
minAvailable: 4
```

instead of requiring all six Pods to remain available, depending on the application's real availability requirement.

Always choose the PDB based on the application's actual redundancy and availability design.

---

## Scenario 2 — PDB appears to have no effect

### Checks

```bash
kubectl get pdb -n <namespace>
kubectl describe pdb <pdb-name> -n <namespace>
kubectl get pods -n <namespace> --show-labels
```

### Common causes

- PDB selector does not match the Pods.
- PDB is in the wrong namespace.
- The workload has fewer replicas than expected.
- The PDB configuration does not match the application's intended availability requirement.

### Root-cause method

Compare:

```text
PDB selector
      ↓
Pod labels
```

For example:

```yaml
selector:
  matchLabels:
    app: api
```

must match:

```yaml
labels:
  app: api
```

---

## Scenario 3 — PDB does not protect against a node crash

### Symptom

A node fails and several Pods disappear even though a PDB exists.

### Explanation

This is expected.

PDB primarily protects against **voluntary disruptions**.

It cannot prevent:

```text
Node crash
Hardware failure
Power failure
Kernel panic
```

### Production lesson

PDB is only one part of high availability.

A production application should also consider:

- Multiple replicas
- Multiple nodes
- Pod anti-affinity
- Topology spread constraints
- Appropriate scheduling
- Autoscaling

---

## Scenario 4 — PDB configuration conflicts with workload size

Example:

```text
Deployment replicas = 2
PDB minAvailable = 4
```

PDB cannot create the missing replicas.

### Correct mental model

```text
Deployment
→ Controls desired Pod count

PDB
→ Controls voluntary disruption of those Pods
```

If the application needs four replicas, configure the Deployment accordingly.

---

# PDB Troubleshooting Commands

```bash
kubectl get pdb -A

kubectl get pdb -n <namespace>

kubectl describe pdb <name> -n <namespace>

kubectl get pods -n <namespace> --show-labels

kubectl get pods -n <namespace> -o wide

kubectl get nodes

kubectl describe node <node-name>
```

---

# General troubleshooting approach

When a PDB-related operation is not behaving as expected:

```text
1. Check the PDB
        ↓
2. Check PDB selector
        ↓
3. Check Pod labels
        ↓
4. Check desired replicas
        ↓
5. Check available Pods
        ↓
6. Check node placement
        ↓
7. Check the eviction/drain output
```

---

# Interview Troubleshooting Question

### Q: `kubectl drain` is blocked even though the application has several replicas. What would you check?

Answer:

> I would first inspect the PDB with `kubectl get pdb` and `kubectl describe pdb`. Then I would compare its selector with the actual Pod labels, check the Deployment replica count and available replicas, and verify whether the PDB's `minAvailable` or `maxUnavailable` setting leaves enough room for the requested eviction.

---

# Important rule

Do not troubleshoot PDB in isolation.

Think about:

```text
Deployment replicas
       ↓
Pod labels
       ↓
PDB selector
       ↓
Available Pods
       ↓
Node distribution
       ↓
Voluntary disruption
```

---

# Progress

- [x] PDB troubleshooting foundation
- [ ] Advanced Scheduling troubleshooting
- [ ] Affinity troubleshooting
- [ ] Anti-affinity troubleshooting
- [ ] Topology Spread troubleshooting
- [ ] Taints/Tolerations troubleshooting
- [ ] Termination troubleshooting
- [ ] Container lifecycle troubleshooting
- [ ] Admission/security troubleshooting
- [ ] ResourceQuota/LimitRange troubleshooting
- [ ] CRD/Operator troubleshooting
- [ ] Advanced Kubernetes troubleshooting scenarios
# Advanced Kubernetes — Troubleshooting

> GitHub-ready troubleshooting notes. Troubleshooting scenarios will be added as each Advanced Kubernetes concept is covered.

---

# 01. Pod Disruption Budget (PDB)

## Scenario 1 — Pods are not being evicted during `kubectl drain`

### Symptom

A node drain appears to be blocked or eviction is taking longer than expected.

### First checks

```bash
kubectl get pdb -A
kubectl describe pdb <pdb-name> -n <namespace>
kubectl get pods -n <namespace> -o wide
kubectl get nodes
```

### What to inspect

Check:

- `minAvailable`
- `maxUnavailable`
- Number of matching Pods
- Number of currently available Pods
- PDB selector
- Whether the selector actually matches the intended Pods

### Common root cause

The PDB may be protecting too much of the workload.

Example:

```text
6 replicas
PDB minAvailable = 6
```

There is effectively no room for a voluntary disruption while all six Pods are required to remain available.

### Resolution approach

Review whether the availability requirement is realistic.

For example:

```yaml
minAvailable: 4
```

instead of requiring all six Pods to remain available, depending on the application's real availability requirement.

Always choose the PDB based on the application's actual redundancy and availability design.

---

## Scenario 2 — PDB appears to have no effect

### Checks

```bash
kubectl get pdb -n <namespace>
kubectl describe pdb <pdb-name> -n <namespace>
kubectl get pods -n <namespace> --show-labels
```

### Common causes

- PDB selector does not match the Pods.
- PDB is in the wrong namespace.
- The workload has fewer replicas than expected.
- The PDB configuration does not match the application's intended availability requirement.

### Root-cause method

Compare:

```text
PDB selector
      ↓
Pod labels
```

For example:

```yaml
selector:
  matchLabels:
    app: api
```

must match:

```yaml
labels:
  app: api
```

---

## Scenario 3 — PDB does not protect against a node crash

### Symptom

A node fails and several Pods disappear even though a PDB exists.

### Explanation

This is expected.

PDB primarily protects against **voluntary disruptions**.

It cannot prevent:

```text
Node crash
Hardware failure
Power failure
Kernel panic
```

### Production lesson

PDB is only one part of high availability.

A production application should also consider:

- Multiple replicas
- Multiple nodes
- Pod anti-affinity
- Topology spread constraints
- Appropriate scheduling
- Autoscaling

---

## Scenario 4 — PDB configuration conflicts with workload size

Example:

```text
Deployment replicas = 2
PDB minAvailable = 4
```

PDB cannot create the missing replicas.

### Correct mental model

```text
Deployment
→ Controls desired Pod count

PDB
→ Controls voluntary disruption of those Pods
```

If the application needs four replicas, configure the Deployment accordingly.

---

# PDB Troubleshooting Commands

```bash
kubectl get pdb -A

kubectl get pdb -n <namespace>

kubectl describe pdb <name> -n <namespace>

kubectl get pods -n <namespace> --show-labels

kubectl get pods -n <namespace> -o wide

kubectl get nodes

kubectl describe node <node-name>
```

---

# General troubleshooting approach

When a PDB-related operation is not behaving as expected:

```text
1. Check the PDB
        ↓
2. Check PDB selector
        ↓
3. Check Pod labels
        ↓
4. Check desired replicas
        ↓
5. Check available Pods
        ↓
6. Check node placement
        ↓
7. Check the eviction/drain output
```

---

# Interview Troubleshooting Question

### Q: `kubectl drain` is blocked even though the application has several replicas. What would you check?

Answer:

> I would first inspect the PDB with `kubectl get pdb` and `kubectl describe pdb`. Then I would compare its selector with the actual Pod labels, check the Deployment replica count and available replicas, and verify whether the PDB's `minAvailable` or `maxUnavailable` setting leaves enough room for the requested eviction.

---

# Important rule

Do not troubleshoot PDB in isolation.

Think about:

```text
Deployment replicas
       ↓
Pod labels
       ↓
PDB selector
       ↓
Available Pods
       ↓
Node distribution
       ↓
Voluntary disruption
```

---

# Progress

- [x] PDB troubleshooting foundation
- [ ] Advanced Scheduling troubleshooting
- [ ] Affinity troubleshooting
- [ ] Anti-affinity troubleshooting
- [ ] Topology Spread troubleshooting
- [ ] Taints/Tolerations troubleshooting
- [ ] Termination troubleshooting
- [ ] Container lifecycle troubleshooting
- [ ] Admission/security troubleshooting
- [ ] ResourceQuota/LimitRange troubleshooting
- [ ] CRD/Operator troubleshooting
- [ ] Advanced Kubernetes troubleshooting scenarios

