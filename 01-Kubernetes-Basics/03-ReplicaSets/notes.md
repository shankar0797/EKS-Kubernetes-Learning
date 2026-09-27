# Kubernetes ReplicaSet

## 1. What is a ReplicaSet?

A ReplicaSet is a Kubernetes controller that maintains a desired number of identical Pod replicas.

Example:

```text
ReplicaSet
    |
    ├── Pod
    ├── Pod
    └── Pod
```

If the desired replica count is 3, the ReplicaSet continuously tries to maintain 3 matching Pods.

---

# 2. Why do we use ReplicaSets?

A standalone Pod does not provide workload-level self-healing.

If we delete a standalone Pod:

```text
Pod
 ↓
Deleted
 ↓
Gone
```

A ReplicaSet maintains the desired number of Pods:

```text
ReplicaSet
Desired = 3
Actual  = 3

Delete one Pod
      ↓
Actual = 2
      ↓
ReplicaSet controller detects difference
      ↓
Creates replacement Pod
      ↓
Actual = 3
```

---

# 3. Desired State vs Actual State

This is one of the most important Kubernetes concepts.

Desired state:

```text
replicas: 3
```

Actual state:

```text
Currently running: 3 Pods
```

Healthy:

```text
Desired = 3
Actual  = 3
```

If a Pod is deleted:

```text
Desired = 3
Actual  = 2
```

The ReplicaSet reconciles the difference.

---

# 4. Reconciliation Loop

Kubernetes controllers continuously compare desired state with actual state.

```text
Desired State
     |
     v
Controller
     |
     v
Actual State
     |
     v
Difference?
     |
    Yes
     |
     v
Take corrective action
```

For a ReplicaSet:

```text
Desired = 3
Actual = 2
     |
     v
Create Pod
     |
     v
Actual = 3
```

This reconciliation model is fundamental to Kubernetes.

---

# 5. ReplicaSet Architecture

Our lab:

```text
ReplicaSet
    |
    ├── nginx Pod
    ├── nginx Pod
    └── nginx Pod
```

The ReplicaSet uses labels and selectors to identify its Pods.

```text
ReplicaSet selector
       |
       | app=nginx
       v
Pod labels
       |
       | app=nginx
       v
Managed Pod
```

---

# 6. ReplicaSet Manifest

File:

```text
nginx-replicaset.yaml
```

```yaml
apiVersion: apps/v1
kind: ReplicaSet

metadata:
  name: nginx-replicaset

spec:
  replicas: 3

  selector:
    matchLabels:
      app: nginx

  template:
    metadata:
      labels:
        app: nginx

    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
```

---

# 7. Important ReplicaSet YAML Sections

## apiVersion

```yaml
apiVersion: apps/v1
```

Specifies the Kubernetes API version for the ReplicaSet resource.

## kind

```yaml
kind: ReplicaSet
```

Specifies that the resource is a ReplicaSet.

## replicas

```yaml
replicas: 3
```

Defines the desired number of Pods.

## selector

```yaml
selector:
  matchLabels:
    app: nginx
```

Defines which Pods the ReplicaSet manages.

## template

```yaml
template:
```

Defines the blueprint used to create Pods.

## Pod labels

```yaml
labels:
  app: nginx
```

The labels must match the ReplicaSet selector.

---

# 8. Create the ReplicaSet

```bash
kubectl apply -f nginx-replicaset.yaml
```

Expected:

```text
replicaset.apps/nginx-replicaset created
```

---

# 9. Verify the ReplicaSet

```bash
kubectl get rs
```

Example:

```text
NAME               DESIRED   CURRENT   READY
nginx-replicaset   3         3         3
```

Meaning:

```text
DESIRED = desired number of Pods
CURRENT = Pods currently created
READY   = Pods currently ready
```

---

# 10. View ReplicaSet Pods

```bash
kubectl get pods -o wide
```

The ReplicaSet automatically creates the required Pods.

---

# 11. Verify Pod Ownership

```bash
kubectl describe pod <pod-name>
```

Look for:

```text
Controlled By: ReplicaSet/nginx-replicaset
```

We also verified the Kubernetes metadata directly:

```bash
kubectl get pod <pod-name> \
-o jsonpath='{.metadata.ownerReferences[0].kind}{" / "}{.metadata.ownerReferences[0].name}{"\n"}'
```

Result:

```text
ReplicaSet / nginx-replicaset
```

This confirms that the Pod has an owner reference pointing to the ReplicaSet.

---

# 12. Self-Healing Experiment

We intentionally deleted a ReplicaSet-managed Pod.

```bash
kubectl delete pod <pod-name>
```

Before deletion:

```text
Desired = 2
Current = 2
Ready   = 2
```

After deletion:

```text
Desired = 2
Current = 1
```

The ReplicaSet controller detected the difference and created a replacement.

Final state:

```text
Desired = 2
Current = 2
Ready   = 2
```

The replacement Pod received:

* A new Pod name
* A new Pod IP
* A new Pod UID

This demonstrates that Pods are ephemeral.

---

# 13. Pod Names and IPs Are Not Permanent

Example:

```text
Old Pod:
nginx-replicaset-psc5z
IP: 10.244.0.4

New Pod:
nginx-replicaset-zzdvx
IP: 10.244.0.10
```

Therefore, applications should not depend on individual Pod names or IP addresses.

A Kubernetes Service provides a stable endpoint for accessing Pods.

---

# 14. Labels and Selectors

Our ReplicaSet uses:

```text
Selector:
app=nginx
```

Its Pods have:

```text
Label:
app=nginx
```

We verified:

```bash
kubectl get pods --show-labels
```

Example:

```text
nginx-replicaset-sknqc   app=nginx
nginx-replicaset-zzdvx   app=nginx
```

---

# 15. Independent Pod Experiment

We created:

```yaml
metadata:
  name: independent-nginx
  labels:
    app: web
```

The ReplicaSet selector was:

```text
app=nginx
```

The independent Pod was:

```text
app=web
```

Therefore, the ReplicaSet did not manage the independent Pod.

This demonstrated that controllers use selectors to identify the Pods they manage.

---

# 16. Important Selector Rule

For an `apps/v1` ReplicaSet, the selector must match the labels in the Pod template.

Correct:

```yaml
selector:
  matchLabels:
    app: nginx

template:
  metadata:
    labels:
      app: nginx
```

Incorrect:

```yaml
selector:
  matchLabels:
    app: nginx

template:
  metadata:
    labels:
      app: web
```

The API server rejects an invalid ReplicaSet definition where the selector does not match the template labels.

---

# 17. Scaling a ReplicaSet

Using the manifest:

```yaml
replicas: 5
```

Then:

```bash
kubectl apply -f nginx-replicaset.yaml
```

Or imperatively:

```bash
kubectl scale replicaset nginx-replicaset --replicas=5
```

Verify:

```bash
kubectl get rs
kubectl get pods
```

---

# 18. Important Commands

Create/update:

```bash
kubectl apply -f nginx-replicaset.yaml
```

List ReplicaSets:

```bash
kubectl get rs
```

Detailed information:

```bash
kubectl describe rs nginx-replicaset
```

List Pods:

```bash
kubectl get pods
```

List Pods with labels:

```bash
kubectl get pods --show-labels
```

Scale:

```bash
kubectl scale rs nginx-replicaset --replicas=3
```

View events:

```bash
kubectl get events --sort-by=.lastTimestamp
```

Check Pod owner:

```bash
kubectl get pod <pod-name> \
-o jsonpath='{.metadata.ownerReferences[0].kind}{" / "}{.metadata.ownerReferences[0].name}{"\n"}'
```

---

# 19. ReplicaSet vs Standalone Pod

| Standalone Pod                   | ReplicaSet                          |
| -------------------------------- | ----------------------------------- |
| Individual Pod                   | Controller                          |
| No replica management            | Maintains desired replicas          |
| No automatic replacement         | Automatically replaces deleted Pods |
| Pod can disappear permanently    | Controller maintains desired count  |
| Mostly useful for simple testing | Used as a workload controller       |

---

# 20. ReplicaSet vs Deployment

A ReplicaSet primarily manages the desired number of Pods.

A Deployment provides higher-level workload management such as:

* Rolling updates
* Rollbacks
* Revision history
* Deployment strategies
* Rollout status

