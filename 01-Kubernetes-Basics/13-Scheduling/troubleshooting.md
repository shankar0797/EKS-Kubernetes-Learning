# Kubernetes Scheduling — Troubleshooting Guide

> **Purpose:** Production-style troubleshooting reference for Module 06 Scheduling.

---

# 1. Universal Scheduling Troubleshooting Method

Whenever a Pod is stuck in `Pending`, do not guess.

Start with:

```bash
kubectl get pod <pod-name> -o wide
```

Then:

```bash
kubectl describe pod <pod-name>
```

The most important section is:

```text
Events:
```

Then inspect nodes:

```bash
kubectl get nodes
kubectl get nodes --show-labels
kubectl describe node <node-name>
```

Inspect the actual Pod configuration:

```bash
kubectl get pod <pod-name> -o yaml
```

Check:

```text
resources.requests
nodeSelector
affinity
tolerations
topologySpreadConstraints
```

---

# 2. Decision Tree

```text
Pod Pending
    |
    v
kubectl describe pod
    |
    v
Read Events
    |
    +--> Insufficient CPU/memory
    |       |
    |       +--> Check node allocatable
    |
    +--> nodeSelector / Node Affinity
    |       |
    |       +--> Check node labels
    |
    +--> Untolerated taint
    |       |
    |       +--> Check taints/tolerations
    |
    +--> Pod Affinity
    |       |
    |       +--> Check matching Pods/topology
    |
    +--> Pod Anti-Affinity
    |       |
    |       +--> Check number of topology domains
    |
    +--> Topology Spread
            |
            +--> Check labels/domains/skew
```

---

# 3. Insufficient CPU

## Symptom

```text
Pod -> Pending
```

Describe:

```bash
kubectl describe pod <pod>
```

Events may indicate insufficient CPU.

## Diagnosis

Check:

```bash
kubectl describe node <node>
```

Inspect:

```text
Capacity
Allocatable
Allocated resources
```

Also inspect the Pod:

```bash
kubectl get pod <pod> -o yaml
```

Look at:

```yaml
resources:
  requests:
```

## Root cause

The Pod's requested CPU cannot fit on an eligible node.

## Resolution

Options:

- reduce request if incorrectly sized
- add/scale nodes
- change scheduling constraints that unnecessarily restrict eligible nodes

---

# 4. Insufficient Memory

## Symptom

Pod remains Pending.

Example:

```yaml
resources:
  requests:
    memory: "100Gi"
```

## Troubleshooting

```bash
kubectl describe pod <pod>
kubectl describe node <node>
```

## Root cause

No eligible node has enough allocatable memory to satisfy the request.

## Resolution

Right-size the request or provide suitable capacity.

---

# 5. Pending vs OOMKilled

This distinction is critical.

## Pending

```text
Pod has not been successfully scheduled.
```

Check:

```bash
kubectl describe pod <pod>
```

## OOMKilled

```text
Pod was scheduled and a container was killed due to memory pressure/limit.
```

Check:

```bash
kubectl describe pod <pod>
```

Look under container state.

### Interview explanation

> Pending is generally a placement/scheduling problem, while OOMKilled is a runtime memory problem.

---

# 6. nodeSelector Failure

## Example

Pod:

```yaml
nodeSelector:
  workload: database
```

Node:

```text
workload=application
```

## Symptom

```text
Pending
```

## Troubleshooting

```bash
kubectl get nodes --show-labels
kubectl get nodes -L workload
kubectl describe pod <pod>
```

## Root cause

No eligible node has the exact required label.

## Resolution

Either fix the selector or label an intended node:

```bash
kubectl label node <node-name> workload=database
```

Remember:

> nodeSelector does not create a node.

---

# 7. Node Affinity Failure

## Example

```yaml
requiredDuringSchedulingIgnoredDuringExecution:
  nodeSelectorTerms:
    - matchExpressions:
        - key: workload
          operator: In
          values:
            - database
```

But nodes only have:

```text
workload=application
```

## Troubleshooting

```bash
kubectl describe pod <pod>
kubectl get nodes --show-labels
```

Compare:

```text
Required affinity
       vs
Actual node labels
```

## Common root causes

