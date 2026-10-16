# Kubernetes Autoscaling — Troubleshooting

## 1. HPA shows `<unknown>`

### Symptoms

```text
NAME       TARGETS
hpa-demo   <unknown>/50%
```

### Check

```bash
kubectl get hpa -n <namespace>
kubectl describe hpa <name> -n <namespace>
kubectl top pods -n <namespace>
kubectl get apiservice | grep metrics
kubectl get pods -n kube-system | grep metrics-server
```

### Common causes

- Metrics Server unavailable.
- Metrics API unavailable.
- Metrics Server cannot reach kubelets.
- Pods have missing resource requests for a utilization-based target.
- Target workload or metric configuration is incorrect.

---

## 2. HPA is not scaling

### Check the HPA

```bash
kubectl get hpa -n <namespace>
kubectl describe hpa <name> -n <namespace>
```

Look at:

```text
TARGETS
REPLICAS
MINPODS
MAXPODS
Events
```

### Check actual Pod metrics

```bash
kubectl top pods -n <namespace>
```

### Check Deployment

```bash
kubectl get deployment -n <namespace>
```

### Verify

1. Metrics Server is healthy.
2. Target Pods are actually consuming CPU/memory.
3. Resource requests exist.
4. Target metric is correct.
5. `maxReplicas` has not already been reached.
6. HPA events do not show errors.

---

## 3. Load generator is using CPU but HPA does not scale

This happened during our lab.

Observed:

```text
load-generator     542m
hpa-demo Pods         0m
```

HPA watches the target Deployment's Pods, not the load-generator's CPU.

### Lesson

Always check:

```bash
kubectl top pods -n hpa-lab
```

and identify which Pods are actually consuming the resource.

---

## 4. HPA reaches maxReplicas

Example:

```text
TARGETS    197%/50%
REPLICAS   6
MAXPODS    6
```

This is not necessarily an error.

The workload needs more capacity, but:

```text
maxReplicas = 6
```

prevents HPA from going higher.

### Check

```bash
kubectl describe hpa hpa-demo -n hpa-lab
```

### Possible production actions

- Review whether `maxReplicas` is appropriate.
- Check cluster capacity.
- Check application performance.
- Check whether another bottleneck exists.
- Do not blindly increase the maximum without understanding the workload.

---

## 5. HPA scales but Pods remain Pending

### Symptoms

```bash
kubectl get pods
```

shows:

```text
Pending
```

### Check

```bash
kubectl describe pod <pod-name>
kubectl get nodes
```

Look for scheduler messages such as insufficient CPU or memory.

### Likely architecture

```text
HPA
 ↓
More Pods
 ↓
No node capacity
 ↓
Pods Pending
 ↓
Cluster Autoscaler/Karpenter
 ↓
More node capacity
```

---

## 6. HPA scales down slowly

This can be expected.

### Why?

HPA can use stabilization and scaling behavior to avoid reacting to short-lived drops in workload.

Check:

```bash
kubectl describe hpa <name>
```

Review:

- Current metrics.
- Desired replicas.
- Behavior configuration.
- Stabilization windows.

### Production lesson

Fast scale-up and conservative scale-down can protect availability and prevent scaling flapping.

---

## 7. HPA keeps scaling up and down

### Symptom

```text
2 → 6 → 2 → 6 → 2
```

### Possible causes

- Workload fluctuates around the target.
- Scaling behavior is too aggressive.
- Stabilization is insufficient.
- Target metric is noisy.
- Application has a bursty workload.

### Check

```bash
kubectl describe hpa <name>
```

Review the `behavior` configuration.

Example:

```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300
```

---

## 8. CPU utilization is unexpectedly high

Remember that utilization is relative to the request.

Example:

```text
CPU request = 100m
CPU usage   = 200m
```

Therefore:

```text
200 / 100 × 100 = 200%
```

High percentage does not automatically mean the node is using 200% of a physical CPU core.

