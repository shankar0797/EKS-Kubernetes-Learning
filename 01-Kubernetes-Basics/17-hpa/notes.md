# Kubernetes Autoscaling — Notes

## 1. What is Autoscaling?

Autoscaling automatically adjusts Kubernetes resources according to workload demand.

Main forms:
- Horizontal scaling — change the number of Pods.
- Vertical scaling — change CPU/memory resources allocated to Pods.
- Node scaling — add/remove worker nodes.
- Event-driven scaling — scale workloads based on events such as queue depth.

---

## 2. HPA — Horizontal Pod Autoscaler

HPA automatically changes the replica count of a workload such as a Deployment.

```text
Traffic increases
      ↓
CPU increases
      ↓
Metrics Server
      ↓
HPA
      ↓
Deployment replicas increase
      ↓
More Pods
```

Important: HPA changes the desired replica count. The Deployment/ReplicaSet creates or removes Pods.

---

## 3. HPA Architecture

```text
Application Pods
      ↓
CPU / Memory usage
      ↓
Metrics Server
      ↓
HPA Controller
      ↓
Deployment replica count
      ↓
ReplicaSet
      ↓
Pods
```

Metrics Server provides resource metrics for CPU and memory.

Prometheus is not required for basic CPU/memory HPA.

---

## 4. CPU Utilization and Resource Requests

For HPA using `averageUtilization`, utilization is calculated relative to the CPU request.

Example:

```yaml
resources:
  requests:
    cpu: "100m"
```

If a Pod uses 50m:

```text
50 / 100 × 100 = 50%
```

If it uses 200m:

```text
200 / 100 × 100 = 200%
```

Therefore CPU requests are important for CPU-based HPA.

**Remember:** HPA CPU utilization is based on the resource request, not the CPU limit.

---

## 5. HPA Scale Up

Example:

```text
Target CPU = 50%
Current CPU = 150%
        ↓
HPA determines more replicas are required
```

Example progression:

```text
2 → 4 → 6 Pods
```

The exact progression depends on HPA calculations and behavior configuration.

---

## 6. minReplicas and maxReplicas

```yaml
minReplicas: 2
maxReplicas: 6
```

Meaning:
- Normally do not go below 2 replicas.
- Do not scale above 6 replicas.

If HPA wants 10 Pods but `maxReplicas` is 6, the desired count is bounded at 6.

---

## 7. HPA Scale Down

When workload decreases:

```text
CPU decreases
     ↓
HPA detects lower utilization
     ↓
Desired replicas decrease
     ↓
Deployment removes Pods
```

Example:

```text
6 → 5 → 4 → 2
```

Scale-down can intentionally be slower than scale-up to avoid repeated Pod creation/deletion.

---

## 8. Multiple Metrics

HPA can evaluate multiple metrics.

```yaml
metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50

  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70
```

HPA calculates the required replica count for each metric and uses the highest required count.

Example:

```text
CPU requires     → 4 Pods
Memory requires  → 6 Pods
                     ↓
                 HPA uses 6
```

---

## 9. Memory-based HPA

HPA can scale based on memory utilization.

```yaml
- type: Resource
  resource:
    name: memory
    target:
      type: Utilization
      averageUtilization: 70
```

Memory utilization with `Utilization` is evaluated relative to the memory request.

Example:

```text
Memory request = 500Mi
Memory usage   = 350Mi

350 / 500 × 100 = 70%
```

Memory autoscaling does not fix a memory leak; a leaking application may simply cause more Pods to be created.

---

## 10. Utilization vs AverageValue

### Utilization

Percentage relative to the resource request:

```yaml
target:
  type: Utilization
  averageUtilization: 50
```

### AverageValue

Absolute average value:

```yaml
target:
  type: AverageValue
  averageValue: 500m
```

Remember:

```text
Utilization → percentage of request
AverageValue → absolute metric value
```

---

## 11. HPA Behavior

HPA behavior controls how scaling happens.