Relationship:

```text
Deployment
     |
     v
ReplicaSet
     |
     ├── Pod
     ├── Pod
     └── Pod
```

In normal production workloads, we generally create a Deployment rather than managing a ReplicaSet directly.

---

# 21. Production Troubleshooting Workflow

If a ReplicaSet is not maintaining the expected number of Pods:

```bash
kubectl get rs
```

Then:

```bash
kubectl describe rs <replicaset-name>
```

Check:

```text
Events
```

Then:

```bash
kubectl get pods
```

Inspect individual Pods:

```bash
kubectl describe pod <pod-name>
```

Check recent events:

```bash
kubectl get events --sort-by=.lastTimestamp
```

If scheduling appears to be the issue:

```bash
kubectl get nodes
kubectl describe node <node-name>
```

---

# 22. Real Production Scenario — Replica Count Lower Than Desired

### Scenario

A production ReplicaSet shows:

```text
DESIRED   CURRENT   READY
3         2         2
```

### Investigation

First:

```bash
kubectl describe rs <replicaset-name>
```

Then:

```bash
kubectl get pods
```

Then:

```bash
kubectl get events --sort-by=.lastTimestamp
```

Potential causes include:

* Insufficient CPU
* Insufficient memory
* Node unavailable
* Taints
* Node selectors
* Affinity rules
* Resource quotas
* Scheduling constraints

The key is to determine **why the controller cannot reach the desired state** rather than simply restarting Pods.

---

# 23. Real Production Scenario — Pod Deleted Automatically

### Scenario

A developer says:

> "I deleted a Pod, but Kubernetes created another Pod automatically."

### Investigation

```bash
kubectl describe pod <pod-name>
```

Look for:

```text
Controlled By: ReplicaSet/<name>
```

Then:

```bash
kubectl get rs
```

The ReplicaSet is maintaining the configured replica count.

### Interview answer

"The Pod was controlled by a ReplicaSet. When I deleted it, the ReplicaSet controller detected that the actual number of Pods was lower than the desired replica count and created a replacement."

---

# 24. Real Production Scenario — Pods Exist but Are Not Ready

Example:

```text
DESIRED   CURRENT   READY
3         3         0
```

The ReplicaSet successfully created three Pods, but none are Ready.

Investigation:

```bash
kubectl get pods
```

Then:

```bash
kubectl describe pod <pod-name>
```

Then:

```bash
kubectl logs <pod-name>
```

Possible causes:

* ImagePullBackOff
* CrashLoopBackOff
* Readiness probe failure
* Container startup failure
* Application configuration error

The troubleshooting path is:

```text
ReplicaSet
    ↓
Pods exist
    ↓
Pods not Ready
    ↓
Investigate individual Pod
    ↓
Container
    ↓
Application
```

---

# 25. Real Production Scenario — Events

Command:

```bash
kubectl get events --sort-by=.lastTimestamp
```

Useful events include:

```text
SuccessfulCreate
SuccessfulDelete
Scheduled
Pulling
Pulled
Created
Started
Failed
BackOff
```

Events help determine what Kubernetes controllers and kubelet are doing.

Events are useful for troubleshooting but are not a replacement for application logs or centralized observability.

---

# 26. Interview Questions & Answers

## Q1. What is a ReplicaSet?

A ReplicaSet is a Kubernetes controller that maintains a specified number of identical Pod replicas.

---

## Q2. Why do we need a ReplicaSet?

A ReplicaSet provides replica management and self-healing. If a managed Pod is deleted or becomes unavailable, the ReplicaSet attempts to maintain the desired number of Pods.

---

## Q3. How does a ReplicaSet know which Pods it manages?

It uses a label selector.

For example:

```text
selector:
app=nginx
```

Pods with matching labels are associated with the ReplicaSet.

---

## Q4. What happens when you delete a ReplicaSet-managed Pod?

The ReplicaSet controller detects that the actual replica count is below the desired count and creates a replacement Pod.

---

## Q5. Does the replacement Pod have the same IP?

No.

Pods are ephemeral. A replacement Pod normally receives a new Pod IP.

---

## Q6. Does the replacement Pod have the same name?