---

## 9. CPU utilization is not available as expected

Check resource requests:

```bash
kubectl get deployment <name> -o yaml
```

Look for:

```yaml
resources:
  requests:
    cpu: ...
```

For utilization-based HPA, requests are critical.

---

## 10. Metrics Server troubleshooting

Check:

```bash
kubectl get pods -n kube-system | grep metrics-server
kubectl get apiservice | grep metrics
kubectl top nodes
kubectl top pods -A
```

If `kubectl top` fails, investigate Metrics Server and the resource metrics API before blaming HPA.

---

## 11. Custom metric HPA troubleshooting

If CPU/memory works but a custom metric does not:

Check:

```bash
kubectl describe hpa <name>
```

Verify:

- Custom metrics API is available.
- Metric name is correct.
- Metric is being exposed.
- Adapter/metrics infrastructure is healthy.
- Namespace/labels/selectors match the metric configuration.

---

## 12. External metric troubleshooting

For external metrics such as queue depth:

Verify:

1. External system is reachable.
2. Authentication/permissions are correct.
3. Metric exists.
4. Metric value is being returned.
5. HPA/KEDA configuration references the correct trigger.
6. Target workload is correct.

---

## 13. KEDA troubleshooting

Typical flow:

```text
Event source
    ↓
KEDA
    ↓
Scaling mechanism
    ↓
Deployment
    ↓
Pods
```

Check the workload and KEDA resources:

```bash
kubectl get pods -A
kubectl get scaledobject -A
kubectl describe scaledobject <name> -n <namespace>
```

Also verify the event source, credentials, and trigger configuration.

---

## 14. HPA vs Cluster Autoscaler troubleshooting

Do not confuse these two.

### HPA problem

```text
Application needs more Pods
```

Investigate:

```text
HPA
Metrics
Deployment
Pods
```

### Cluster capacity problem

```text
Pods cannot be scheduled
```

Investigate:

```text
Nodes
Scheduler events
Node resources
Cluster Autoscaler/Karpenter
```

---

## 15. Practical troubleshooting sequence

When HPA is not behaving as expected:

```text
1. kubectl get hpa
        ↓
2. kubectl describe hpa
        ↓
3. kubectl top pods
        ↓
4. kubectl get deployment
        ↓
5. Check resource requests
        ↓
6. Check Metrics Server
        ↓
7. Check HPA events
        ↓
8. Check Pod status/events
        ↓
9. Check node capacity
        ↓
10. Check Cluster Autoscaler/Karpenter if needed
```

---

## 16. Important interview troubleshooting scenario

### Question

> HPA shows high CPU but the application is not scaling. What would you check?

### Answer

> First I would check `kubectl get hpa` and `kubectl describe hpa` to inspect the target, desired replicas, limits, and events. Then I would check `kubectl top pods` to confirm that the target Pods, not a load-generator, are consuming CPU. I would verify resource requests, Metrics Server health, HPA behavior, and whether `maxReplicas` has already been reached. If new Pods are being created but remain Pending, I would then investigate node capacity and Cluster Autoscaler/Karpenter.

---

## 17. Key commands

```bash
kubectl get hpa -n <namespace>

kubectl describe hpa <name> -n <namespace>

kubectl top pods -n <namespace>

kubectl top nodes

kubectl get deployment -n <namespace>

kubectl describe pod <pod-name> -n <namespace>

kubectl get apiservice | grep metrics

kubectl get pods -n kube-system | grep metrics-server

kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

---

## 18. Golden troubleshooting rule

Never troubleshoot HPA in isolation.

Think about the complete chain:

```text
Workload
   ↓
Resource usage
   ↓
Metrics collection
   ↓
HPA calculation
   ↓
Desired replicas
   ↓
Deployment/ReplicaSet
   ↓
Pod scheduling
   ↓