```yaml
behavior:
  scaleUp:
    ...
  scaleDown:
    ...
```

A common production principle is:

```text
Scale up   → relatively fast
Scale down → more conservative
```

The goal is to react to demand while avoiding scaling flapping.

---

## 12. Stabilization

Rapidly changing metrics could otherwise cause:

```text
2 → 6 → 2 → 6 → 2
```

Stabilization helps prevent unnecessary scaling decisions caused by short-lived changes.

Example:

```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300
```

Concept:

> Wait and confirm that the workload really remains low before scaling down.

---

## 13. Custom Metrics

Applications may expose metrics such as:

```text
requests_per_second
active_connections
jobs_waiting
```

Architecture:

```text
Application
    ↓
Custom metric
    ↓
Metrics system / adapter
    ↓
HPA
    ↓
More/fewer Pods
```

Custom metrics require the appropriate metrics infrastructure.

---

## 14. External Metrics

External metrics originate from systems outside the normal Kubernetes resource metrics model.

Examples:
- SQS queue depth
- Kafka lag
- Azure Service Bus messages
- External application metrics

Conceptually:

```text
External system
      ↓
External metric
      ↓
HPA
      ↓
Pods
```

---

## 15. VPA — Vertical Pod Autoscaler

VPA adjusts or recommends CPU and memory resources for Pods.

Example:

```text
Current:
CPU = 100m
Memory = 256Mi

Application consistently needs:
CPU = 500m
Memory = 1Gi
```

Remember:

```text
HPA → changes number of Pods
VPA → changes/recommends Pod resources
```

---

## 16. HPA vs VPA

| Feature | HPA | VPA |
|---|---|---|
| Full name | Horizontal Pod Autoscaler | Vertical Pod Autoscaler |
| Changes | Pod count | CPU/memory resources |
| Example | 2 → 6 Pods | 100m → 500m CPU |
| Main purpose | Handle changing workload | Right-size resources |

---

## 17. Cluster Autoscaler

Cluster Autoscaler scales worker nodes.

```text
HPA needs 10 Pods
      ↓
Only enough node capacity for 6
      ↓
Some Pods remain Pending
      ↓
Cluster Autoscaler
      ↓
More worker nodes
      ↓
Pending Pods can be scheduled
```

**Remember:** HPA scales Pods. Cluster Autoscaler scales nodes.

---

## 18. Cluster Autoscaler Scale Down

```text
Workload decreases
      ↓
Nodes become unnecessary
      ↓
Cluster Autoscaler
      ↓
Unnecessary nodes removed
```

This can reduce infrastructure cost.

---

## 19. HPA + Cluster Autoscaler

```text
Traffic
   ↓
HPA
   ↓
More Pods required
   ↓
Enough node capacity?
   ├── Yes → Pods scheduled
   └── No
        ↓
   Cluster Autoscaler
        ↓
   More nodes
        ↓
   Pods scheduled
```

---

## 20. KEDA

KEDA = Kubernetes Event-driven Autoscaling.

It is useful when scaling should be driven by events such as queue depth rather than only CPU/memory.

Example:

```text
SQS Queue
   ↓
Queue depth = 5,000
   ↓
KEDA
   ↓
Worker workload scales
   ↓
More worker Pods
```

Common event sources:
- AWS SQS
- Kafka
- RabbitMQ
- Azure Service Bus
- Redis
- Prometheus metrics

---

## 21. KEDA and HPA

Conceptually:

```text
Event source
     ↓
    KEDA
     ↓
HPA-based scaling mechanism
     ↓
Deployment
     ↓
Pods
```

KEDA is particularly useful for event-driven workloads.

---

## 22. Scale to Zero

KEDA can scale event-driven workloads to zero when there is no work.

```text
Queue empty
    ↓
0 worker Pods
```

When messages arrive:

```text
New messages
    ↓
KEDA detects event
    ↓
Worker Pods start
```

---

## 23. HPA vs KEDA