- typo in key
- typo in value
- case mismatch
- wrong operator
- no matching node
- requirement is too restrictive

## Resolution

Correct the rule or provide a matching node.

---

# 8. Preferred Node Affinity Appears to Be Ignored

## Symptom

You configured:

```yaml
preferredDuringSchedulingIgnoredDuringExecution:
```

but the Pod runs somewhere else.

## Is it a failure?

Not necessarily.

Preferred affinity is a soft preference.

## Correct interpretation

```text
Preferred node available
      -> scheduler favors it

Preferred node unsuitable/unavailable
      -> scheduler may use another node
```

If placement is mandatory, use a required rule.

---

# 9. Pod Affinity Failure

## Example

```yaml
podAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          app: database
      topologyKey: kubernetes.io/hostname
```

But no matching Pod exists.

## Symptom

```text
Pending
```

## Troubleshooting

Check Pods:

```bash
kubectl get pods --show-labels
```

Check topology:

```bash
kubectl get nodes --show-labels
```

Check scheduler:

```bash
kubectl describe pod <pod>
```

## Root causes

### No matching Pod

Expected:

```text
app=database
```

but it doesn't exist.

### Wrong label

Pod has:

```text
app=db
```

instead of:

```text
app=database
```

### Wrong namespace

The affinity may be looking in a different namespace configuration than expected.

### Wrong topology

The topology key does not produce the intended placement domain.

## Resolution

Fix the matching Pod labels, namespace selection, or topology rule.

---

# 10. Pod Anti-Affinity Causes Pending

## Scenario

There is one node:

```text
Node-1
  backend-1
```

Second Pod has:

```yaml
podAntiAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          app: backend
      topologyKey: kubernetes.io/hostname
```

## Symptom

```text
backend-2 -> Pending
```

## Root cause

The Pod is required to avoid the node containing `app=backend`, but no other node exists.

## Troubleshooting

```bash
kubectl get nodes
kubectl get pods -o wide --show-labels
kubectl describe pod backend-2
```

## Resolution

- add more nodes
- use preferred anti-affinity
- change topology requirements

---

# 11. Taint Causes Pod Pending

## Node

```text
workload=database:NoSchedule
```

## Pod

No matching toleration.

## Symptom

```text
Pending
```

## Troubleshooting

Check node:

```bash
kubectl describe node <node> | grep -i taint
```

Check Pod:

```bash
kubectl describe pod <pod>
```

Look at Events for an untolerated taint.

## Resolution

Add:

```yaml
tolerations:
  - key: workload
    operator: Equal
    value: database
    effect: NoSchedule
```

or remove the taint if it is not required:

```bash
kubectl taint nodes <node> workload=database:NoSchedule-
```

---

# 12. Toleration Exists but Pod Runs Elsewhere

## Symptom

You expected the Pod to run on a tainted node, but it selected another node.

## Root cause

A toleration does not attract a Pod.

It only makes the node eligible with respect to that taint.

## Resolution

For dedicated placement, combine:

```text
Taint
+
Toleration
+
Node Affinity
```

Example:

```yaml
tolerations:
  - key: workload
    operator: Equal
    value: database
    effect: NoSchedule

affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: workload
              operator: In
              values:
                - database
```

---

# 13. NoExecute Evicts a Pod

## Symptom

A previously running Pod is removed after a node receives a taint.

## Example taint

```text
workload=database:NoExecute
```

## Root cause

`NoExecute` affects existing Pods that do not tolerate the taint.

## Troubleshooting

```bash
kubectl describe node <node>
kubectl describe pod <pod>
```

## Resolution

Use a matching toleration when eviction should not occur.

Timed toleration:

```yaml
tolerations:
  - key: workload
    operator: Equal
    value: database
    effect: NoExecute
    tolerationSeconds: 60
```

---

# 14. Topology Spread Prevents Scheduling

