# Kubernetes Scheduling — Complete Notes

> **Module:** 06 — Scheduling  
> **Level:** Fundamentals → Production → Interview  
> **Environment used:** Minikube on Amazon Linux EC2

---

# 1. What is Kubernetes Scheduling?

Kubernetes Scheduling is the process of deciding **which node should run a newly created Pod**.

The Kubernetes Scheduler watches for Pods that do not yet have a node assigned and evaluates available nodes against the Pod's requirements.

## Basic flow

```text
Pod created
   |
   v
API Server
   |
   v
Scheduler notices Pod has no node
   |
   v
Evaluate nodes
   |
   +--> Resource requests
   +--> nodeSelector
   +--> Node Affinity
   +--> Taints / Tolerations
   +--> Pod Affinity
   +--> Pod Anti-Affinity
   +--> Topology Spread
   |
   v
Select suitable node
   |
   v
Bind Pod to node
   |
   v
Kubelet starts containers
```

## Why scheduling is important

In production, we may have:

- General-purpose nodes
- Database nodes
- GPU nodes
- High-memory nodes
- Different Availability Zones
- Dedicated nodes for platform components
- Different workload environments

Scheduling rules allow us to control where workloads run and how replicas are distributed.

---

# 06.1 Requests and Limits

## What problem do Requests and Limits solve?

Without resource configuration, Kubernetes does not know how much CPU or memory a workload should reserve or be allowed to consume.

For example:

```text
Node has 4 CPU and 8 Gi memory

Pod A requests:
1 CPU
2 Gi

Pod B requests:
2 CPU
4 Gi
```

The scheduler can use these requests to determine whether the Pods fit.

---

## Resource Request

A **request** represents the amount of CPU/memory Kubernetes uses for scheduling and resource accounting.

Example:

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "128Mi"
```

Meaning:

```text
CPU    = 0.25 CPU
Memory = 128 MiB
```

The scheduler primarily considers requests when deciding placement.

---

## Resource Limit

A **limit** defines the maximum resource usage allowed for a container.

```yaml
resources:
  limits:
    cpu: "500m"
    memory: "256Mi"
```

Conceptually:

```text
Request = "I need this much to be scheduled."

Limit = "Don't let me exceed this runtime limit."
```

---

## CPU Units

```text
1000m = 1 CPU
500m  = 0.5 CPU
250m  = 0.25 CPU
100m  = 0.1 CPU
```

---

## Memory Units

Common values:

```text
Mi = Mebibyte
Gi = Gibibyte
```

Example:

```text
128Mi
256Mi
1Gi
2Gi
```

---

## Basic Lab

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resources-demo
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      resources:
        requests:
          cpu: "250m"
          memory: "128Mi"
        limits:
          cpu: "500m"
          memory: "256Mi"
```

Apply:

```bash
kubectl apply -f resources-demo.yaml
```

Verify:

```bash
kubectl get pod resources-demo -o wide
kubectl describe pod resources-demo
```

---

## What happens internally?

The scheduler sees:

```text
CPU request    = 250m
Memory request = 128Mi
```

It compares these against node allocatable resources.

If a node has enough allocatable capacity and satisfies other scheduling rules, the Pod can be scheduled.

The scheduler does **not** simply look at current CPU utilization to decide whether the request fits.

---

## Failure example

```yaml
resources:
  requests:
    memory: "100Gi"
```

If no node can satisfy that request:

```text
Pod -> Pending
```

Check:

```bash
kubectl describe pod resource-pending
```

Look at:

```text
Events
```

---

## Runtime behavior

CPU reaching its limit can result in CPU throttling.

Memory exceeding the applicable limit can result in:

```text
OOMKilled
```

---

## Real-world use case

A Java application may require:

```yaml
requests:
  cpu: "500m"
  memory: "1Gi"

limits:
  cpu: "2"
  memory: "2Gi"
```

This allows the scheduler to reserve enough capacity while giving the application room to burst.

---

## Interview Q&A

### Q: Difference between request and limit?

**Answer:**

> A request is the amount of resource Kubernetes uses primarily for scheduling and accounting. A limit is the maximum resource a container can consume at runtime.

### Q: Does the scheduler use limits for placement?

**Answer:**

> Scheduling is primarily based on resource requests and node allocatable resources.