No. The replacement receives a different Pod name.

---

## Q7. How do you find who owns a Pod?

I can use:

```bash
kubectl describe pod <pod-name>
```

and look for:

```text
Controlled By
```

Or inspect the owner reference:

```bash
kubectl get pod <pod-name> \
-o jsonpath='{.metadata.ownerReferences[0].kind}{" / "}{.metadata.ownerReferences[0].name}{"\n"}'
```

---

## Q8. What is the difference between desired, current and ready replicas?

**Desired** is the number configured in the ReplicaSet.

**Current** is the number of Pods currently created.

**Ready** is the number of Pods currently considered Ready.

Example:

```text
DESIRED = 3
CURRENT = 3
READY   = 2
```

Three Pods exist, but only two are Ready.

---

## Q9. What happens if a ReplicaSet cannot create the desired number of Pods?

I would check:

```bash
kubectl describe rs <name>
kubectl get pods
kubectl get events --sort-by=.lastTimestamp
```

Then investigate scheduling, resources, node conditions, taints, affinity, quotas, image problems, or other constraints.

---

## Q10. ReplicaSet vs Deployment?

A ReplicaSet maintains the desired number of Pods.

A Deployment manages ReplicaSets and provides higher-level capabilities such as rolling updates, rollbacks, revision history, and rollout management.

---

## Q11. Do we normally create ReplicaSets directly in production?

Usually no. Deployments are generally used for stateless application workloads because the Deployment provides rollout and revision management while managing ReplicaSets underneath.

---

## Q12. What is the relationship between Deployment, ReplicaSet and Pod?

```text
Deployment
    ↓
ReplicaSet
    ↓
Pod
```

The Deployment manages ReplicaSets, and the ReplicaSet manages Pods.

---

## Q13. What is reconciliation in Kubernetes?

Reconciliation is the process where Kubernetes controllers continuously compare the desired state with the actual state and take corrective actions when they differ.

---

## Q14. A developer deleted a Pod and says Kubernetes is "creating unwanted Pods." What would you explain?

I would first check whether the Pod is controlled by a ReplicaSet or Deployment. If it is, Kubernetes is behaving as designed: the controller is maintaining the configured desired replica count.

---

## Q15. How would you troubleshoot a ReplicaSet showing `DESIRED=3`, `CURRENT=2`?

I would:

```bash
kubectl get rs
kubectl describe rs <name>
kubectl get pods
kubectl get events --sort-by=.lastTimestamp
```

Then investigate why the third Pod cannot be created or scheduled, such as insufficient node resources, taints, affinity rules, quotas, or other scheduling constraints.

---

# 27. Interview Scenario — Production Application

### Question

> You have an application with 5 replicas. One Pod crashes. What happens?

### Answer

If the application is managed by a Deployment/ReplicaSet, the controller detects that the actual number of available replicas has fallen below the desired state and attempts to create a replacement Pod.

I would verify with:

```bash
kubectl get deployment
kubectl get rs
kubectl get pods
```

Then investigate the failed Pod using:

```bash
kubectl describe pod <pod>
kubectl logs <pod>
```

to determine why the original Pod failed.

---

# 28. Lab Completed

* [x] Create ReplicaSet
* [x] Create multiple Pods
* [x] Understand desired/current/ready
* [x] Verify labels
* [x] Verify selectors
* [x] Verify Pod ownership
* [x] Delete managed Pod
* [x] Observe automatic replacement
* [x] Observe new Pod name
* [x] Observe new Pod IP
* [x] Create independent Pod
* [x] Prove selector behavior
* [x] Scale ReplicaSet
* [x] Investigate Events
* [x] Practice production troubleshooting
* [x] Prepare interview scenarios

## Next Topic

**Deployment**

We will build on this exact hierarchy:

```text
Deployment
    ↓
ReplicaSet
    ↓
Pods
    ↓
Containers
```

Deployment will introduce:

* Rolling updates
* Revision history
* Rollbacks
* Rollout status
* Scaling
* Zero-downtime deployment concepts
* Failed rollout troubleshooting
* Version mismatch scenarios
* CrashLoopBackOff during deployment
* Production deployment scenarios
* Interview questions