| Feature | HPA | KEDA |
|---|---|---|
| CPU | Yes | Can work alongside HPA |
| Memory | Yes | Can work with metrics |
| Queue-driven scaling | Possible with appropriate metrics setup | Core use case |
| SQS | Not the natural/simple approach | Excellent use case |
| Kafka | Not the natural/simple approach | Excellent use case |
| Event-driven | Limited | Designed for it |
| Scale to zero | Not the normal HPA model | Supported |

---

## 24. Karpenter

Karpenter is an AWS-focused node provisioning technology used with EKS.

```text
HPA
 ↓
More Pods
 ↓
Insufficient node capacity
 ↓
Karpenter
 ↓
Appropriate EC2 capacity
 ↓
Pods scheduled
```

High-level comparison:

```text
HPA        → Pod count
VPA        → Pod resources
CA         → Node count
KEDA       → Event-driven workload scaling
Karpenter  → AWS node provisioning
```

Karpenter will be covered more deeply during the EKS phase.

---

## 25. Important Autoscaling Distinctions

```text
HPA
→ How many Pods?

VPA
→ How much CPU/memory should each Pod have?

Cluster Autoscaler
→ How many nodes does the cluster need?

KEDA
→ How many Pods are needed based on events?

Karpenter
→ What AWS compute capacity should be provisioned?
```

---

## 26. Hands-on HPA Lab Completed

Our lab demonstrated actual HPA scaling.

Initial:

```text
2 Pods
```

CPU workload increased:

```text
~197% CPU / 50% target
```

HPA scaled:

```text
2 → 4 → 6 Pods
```

The configured maximum was:

```yaml
maxReplicas: 6
```

Therefore the workload stopped at 6 Pods.

Important troubleshooting observation:

Initially the load-generator itself was consuming CPU while the Nginx application Pods remained around 0m CPU. HPA correctly did not scale because HPA watches the target workload's metrics, not the load-generator's CPU.

---

# 27. Autoscaling Troubleshooting Quick Reference

### HPA shows `<unknown>`

```bash
kubectl get hpa -n <namespace>
kubectl describe hpa <name> -n <namespace>
kubectl top pods -n <namespace>
kubectl get apiservice | grep metrics
```

Check Metrics Server:

```bash
kubectl get pods -n kube-system | grep metrics-server
```

### HPA doesn't scale

Check:

```bash
kubectl get hpa
kubectl describe hpa <name>
kubectl top pods
kubectl get deployment
```

Questions:
1. Is Metrics Server working?
2. Are target Pods consuming the expected resource?
3. Does the target Deployment have resource requests?
4. Is the target metric correct?
5. Is `maxReplicas` already reached?
6. Are HPA events showing errors?

### CPU is high but HPA doesn't scale

Check whether CPU is high on the **target Pods**. Do not assume the load-generator's CPU matters.

### Pods are Pending after HPA scales

```bash
kubectl get pods
kubectl describe pod <pod>
kubectl get nodes
```

Possible cause: insufficient node capacity. Cluster Autoscaler becomes relevant.

### HPA scales down slowly

This may be expected. Check:

```bash
kubectl describe hpa <name>
```

Consider stabilization window, current metrics, and HPA behavior configuration.

---

# 28. Interview Q&A

### Q1. What is HPA?
HPA automatically adjusts the number of Pods in a Kubernetes workload based on observed metrics such as CPU, memory, custom metrics, or external metrics.

### Q2. Does HPA create Pods directly?
No. HPA changes the desired replica count of the target workload. The Deployment/ReplicaSet creates or removes Pods.

### Q3. What does HPA use for CPU utilization?
CPU utilization with `Utilization` is calculated relative to the CPU resource request.

### Q4. Why are resource requests important for HPA?
Because utilization targets are calculated as a percentage of configured resource requests.

### Q5. Can HPA show 200% CPU?
Yes. If a Pod requests 100m CPU and consumes 200m, utilization is 200%.