### Q: What happens if a Pod requests more memory than any node has?

**Answer:**

> The Pod remains Pending because the scheduler cannot find a suitable node.

### Q: What can happen when a container exceeds its memory limit?

**Answer:**

> The container can be terminated with OOMKilled.

---

# 06.2 QoS Classes

## What problem does QoS solve?

Kubernetes needs a way to classify Pods based on their CPU/memory configuration, especially when nodes experience resource pressure.

Kubernetes has:

```text
BestEffort
Burstable
Guaranteed
```

---

## 1. BestEffort

No CPU or memory requests or limits are specified.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: qos-besteffort
spec:
  containers:
    - name: nginx
      image: nginx:1.27
```

Check:

```bash
kubectl get pod qos-besteffort \
  -o jsonpath='{.status.qosClass}{"\n"}'
```

Expected:

```text
BestEffort
```

---

## 2. Burstable

The Pod has resource requests/limits, but does not satisfy the Guaranteed requirements.

Example:

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

Check:

```text
Burstable
```

---

## 3. Guaranteed

For every container:

- CPU request is specified
- CPU limit is specified
- Memory request is specified
- Memory limit is specified
- CPU request = CPU limit
- Memory request = memory limit

Example:

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

---

## Why does QoS matter?

Under node resource pressure, QoS classification contributes to how Kubernetes handles Pods.

Simplified mental model:

```text
BestEffort
   ↓
least resource guarantee

Burstable
   ↓
some resource guarantee

Guaranteed
   ↓
strongest resource guarantee
```

Do not confuse QoS with scheduling priority.

---

## QoS vs PriorityClass

```text
QoS
 -> resource-pressure classification

PriorityClass
 -> scheduling priority
```

They are different Kubernetes mechanisms.

---

## Verification

```bash
kubectl describe pod <pod> | grep "QoS Class"
```

or:

```bash
kubectl get pod <pod> \
  -o jsonpath='{.status.qosClass}{"\n"}'
```

---

## Real-world use case

A critical API workload can be configured with predictable CPU/memory resources.

Less critical batch workloads may use Burstable or BestEffort resources depending on requirements.

---

## Interview Q&A

### Q: What are Kubernetes QoS classes?

**Answer:**

> Kubernetes assigns Pods to BestEffort, Burstable, or Guaranteed based on CPU and memory requests and limits.

### Q: When is a Pod Guaranteed?

**Answer:**

> Every container must specify CPU and memory requests and limits, and each request must equal its corresponding limit.

### Q: Is Guaranteed the same as highest scheduling priority?

**Answer:**

> No. QoS and PriorityClass are separate concepts.

---

# 06.3 Node Selectors

## What problem does nodeSelector solve?

Sometimes a workload must run only on a particular category of node.

Example:

```text
workload=application
workload=database
workload=gpu
```

A Pod can select nodes using labels.

---

## Add a node label

```bash
kubectl label node minikube workload=application
```

Verify:

```bash
kubectl get nodes --show-labels
```

or:

```bash
kubectl get nodes -L workload
```

---

## Pod example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: node-selector-demo
spec:
  nodeSelector:
    workload: application
  containers:
    - name: nginx
      image: nginx:1.27
```

Apply:

```bash
kubectl apply -f node-selector-demo.yaml
```

Verify:

```bash
kubectl get pod node-selector-demo -o wide
```

---

## Internal behavior

Scheduler checks node labels.

```text
Pod:
workload=application

Node-1:
workload=application   -> match

Node-2:
workload=database      -> no match
```

Only matching nodes are eligible.

---

## Failure example

```yaml
nodeSelector:
  workload: database
```

If no node has:

```text
workload=database
```

the Pod remains Pending.

---

## Real-world use cases

- GPU workloads
- High-memory workloads
- Dedicated application nodes
- Environment-specific nodes
- Special hardware

---

## Limitations

`nodeSelector` is simple exact matching.

It cannot express advanced logic such as:

```text
environment is prod OR staging
```

or:

```text
prefer SSD but don't require it
```

For those requirements, use Node Affinity.

---

## Interview Q&A

### Q: What is nodeSelector?

> It is a simple Kubernetes scheduling mechanism that places a Pod only on nodes matching specified labels.

### Q: What if no node matches?

> The Pod remains Pending.

