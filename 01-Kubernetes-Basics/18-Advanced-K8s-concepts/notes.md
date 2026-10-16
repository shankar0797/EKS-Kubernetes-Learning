# Advanced Kubernetes — Notes

> GitHub-ready learning notes. Concepts are documented as we complete the Advanced Kubernetes module.

---

# Module Roadmap

1. Pod Disruption Budgets (PDB)
2. Advanced Scheduling
3. Pod Affinity
4. Pod Anti-Affinity
5. Topology Spread Constraints
6. Taints & Tolerations
7. Graceful Pod Termination
8. PreStop Hooks
9. Init Containers
10. Sidecar Containers
11. Ephemeral Containers
12. Admission Controllers
13. Mutating Admission
14. Validating Admission
15. Pod Security Admission
16. ResourceQuota
17. LimitRange
18. Kubernetes Multi-Tenancy
19. Finalizers
20. OwnerReferences
21. Garbage Collection
22. CRDs
23. Operators
24. API Extensions
25. Advanced Troubleshooting
26. Interview Q&A
27. Cheat Sheet

---

# 01. Pod Disruption Budget (PDB)

## What is it?

A Pod Disruption Budget defines how much **voluntary disruption** an application can tolerate.

It can specify either:

- `minAvailable` — minimum number/percentage of Pods that should remain available.
- `maxUnavailable` — maximum number/percentage of Pods that can be unavailable.

## What problem does it solve?

During planned Kubernetes operations such as node maintenance or `kubectl drain`, multiple Pods could otherwise be disrupted at the same time.

PDB helps protect application availability during these voluntary disruptions.

## Real-world use case

Suppose a production API has six replicas:

```text
api-1
api-2
api-3
api-4
api-5
api-6
```

We want at least four to remain available during planned node maintenance.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
  namespace: production
spec:
  minAvailable: 4
  selector:
    matchLabels:
      app: api
```

## `minAvailable`

```yaml
minAvailable: 4
```

Means:

> At least four matching Pods should remain available during voluntary disruption.

Percentage is also possible:

```yaml
minAvailable: 80%
```

## `maxUnavailable`

```yaml
maxUnavailable: 1
```

Means:

> At most one matching Pod can be unavailable because of the voluntary disruption.

Percentage is also possible:

```yaml
maxUnavailable: 20%
```

## Voluntary vs involuntary disruption

### Voluntary

Examples:

- `kubectl drain`
- Planned node maintenance
- Cluster maintenance/upgrade
- Voluntary Pod eviction

PDB helps protect against these.

### Involuntary

Examples:

- Node crash
- Hardware failure
- Power failure
- Kernel panic

PDB cannot prevent these failures.

## Important distinction

Deployment replicas and PDB have different responsibilities:

```text
Deployment
    ↓
How many Pods should exist?

PDB
    ↓
How many Pods should remain available
during voluntary disruption?
```

PDB does not create extra Pods.

For example:

```yaml
replicas: 2
```

and:

```yaml
minAvailable: 4
```

does not cause Kubernetes to create four Pods.

## Architecture

```text
                 Deployment
                     │
                 replicas: 6
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
       Pod          Pod          Pod
        │
        └─────────────────────────┐
                                  ▼
                                 PDB
                                  │
                          minAvailable: 4
                                  │
                                  ▼
                    Protects availability
                    during voluntary eviction
```

## Interview explanation

> A Pod Disruption Budget defines the minimum availability or maximum unavailability allowed for Pods during voluntary disruptions such as node drain or maintenance. It helps maintain application availability during planned Kubernetes operations.

### Interview Q&A

**Q: Does PDB protect against node failure?**

A: No. PDB primarily protects against voluntary disruptions. It cannot prevent involuntary failures such as a node crash.

**Q: PDB vs Deployment replicas?**

A: Deployment replicas define how many Pods should run. PDB defines how many of those Pods should remain available during voluntary disruption.

**Q: What are the two main PDB controls?**

A: `minAvailable` and `maxUnavailable`.

## Cheat sheet

```text
PDB
 ↓
Protects availability during voluntary disruption

minAvailable
 ↓
Minimum Pods that should remain available

maxUnavailable
 ↓
Maximum Pods allowed to be unavailable

PDB does NOT:
 ↓