Node capacity
```

A failure anywhere in this chain can appear as an "HPA problem".
# Kubernetes Autoscaling — Troubleshooting

## 1. HPA shows `<unknown>`

### Symptoms

```text
NAME       TARGETS
hpa-demo   <unknown>/50%
```

### Check

```bash
kubectl get hpa -n <namespace>
kubectl describe hpa <name> -n <namespace>
kubectl top pods -n <namespace>
kubectl get apiservice | grep metrics
kubectl get pods -n kube-system | grep metrics-server
```

### Common causes

- Metrics Server unavailable.
- Metrics API unavailable.
- Metrics Server cannot reach kubelets.
- Pods have missing resource requests for a utilization-based target.
- Target workload or metric configuration is incorrect.

---

## 2. HPA is not scaling

### Check the HPA

```bash
kubectl get hpa -n <namespace>
kubectl describe hpa <name> -n <namespace>
```

Look at:

```text
TARGETS
REPLICAS
MINPODS
MAXPODS
Events
```

### Check actual Pod metrics

```bash
kubectl top pods -n <namespace>
```

### Check Deployment

```bash
kubectl get deployment -n <namespace>
```

### Verify

1. Metrics Server is healthy.
2. Target Pods are actually consuming CPU/memory.
3. Resource requests exist.
4. Target metric is correct.
5. `maxReplicas` has not already been reached.
6. HPA events do not show errors.

---

## 3. Load generator is using CPU but HPA does not scale

This happened during our lab.

Observed:

```text
load-generator     542m
hpa-demo Pods         0m
```

HPA watches the target Deployment's Pods, not the load-generator's CPU.

### Lesson

Always check:

```bash
kubectl top pods -n hpa-lab
```

and identify which Pods are actually consuming the resource.

---

## 4. HPA reaches maxReplicas

Example:

```text
TARGETS    197%/50%
REPLICAS   6
MAXPODS    6
```

This is not necessarily an error.

The workload needs more capacity, but:

```text
maxReplicas = 6
```

prevents HPA from going higher.

### Check

```bash
kubectl describe hpa hpa-demo -n hpa-lab
```

### Possible production actions

- Review whether `maxReplicas` is appropriate.
- Check cluster capacity.
- Check application performance.
- Check whether another bottleneck exists.
- Do not blindly increase the maximum without understanding the workload.

---

## 5. HPA scales but Pods remain Pending

### Symptoms

```bash
kubectl get pods
```

shows:

```text
Pending
```

### Check

```bash
kubectl describe pod <pod-name>
kubectl get nodes
```

Look for scheduler messages such as insufficient CPU or memory.

### Likely architecture

```text
HPA
 ↓
More Pods
 ↓
No node capacity
 ↓
Pods Pending
 ↓
Cluster Autoscaler/Karpenter
 ↓
More node capacity
```

---

## 6. HPA scales down slowly

This can be expected.

### Why?

HPA can use stabilization and scaling behavior to avoid reacting to short-lived drops in workload.

Check:

```bash
kubectl describe hpa <name>
```

Review:

- Current metrics.
- Desired replicas.
- Behavior configuration.
- Stabilization windows.

### Production lesson

Fast scale-up and conservative scale-down can protect availability and prevent scaling flapping.

---

## 7. HPA keeps scaling up and down

### Symptom

```text
2 → 6 → 2 → 6 → 2
```

### Possible causes

- Workload fluctuates around the target.
- Scaling behavior is too aggressive.
- Stabilization is insufficient.
- Target metric is noisy.
- Application has a bursty workload.

### Check

```bash
kubectl describe hpa <name>
```

Review the `behavior` configuration.

Example:

```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300
```

---

## 8. CPU utilization is unexpectedly high

Remember that utilization is relative to the request.

Example:

```text
CPU request = 100m
CPU usage   = 200m
```

Therefore:

```text
200 / 100 × 100 = 200%
```

High percentage does not automatically mean the node is using 200% of a physical CPU core.

---

## 9. CPU utilization is not available as expected

Check resource requests:

```bash
kubectl get deployment <name> -o yaml
```

Look for:

```yaml
resources:
  requests:
    cpu: ...