### Q: NodeSelector vs Node Affinity?

> nodeSelector provides simple exact label matching, while Node Affinity supports required/preferred rules and richer operators.

---

# 06.4 Node Affinity

## What problem does Node Affinity solve?

Node Affinity provides more expressive node selection than nodeSelector.

It supports:

- Required placement
- Preferred placement
- Multiple expressions
- Operators such as `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt`

---

## Required Node Affinity

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: required-affinity-demo
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: workload
                operator: In
                values:
                  - application
  containers:
    - name: nginx
      image: nginx:1.27
```

This is a hard requirement.

If no matching node exists:

```text
Pending
```

---

## Preferred Node Affinity

```yaml
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
            - key: workload
              operator: In
              values:
                - application
```

This is a soft preference.

The scheduler prefers matching nodes but can select another suitable node.

---

## Required + Preferred

Example:

```text
Required:
environment=production

Preferred:
disk=ssd
```

Meaning:

> Must be on production nodes, but prefer production nodes with SSD.

---

## Operators

```text
In
NotIn
Exists
DoesNotExist
Gt
Lt
```

---

## Important: IgnoredDuringExecution

The phrase:

```text
requiredDuringSchedulingIgnoredDuringExecution
```

means:

- Required when scheduling.
- If labels later change, Kubernetes does not automatically evict the running Pod solely because the affinity condition is no longer satisfied.

---

## Troubleshooting

```bash
kubectl describe pod <pod>
kubectl get nodes --show-labels
```

Compare:

```text
Affinity requirements
        vs
Node labels
```

---

## Real-world use case

Production API Pods might require:

```text
environment=production
```

and prefer:

```text
disk=ssd
```

This gives strict environment isolation while still expressing a performance preference.

---

## Interview Q&A

### Q: NodeSelector vs Node Affinity?

> NodeSelector is simple exact label matching. Node Affinity provides richer expressions and required/preferred behavior.

### Q: Required vs preferred?

> Required is a hard scheduling condition. Preferred is a soft preference.

### Q: What does IgnoredDuringExecution mean?

> A running Pod is not automatically evicted solely because node labels later stop satisfying the affinity rule.

---

# 06.5 Pod Affinity

## What problem does Pod Affinity solve?

Node Affinity asks:

```text
Which node should I run on?
```

Pod Affinity asks:

```text
Which Pods should I run close to?
```

Example:

```text
Frontend
   |
   +--> Backend
```

We may want frontend and backend Pods in the same node or Availability Zone.

---

## Example backend

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: backend-pod
  labels:
    app: backend
spec:
  containers:
    - name: backend
      image: nginx:1.27
```

---

## Frontend with required Pod Affinity

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: frontend-pod
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app: backend
          topologyKey: kubernetes.io/hostname
  containers:
    - name: frontend
      image: nginx:1.27
```

Meaning:

> Find a Pod labeled `app=backend` and schedule this Pod in the same topology domain.

Because:

```yaml
topologyKey: kubernetes.io/hostname
```

the topology domain is the node.

---

## Topology Key

This is extremely important.

```text
kubernetes.io/hostname
    -> same node

topology.kubernetes.io/zone
    -> same Availability Zone
```

Pod Affinity does not inherently mean "same node."

---

## Internal behavior

```text
backend-pod
label:
app=backend

        ↓

Scheduler searches matching Pods

        ↓

Finds backend-pod

        ↓

Evaluates topologyKey

        ↓

Chooses eligible topology domain

        ↓

Schedules frontend
```

---

## Failure example

Affinity requires:

```yaml
matchLabels:
  app: database
```

but there is no matching Pod.

The new Pod can remain Pending.

---

## Real-world use cases

- Frontend close to backend
- Application close to cache
- Latency-sensitive components
- Workloads that benefit from locality

---

## Interview Q&A

### Q: What is Pod Affinity?

> Pod Affinity allows a Pod to be scheduled close to other Pods selected by labels.

### Q: Does Pod Affinity always mean same node?

> No. `topologyKey` determines the topology domain. It can mean same node, same zone, or another topology.

### Q: What does labelSelector do?

> It identifies the Pods that the new Pod should be close to.

---

# 06.6 Pod Anti-Affinity

## What problem does it solve?

Pod Anti-Affinity prevents or discourages related Pods from being colocated.

Main use case:

> High availability.

Bad:

```text
Node-1
 ├── api-1
 ├── api-2
 └── api-3