Prevent node crashes
Create extra Pods
Replace a Deployment
```

---

# Progress

- [x] Pod Disruption Budget — conceptual foundation
- [ ] Advanced Scheduling
- [ ] Pod Affinity
- [ ] Pod Anti-Affinity
- [ ] Topology Spread Constraints
- [ ] Taints & Tolerations
- [ ] Graceful Pod Termination
- [ ] PreStop Hooks
- [ ] Init Containers
- [ ] Sidecar Containers
- [ ] Ephemeral Containers
- [ ] Admission Controllers
- [ ] Mutating Admission
- [ ] Validating Admission
- [ ] Pod Security Admission
- [ ] ResourceQuota
- [ ] LimitRange
- [ ] Multi-Tenancy
- [ ] Finalizers
- [ ] OwnerReferences
- [ ] Garbage Collection
- [ ] CRDs
- [ ] Operators
- [ ] API Extensions
- [ ] Advanced Troubleshooting
- [ ] Interview Q&A
- [ ] Final Cheat Sheet
# Advanced Kubernetes — Notes

> GitHub-ready learning notes. Concepts are documented as we complete the Advanced Kubernetes module.

---

# Module Roadmap

1. Pod Disruption Budgets (PDB)
2. Advanced Scheduling
3. Pod Affinity
4. Pod Anti-Affinity
5. Topology Spread Constraints
6. Taints & Tolerations
7. Graceful Pod Termination
8. PreStop Hooks
9. Init Containers
10. Sidecar Containers
11. Ephemeral Containers
12. Admission Controllers
13. Mutating Admission
14. Validating Admission
15. Pod Security Admission
16. ResourceQuota
17. LimitRange
18. Kubernetes Multi-Tenancy
19. Finalizers
20. OwnerReferences
21. Garbage Collection
22. CRDs
23. Operators
24. API Extensions
25. Advanced Troubleshooting
26. Interview Q&A
27. Cheat Sheet

---

# 01. Pod Disruption Budget (PDB)

## What is it?

A Pod Disruption Budget defines how much **voluntary disruption** an application can tolerate.

It can specify either:

- `minAvailable` — minimum number/percentage of Pods that should remain available.
- `maxUnavailable` — maximum number/percentage of Pods that can be unavailable.

## What problem does it solve?

During planned Kubernetes operations such as node maintenance or `kubectl drain`, multiple Pods could otherwise be disrupted at the same time.

PDB helps protect application availability during these voluntary disruptions.

## Real-world use case

Suppose a production API has six replicas:

```text
api-1
api-2
api-3
api-4
api-5
api-6
```

We want at least four to remain available during planned node maintenance.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
  namespace: production
spec:
  minAvailable: 4
  selector:
    matchLabels:
      app: api
```

## `minAvailable`

```yaml
minAvailable: 4
```

Means:

> At least four matching Pods should remain available during voluntary disruption.

Percentage is also possible:

```yaml
minAvailable: 80%
```

## `maxUnavailable`

```yaml
maxUnavailable: 1
```

Means:

> At most one matching Pod can be unavailable because of the voluntary disruption.

Percentage is also possible:

```yaml
maxUnavailable: 20%
```

## Voluntary vs involuntary disruption

### Voluntary

Examples:

- `kubectl drain`
- Planned node maintenance
- Cluster maintenance/upgrade
- Voluntary Pod eviction

PDB helps protect against these.

### Involuntary

Examples:

- Node crash
- Hardware failure
- Power failure
- Kernel panic

PDB cannot prevent these failures.

## Important distinction

Deployment replicas and PDB have different responsibilities:

```text
Deployment
    ↓
How many Pods should exist?

PDB
    ↓
How many Pods should remain available
during voluntary disruption?
```

PDB does not create extra Pods.

For example:

```yaml
replicas: 2
```

and:

```yaml
minAvailable: 4
```

does not cause Kubernetes to create four Pods.

## Architecture

```text
                 Deployment
                     │
                 replicas: 6
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
       Pod          Pod          Pod
        │
        └─────────────────────────┐
                                  ▼
                                 PDB
                                  │
                          minAvailable: 4
                                  │
                                  ▼
                    Protects availability
                    during voluntary eviction
```

## Interview explanation

> A Pod Disruption Budget defines the minimum availability or maximum unavailability allowed for Pods during voluntary disruptions such as node drain or maintenance. It helps maintain application availability during planned Kubernetes operations.

### Interview Q&A

**Q: Does PDB protect against node failure?**

A: No. PDB primarily protects against voluntary disruptions. It cannot prevent involuntary failures such as a node crash.

**Q: PDB vs Deployment replicas?**

A: Deployment replicas define how many Pods should run. PDB defines how many of those Pods should remain available during voluntary disruption.

**Q: What are the two main PDB controls?**

A: `minAvailable` and `maxUnavailable`.

## Cheat sheet

```text
PDB
 ↓
Protects availability during voluntary disruption

minAvailable
 ↓
Minimum Pods that should remain available

maxUnavailable
 ↓
Maximum Pods allowed to be unavailable

PDB does NOT:
 ↓
Prevent node crashes
Create extra Pods
Replace a Deployment
```

---

# Progress

- [x] Pod Disruption Budget — conceptual foundation
- [ ] Advanced Scheduling
- [ ] Pod Affinity
- [ ] Pod Anti-Affinity
- [ ] Topology Spread Constraints
- [ ] Taints & Tolerations
- [ ] Graceful Pod Termination
- [ ] PreStop Hooks
- [ ] Init Containers
- [ ] Sidecar Containers
- [ ] Ephemeral Containers
- [ ] Admission Controllers
- [ ] Mutating Admission
- [ ] Validating Admission
- [ ] Pod Security Admission
- [ ] ResourceQuota
- [ ] LimitRange
- [ ] Multi-Tenancy
- [ ] Finalizers
- [ ] OwnerReferences
- [ ] Garbage Collection
- [ ] CRDs
- [ ] Operators
- [ ] API Extensions
- [ ] Advanced Troubleshooting
- [ ] Interview Q&A
- [ ] Final Cheat Sheet