## Configuration

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: topology-demo
```

## Symptom

New Pod remains Pending.

## Troubleshooting

```bash
kubectl describe pod <pod>
kubectl get nodes --show-labels
kubectl get pods -l app=topology-demo -o wide
```

## Check

1. How many topology domains exist?
2. How are existing matching Pods distributed?
3. Is `maxSkew` too restrictive?
4. Is `DoNotSchedule` making the rule hard?
5. Does the label selector match the intended Pods?
6. Does the topology key exist on nodes?

---

# 15. Wrong Topology Key

Example:

```yaml
topologyKey: example.com/rack
```

But nodes don't have this label.

Check:

```bash
kubectl get nodes --show-labels
```

Common keys:

```text
kubernetes.io/hostname
topology.kubernetes.io/zone
```

For EKS, zone-level spreading commonly uses:

```yaml
topologyKey: topology.kubernetes.io/zone
```

provided the node topology labels are present and correct.

---

# 16. DoNotSchedule vs ScheduleAnyway

## DoNotSchedule

```yaml
whenUnsatisfiable: DoNotSchedule
```

Meaning:

> Do not place the Pod if doing so would violate the spread requirement.

Possible symptom:

```text
Pending
```

## ScheduleAnyway

```yaml
whenUnsatisfiable: ScheduleAnyway
```

Meaning:

> Prefer balanced placement, but don't block scheduling if perfect spreading isn't possible.

## Troubleshooting question

Ask:

> Is this a hard availability requirement or only a preference?

---

# 17. Pod Scheduled on Unexpected Node

Run:

```bash
kubectl get pod <pod> -o wide
```

Then:

```bash
kubectl get pod <pod> -o yaml
```

Inspect:

```text
resources.requests
nodeSelector
affinity
tolerations
topologySpreadConstraints
```

Inspect nodes:

```bash
kubectl get nodes --show-labels
```

Inspect selected node:

```bash
kubectl describe node <node>
```

## Root-cause process

```text
Actual node
   ↓
Pod rules
   ↓
Node labels
   ↓
Node taints
   ↓
Resources
   ↓
Pod relationship rules
   ↓
Topology rules
```

---

# 18. QoS Troubleshooting

Check:

```bash
kubectl get pod <pod> \
  -o jsonpath='{.status.qosClass}{"\n"}'
```

If the result is unexpected, inspect every container:

```bash
kubectl get pod <pod> -o yaml
```

Check:

```yaml
resources:
  requests:
  limits:
```

Remember:

> Guaranteed requires CPU and memory requests and limits for every container, with each request equal to its corresponding limit.

---

# 19. Resource Limit vs Request Troubleshooting

## Problem

Application is being throttled.

Check:

```yaml
limits:
  cpu:
```

CPU limits can cause throttling.

## Problem

Container is OOMKilled.

Check:

```yaml
limits:
  memory:
```

and:

```bash
kubectl describe pod <pod>
```

## Problem

Pod never schedules.

Check:

```yaml
requests:
```

because scheduler placement is primarily based on requests.

---

# 20. Real-World Incident Example — Database Node

## Requirement

Database workloads must run only on dedicated database nodes.

## Configuration

Node:

```text
workload=database:NoSchedule
```

Pod:

```yaml
tolerations:
  - key: workload
    operator: Equal
    value: database
    effect: NoSchedule

affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: workload
              operator: In
              values:
                - database
```

## Incident

Database Pod is Pending.

## Troubleshooting

```bash
kubectl describe pod <pod>
kubectl get nodes --show-labels
kubectl describe node <node>
```

Check:

```text
1. Is workload=database label present?
2. Is database taint present?
3. Does Pod have matching toleration?
4. Are resource requests available?
```

## Root cause example

Node had:

```text
workload=db
```

but Pod required:

```text
workload=database
```

## Fix

Correct the node label or Pod affinity requirement.

---

# 21. Real-World Incident Example — API Replica Availability

## Requirement

Three API replicas should not all run on one node.

## Configuration

Pod Anti-Affinity:

```yaml
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app: api
        topologyKey: kubernetes.io/hostname
```

## Troubleshooting

```bash
kubectl get pods -l app=api -o wide
kubectl get nodes
```

If all Pods are on one node, investigate:

- number of nodes
- anti-affinity type
- whether it is preferred or required
- node resources
- other scheduling constraints

## Important

Preferred anti-affinity does not guarantee separation.

If strict separation is required, use required anti-affinity or topology spread with an appropriate policy.

---

# 22. Real-World Incident Example — Multi-AZ Availability

## Requirement

Payment API replicas should be distributed across AZs.

Configuration:

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: payment-api
```