```

For utilization-based HPA, requests are critical.

---

## 10. Metrics Server troubleshooting

Check:

```bash
kubectl get pods -n kube-system | grep metrics-server
kubectl get apiservice | grep metrics
kubectl top nodes
kubectl top pods -A
```

If `kubectl top` fails, investigate Metrics Server and the resource metrics API before blaming HPA.

---

## 11. Custom metric HPA troubleshooting

If CPU/memory works but a custom metric does not:

Check:

```bash
kubectl describe hpa <name>
```

Verify:

- Custom metrics API is available.
- Metric name is correct.
- Metric is being exposed.
- Adapter/metrics infrastructure is healthy.
- Namespace/labels/selectors match the metric configuration.

---

## 12. External metric troubleshooting

For external metrics such as queue depth:

Verify:

1. External system is reachable.
2. Authentication/permissions are correct.
3. Metric exists.
4. Metric value is being returned.
5. HPA/KEDA configuration references the correct trigger.
6. Target workload is correct.

---

## 13. KEDA troubleshooting

Typical flow:

```text
Event source
    ↓
KEDA
    ↓
Scaling mechanism
    ↓
Deployment
    ↓
Pods
```

Check the workload and KEDA resources:

```bash
kubectl get pods -A
kubectl get scaledobject -A
kubectl describe scaledobject <name> -n <namespace>
```

Also verify the event source, credentials, and trigger configuration.

---

## 14. HPA vs Cluster Autoscaler troubleshooting

Do not confuse these two.

### HPA problem

```text
Application needs more Pods
```

Investigate:

```text
HPA
Metrics
Deployment
Pods
```

### Cluster capacity problem

```text
Pods cannot be scheduled
```

Investigate:

```text
Nodes
Scheduler events
Node resources
Cluster Autoscaler/Karpenter
```

---

## 15. Practical troubleshooting sequence

When HPA is not behaving as expected:

```text
1. kubectl get hpa
        ↓
2. kubectl describe hpa
        ↓
3. kubectl top pods
        ↓
4. kubectl get deployment
        ↓
5. Check resource requests
        ↓
6. Check Metrics Server
        ↓
7. Check HPA events
        ↓
8. Check Pod status/events
        ↓
9. Check node capacity
        ↓
10. Check Cluster Autoscaler/Karpenter if needed
```

---

## 16. Important interview troubleshooting scenario

### Question

> HPA shows high CPU but the application is not scaling. What would you check?

### Answer

> First I would check `kubectl get hpa` and `kubectl describe hpa` to inspect the target, desired replicas, limits, and events. Then I would check `kubectl top pods` to confirm that the target Pods, not a load-generator, are consuming CPU. I would verify resource requests, Metrics Server health, HPA behavior, and whether `maxReplicas` has already been reached. If new Pods are being created but remain Pending, I would then investigate node capacity and Cluster Autoscaler/Karpenter.

---

## 17. Key commands

```bash
kubectl get hpa -n <namespace>

kubectl describe hpa <name> -n <namespace>

kubectl top pods -n <namespace>

kubectl top nodes

kubectl get deployment -n <namespace>

kubectl describe pod <pod-name> -n <namespace>

kubectl get apiservice | grep metrics

kubectl get pods -n kube-system | grep metrics-server

kubectl get events -n <namespace> --sort-by=.lastTimestamp
```

---

## 18. Golden troubleshooting rule

Never troubleshoot HPA in isolation.

Think about the complete chain:

```text
Workload
   ↓
Resource usage
   ↓
Metrics collection
   ↓
HPA calculation
   ↓
Desired replicas
   ↓
Deployment/ReplicaSet
   ↓
Pod scheduling
   ↓
Node capacity
```

A failure anywhere in this chain can appear as an "HPA problem".