### Q6. HPA vs VPA?
HPA changes Pod count; VPA adjusts or recommends CPU/memory resources for individual Pods.

### Q7. What is Cluster Autoscaler?
It automatically adjusts the number of worker nodes when additional capacity is required or nodes become unnecessary.

### Q8. HPA wants 10 Pods but only 6 can fit. What happens?
Additional Pods may remain Pending because there is insufficient node capacity. Cluster Autoscaler can add nodes if configured and able to satisfy scheduling requirements.

### Q9. HPA vs Cluster Autoscaler?
HPA scales application Pods; Cluster Autoscaler scales worker nodes.

### Q10. What is KEDA?
KEDA is Kubernetes Event-driven Autoscaling. It enables scaling based on event sources such as SQS queue depth, Kafka lag, RabbitMQ messages, or other supported triggers.

### Q11. When would you choose KEDA?
For event-driven workloads where scaling should follow external events such as queue messages rather than simply CPU or memory utilization.

### Q12. What is scale-to-zero?
Reducing an event-driven workload to zero Pods when there is no work and starting Pods again when demand/events appear.

### Q13. What is HPA behavior?
It controls how aggressively scaling occurs, including scale-up/scale-down policies and stabilization windows.

### Q14. Why is scale-down often slower than scale-up?
Fast scale-up protects availability during traffic spikes, while conservative scale-down helps avoid unnecessary Pod churn.

### Q15. What are custom metrics?
Application/Kubernetes-specific metrics used for autoscaling, such as requests per second, active connections, or jobs waiting.

### Q16. What are external metrics?
Metrics originating from external systems, such as queue depth in an external messaging system.

### Q17. Can HPA use multiple metrics?
Yes. HPA evaluates multiple metrics and uses the metric that requires the highest desired replica count.

### Q18. Does HPA require Prometheus?
No. Basic CPU/memory HPA uses the Kubernetes resource metrics API, commonly provided by Metrics Server. Prometheus/adapters are commonly used for custom or external metrics.

### Q19. What happens if Metrics Server is unavailable?
HPA may not receive current resource metrics and can show unknown targets or fail to make expected scaling decisions.

### Q20. What is Karpenter?
Karpenter is an AWS node provisioning solution commonly used with EKS to provision appropriate compute capacity when Pods cannot be scheduled with existing capacity.

---

# Autoscaling Cheat Sheet

```text
┌──────────────────────────────────────────────────────────────┐
│                  KUBERNETES AUTOSCALING                     │
├──────────────────────┬───────────────────────────────────────┤
│ HPA                  │ Changes Pod count                     │
│ VPA                  │ Changes/recommends Pod resources      │
│ Cluster Autoscaler   │ Changes node count                    │
│ KEDA                 │ Event-driven Pod autoscaling          │
│ Karpenter            │ AWS node provisioning                 │
└──────────────────────┴───────────────────────────────────────┘
```

### Scaling chain

```text
Metric
  ↓
Metrics API
  ↓
HPA
  ↓
Deployment
  ↓
ReplicaSet
  ↓
Pods
```

### Golden interview line

> **HPA scales Pods, VPA right-sizes Pods, Cluster Autoscaler scales nodes, and KEDA handles event-driven autoscaling.**

---

# Autoscaling Module Status

```text
HPA fundamentals              ✅
HPA architecture              ✅
CPU autoscaling               ✅
Resource requests             ✅
Scale up                      ✅
Scale down                    ✅
min/max replicas              ✅
Multiple metrics              ✅
Memory autoscaling            ✅
Utilization/AverageValue      ✅
HPA behavior                  ✅
Stabilization                 ✅
Custom metrics                ✅
External metrics              ✅
VPA                           ✅
HPA vs VPA                    ✅
Cluster Autoscaler            ✅
HPA + Cluster Autoscaler      ✅
KEDA                          ✅
KEDA vs HPA                   ✅
Karpenter                     ✅ concept
Troubleshooting               ✅
Interview Q&A                 ✅
Cheat Sheet                   ✅
```