## Troubleshooting

Check:

```bash
kubectl get nodes --show-labels
kubectl get pods -l app=payment-api -o wide
kubectl describe pod <pending-pod>
```

Verify:

- nodes have correct zone labels
- enough AZs/nodes exist
- matching Pods are correctly labeled
- maxSkew is realistic
- DoNotSchedule is appropriate

---

# 23. Common Mistakes

## Mistake 1 — Assuming toleration attracts Pods

Wrong:

> "The Pod has a toleration, so Kubernetes will put it on that node."

Correct:

> Toleration permits placement but does not attract the Pod.

---

## Mistake 2 — Using hard anti-affinity on a small cluster

If:

```text
3 replicas
2 nodes
```

and hard anti-affinity requires a different node for every replica, one replica cannot be scheduled.

---

## Mistake 3 — Confusing Pod Affinity with same node

Pod Affinity depends on:

```yaml
topologyKey:
```

It can mean same node, same zone, or another topology.

---

## Mistake 4 — Assuming preferred means guaranteed

`preferred...` is not a hard requirement.

---

## Mistake 5 — Debugging only the Pod YAML

A scheduling decision depends on both:

```text
Pod configuration
+
Node state
```

Always inspect both.

---

# 24. Interview Troubleshooting Q&A

### Q: A Pod is Pending. What is your first command?

```bash
kubectl describe pod <pod>
```

I inspect scheduler Events before changing anything.

### Q: What do you check after Events?

> Node resources, node labels, nodeSelector, affinity, taints/tolerations, and topology constraints.

### Q: A Pod has a toleration but isn't using the tainted node. Why?

> A toleration only makes that node eligible. It does not force placement. I would use Node Affinity if the workload must run there.

### Q: Why is a Pod Pending with hard anti-affinity?

> There may not be another eligible topology domain. I would check the number of nodes, matching Pod labels, topology key, and scheduler Events.

### Q: How do you distribute replicas across AZs?

> Use topology spread constraints with `topology.kubernetes.io/zone`, a suitable maxSkew, and a label selector matching the workload.

### Q: How do you dedicate GPU nodes?

> Taint the GPU nodes, give GPU workloads a matching toleration, and use node affinity to ensure those workloads select GPU nodes.

### Q: How do you distinguish a scheduling memory issue from OOMKilled?

> A scheduling memory issue normally leaves the Pod Pending because its request cannot fit. OOMKilled occurs after scheduling when a running container is terminated because of memory pressure/limits.

---

# 25. Commands to Memorize

```bash
# Pod placement
kubectl get pods -o wide

# Main scheduling diagnosis
kubectl describe pod <pod>

# Node labels
kubectl get nodes --show-labels

# Selected labels
kubectl get nodes -L workload

# Node details
kubectl describe node <node>

# Full Pod configuration
kubectl get pod <pod> -o yaml

# QoS
kubectl get pod <pod> \
  -o jsonpath='{.status.qosClass}{"\n"}'

# Label a node
kubectl label node <node> key=value

# Add taint
kubectl taint nodes <node> key=value:NoSchedule

# Remove taint
kubectl taint nodes <node> key=value:NoSchedule-

# Pod labels
kubectl get pods --show-labels
```

---

# 26. Final Production Troubleshooting Framework

When a scheduling issue occurs:

```text
                 Pod Pending
                      |
                      v
          kubectl describe pod
                      |
                      v
               Read Events
                      |
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
    Resources     Node rules      Taints
        |             |             |
        ↓             ↓             ↓
  CPU/Memory     Selector/Affinity Toleration
        |             |             |
        └─────────────┼─────────────┘
                      ↓
              Pod relationship
                      |
                      ↓
             Affinity/Anti-Affinity
                      |
                      ↓
                Topology spread
                      |
                      v
                 Root cause
                      |
                      v
                    Fix
                      |
                      v
                  Verify
```

## Golden Rule

> **Never troubleshoot a Pending Pod by guessing. Start with `kubectl describe pod <pod>` and read the scheduler Events. Then compare the Pod's scheduling requirements with the actual node resources, labels, taints, topology, and other Pods.**