```

Better:

```text
Node-1      Node-2      Node-3
 api-1       api-2       api-3
```

---

## Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: backend-aa-2
  labels:
    app: backend-aa
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app: backend-aa
          topologyKey: kubernetes.io/hostname
  containers:
    - name: nginx
      image: nginx:1.27
```

Meaning:

> Do not place this Pod in the same node/topology domain as matching Pods.

---

## Required vs Preferred

Required:

```text
Must stay apart.
```

Preferred:

```text
Try to stay apart.
```

Production often uses preferred anti-affinity when hard separation could prevent scheduling.

---

## Real-world use case

A 3-replica payment API can use anti-affinity to reduce the chance that a single node failure removes all replicas.

---

## Interview Q&A

### Q: Why use Pod Anti-Affinity?

> To prevent replicas or related Pods from being colocated, improving availability and workload isolation.

### Q: What happens if there are only two nodes but three replicas and hard anti-affinity requires different nodes?

> At least one Pod may remain Pending because there aren't enough topology domains to satisfy the requirement.

---

# 06.7 Taints and Tolerations

## What problem do they solve?

Sometimes we want a node to reject normal workloads.

Example:

```text
GPU Node
Database Node
System Node
```

We can taint the node.

---

## Taint

```bash
kubectl taint nodes minikube workload=database:NoSchedule
```

Conceptually:

```text
Node:
workload=database:NoSchedule

Meaning:
"Don't schedule Pods here unless they tolerate me."
```

---

## Toleration

```yaml
tolerations:
  - key: workload
    operator: Equal
    value: database
    effect: NoSchedule
```

Meaning:

> This Pod is allowed to run on the node with that taint.

---

## Critical interview point

A toleration does **not** force a Pod onto the node.

It only removes the taint as a scheduling restriction.

For dedicated placement:

```text
Taint
 +
Toleration
 +
Node Affinity
```

is a common pattern.

---

## Taint Effects

### NoSchedule

```text
New Pods without toleration -> not scheduled
```

### PreferNoSchedule

```text
Try to avoid node
but may schedule if necessary
```

### NoExecute

```text
New Pods without toleration -> rejected
Existing Pods without toleration -> can be evicted
```

---

## `tolerationSeconds`

Example:

```yaml
tolerations:
  - key: workload
    operator: Equal
    value: database
    effect: NoExecute
    tolerationSeconds: 60
```

The Pod can tolerate the matching NoExecute taint for the specified duration.

---

## Real-world EKS use case

GPU node group:

```text
workload=gpu:NoSchedule
```

Only GPU workloads get:

```yaml
tolerations:
  - key: workload
    operator: Equal
    value: gpu
    effect: NoSchedule
```

Node affinity can additionally ensure that GPU workloads actually select GPU nodes.

---

## Interview Q&A

### Q: What is a taint?

> A node-side scheduling restriction that prevents Pods without matching tolerations from being scheduled.

### Q: What is a toleration?

> A Pod-side configuration that allows it to tolerate a matching node taint.

### Q: Does a toleration force placement?

> No. It only allows placement.

### Q: Difference between NoSchedule and NoExecute?

> NoSchedule affects new scheduling. NoExecute also affects existing Pods and can cause eviction.

---

# 06.8 Pod Topology Spread Constraints

## What problem does it solve?

Topology Spread Constraints provide explicit control over how evenly Pods are distributed across topology domains.

Without controlled distribution:

```text
Node-1 = 4 Pods
Node-2 = 1 Pod
Node-3 = 1 Pod
```

Desired:

```text
Node-1 = 2
Node-2 = 2
Node-3 = 2
```

---

## Example

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: topology-demo
```

---

## Fields

### `labelSelector`

Which Pods are counted?

```yaml
labelSelector:
  matchLabels:
    app: topology-demo
```

### `topologyKey`

Where should distribution happen?

```text
kubernetes.io/hostname
    -> nodes

topology.kubernetes.io/zone
    -> Availability Zones
```

### `maxSkew`

Maximum permitted imbalance.

Example:

```text
Node-1 = 3
Node-2 = 2
Node-3 = 2

Skew = 1
```

### `whenUnsatisfiable`

`DoNotSchedule`:

> Do not schedule if the constraint cannot be satisfied.

`ScheduleAnyway`:

> Prefer the spread but schedule if necessary.

---

## Real-world EKS use case

For a production payment API:

```yaml
topologyKey: topology.kubernetes.io/zone
```

can distribute replicas across AZs.

Example:

```text
AZ-A       AZ-B       AZ-C
 2          2          2
Pods       Pods       Pods
```

This improves resilience against AZ-level failure.

---

## Topology Spread vs Anti-Affinity

### Anti-Affinity

```text
"Don't put matching Pods together."
```

### Topology Spread

```text
"Keep matching Pods distributed with controlled skew."
```

Topology Spread is particularly useful when you want explicit balancing rather than only separation.

---

## Interview Q&A

### Q: What are topology spread constraints?

> They control how evenly matching Pods are distributed across topology domains such as nodes or Availability Zones.

### Q: What does maxSkew mean?

> It defines the maximum allowed difference in the number of matching Pods between topology domains under the constraint.

### Q: How do you spread Pods across AZs?

> Use `topology.kubernetes.io/zone` as the topology key, together with an appropriate maxSkew and label selector.

---

# Scheduling Comparison

| Feature | Main Question |
|---|---|
| Requests | Can the Pod fit? |
| Limits | How much can it consume? |
| QoS | What resource class is it? |
| nodeSelector | Which exact labeled nodes? |
| Node Affinity | Which nodes are required/preferred? |
| Pod Affinity | Which Pods should I be near? |
| Pod Anti-Affinity | Which Pods should I avoid? |
| Taint | Which Pods should stay away? |
| Toleration | Which taints can I tolerate? |
| Topology Spread | How evenly should replicas be distributed? |

---

# Production Scheduling Example

Imagine an EKS production application:

```text
                    EKS
                     |
        ┌────────────┼────────────┐
        ↓            ↓            ↓
       AZ-A         AZ-B         AZ-C
        |            |            |
      Nodes        Nodes        Nodes
        |            |            |
      API Pods     API Pods     API Pods
```

We may use:

```text
Requests/limits
    +
Node Affinity
    +
Taints/Tolerations
    +
Pod Anti-Affinity
    +
Topology Spread
```

to achieve:

- predictable resources
- dedicated nodes
- replica separation
- AZ-level resilience
- controlled workload placement

---

# Scheduling Interview Q&A — Final Set

## Q1. What is Kubernetes Scheduler?

> The scheduler watches for unscheduled Pods and selects an appropriate node based on resource requirements and scheduling constraints.

## Q2. What is the difference between request and limit?

> Request is primarily used for scheduling; limit is the runtime maximum.

## Q3. What is nodeSelector?

> Simple exact node-label matching.

## Q4. What is Node Affinity?

> A more expressive node-placement mechanism supporting required and preferred rules.

## Q5. What is Pod Affinity?

> It places a Pod close to other Pods selected by labels.

## Q6. What is Pod Anti-Affinity?

> It prevents or discourages matching Pods from being colocated.

## Q7. What are taints and tolerations?

> Taints restrict nodes; tolerations allow Pods to tolerate matching taints.

## Q8. Does toleration force a Pod onto a node?

> No. It only makes the node eligible with respect to that taint.

## Q9. Why use Pod Anti-Affinity?

> To improve high availability by separating replicas.

## Q10. Why use topology spread?

> To control balanced distribution across nodes or Availability Zones.

## Q11. How do you troubleshoot a Pending Pod?

```bash
kubectl describe pod <pod>
```

Then inspect scheduler Events, resources, selectors, affinity, taints/tolerations, and topology constraints.

## Q12. How do you dedicate nodes to a workload?

> Use a node taint to reject unwanted workloads, a matching toleration for the intended workload, and node affinity to ensure the workload actually selects those nodes.

---

# Final Memory Map

```text
RESOURCE
Requests / Limits
       |
       v
NODE SELECTION
nodeSelector / Node Affinity
       |
       v
NODE RESTRICTION
Taints / Tolerations
       |
       v
POD RELATIONSHIP
Pod Affinity / Anti-Affinity
       |
       v
DISTRIBUTION
Topology Spread
       |
       v
SCHEDULER
       |
       v
NODE
```

