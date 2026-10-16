# Kubernetes Workloads — Troubleshooting

## 1. General Troubleshooting Approach

For any workload problem:

```bash
kubectl get <workload>
kubectl describe <workload-type> <name>
kubectl get pods
kubectl describe pod <pod>
kubectl get events --sort-by=.lastTimestamp
kubectl logs <pod>
```

Start from the controller and follow the resource chain.

Examples:

```text
Deployment -> ReplicaSet -> Pod
CronJob -> Job -> Pod
Job -> Pod
DaemonSet -> Pod
StatefulSet -> Pod + PVC
```

---

# 2. Job Troubleshooting

## Problem: Job is Failed

Check:

```bash
kubectl get jobs
kubectl describe job <job>
```

Look for:

```text
Failed
BackoffLimitExceeded
```

Then identify the Job Pods:

```bash
kubectl get pods -l job-name=<job>
```

Check logs:

```bash
kubectl logs <pod-name>
```

### Common causes

- Application exits with non-zero code
- Wrong command
- Missing file
- Missing environment variable
- Image problem
- Permission problem
- Dependency unavailable

### Resolution

Fix the application/command and recreate the Job when appropriate.

---

# 3. Job Does Not Complete

Check:

```bash
kubectl get job <job>
kubectl describe job <job>
kubectl get pods -l job-name=<job>
```

Then:

```bash
kubectl logs <pod>
```

Possible causes:

```text
Application never exits
Application is stuck
External dependency unavailable
Incorrect command
```

Remember:

A Job is expected to finish. A process that runs forever is not a suitable basic Job workload.

---

# 4. Job Repeatedly Fails

Check:

```bash
kubectl describe job <job>
```

Inspect:

```text
Backoff Limit
Pods Statuses
Events
```

Then:

```bash
kubectl get pods -l job-name=<job>
kubectl logs <failed-pod>
```

If:

```yaml
backoffLimit: 2
```

the Job can make the initial attempt plus retries before reaching the failure threshold.

Do not simply increase `backoffLimit` without fixing the underlying failure.

---

# 5. CronJob Is Not Creating Jobs

Check:

```bash
kubectl get cronjob <cronjob>
kubectl describe cronjob <cronjob>
```

Verify:

```text
Schedule
Suspend
Last Schedule
Active
```

### Check whether it is suspended

```bash
kubectl get cronjob <cronjob> -o yaml
```

Look for:

```yaml
spec:
  suspend: true
```

If suspended, new Jobs will not be created.

---

# 6. CronJob Creates Jobs but Pods Fail

Follow the chain:

```text
CronJob
   |
   v
Job
   |
   v
Pod
```

Commands:

```bash
kubectl get cronjobs
kubectl get jobs
kubectl get pods
```

Then:

```bash
kubectl describe job <job>
kubectl describe pod <pod>
kubectl logs <pod>
```

This separates scheduling/controller problems from application problems.

---

# 7. CronJob Historical Pod Not Found

You may run:

```bash
kubectl logs <old-pod-name>
```

and receive:

```text
NotFound
```

The old Pod may already have been removed or you may be using an old generated name.

Find current Jobs:

```bash
kubectl get jobs
```

Then inspect the Job:

```bash
kubectl describe job <job>
kubectl logs job/<job>
```

Also check:

```bash
kubectl get pods
```

---

# 8. CronJob Runs More Than Expected

Check:

```bash
kubectl describe cronjob <cronjob>
```

Inspect:

```text
Schedule
Concurrency Policy
```

Possible policy:

```text
Allow
```

allows overlapping Jobs.

If the task must not overlap, consider:

```yaml
concurrencyPolicy: Forbid
```

Use the policy according to application behavior.

---

# 9. DaemonSet Has Fewer Pods Than Expected

Check:

```bash
kubectl get daemonset <daemonset>
kubectl get nodes
kubectl get pods -o wide
```

Compare:

```text
DESIRED
CURRENT
READY
AVAILABLE
```

If:

```text
DESIRED = 3
CURRENT = 2
```

investigate the node that does not have a DaemonSet Pod.

Check:

```bash
kubectl describe daemonset <daemonset>
kubectl describe node <node>
```

Possible causes include:

- Node not Ready
- Node scheduling constraints
- Taints
- Node selectors
- Affinity rules
- Pod scheduling failure

---

# 10. DaemonSet Pod Keeps Getting Recreated

This can be expected behavior.

A DaemonSet controller continuously tries to maintain its desired state.

If a DaemonSet Pod is manually deleted:

```bash
kubectl delete pod <daemonset-pod>
```

the controller creates a replacement.

If the replacement immediately fails, inspect:

```bash
kubectl get pods -o wide
kubectl describe pod <new-pod>
kubectl logs <new-pod>
```

---

# 11. DaemonSet Pod is Pending

Check:

```bash
kubectl describe pod <pod>
```

Look at Events.

Possible reasons:

```text
Insufficient cpu
Insufficient memory
Taint not tolerated
Node selector mismatch
Affinity mismatch
```

DaemonSet does not bypass normal Kubernetes scheduling constraints.

---

# 12. StatefulSet Pod Does Not Start

Check:

```bash
kubectl get statefulset
kubectl get pods
kubectl describe pod <pod>
```

Then inspect storage:

```bash
kubectl get pvc
kubectl get pv
```

For a Pod waiting on storage, check:

```bash
kubectl describe pvc <pvc>
```

Possible issues:

- PVC Pending
- No matching StorageClass
- Storage provisioning failure
- Access mode mismatch
- Insufficient storage
- Node scheduling problem

---

# 13. StatefulSet PVC is Pending

Run:

```bash
kubectl get pvc
kubectl describe pvc <pvc>
kubectl get storageclass
```

Check:

```text
Status
StorageClass
Events
```

For dynamic provisioning, the StorageClass/provisioner must be available.

In our Minikube lab, the default `standard` StorageClass used the Minikube hostpath provisioner.

---

# 14. StatefulSet Pod Recreated but Data Is Missing

First verify the PVC:

```bash
kubectl get pvc
```

Check whether the recreated Pod uses the same PVC.

For example:

```text
app-data-stateful-demo-1
```

should remain associated with:

```text
stateful-demo-1
```

Check:

```bash
kubectl describe pod stateful-demo-1
kubectl describe pvc app-data-stateful-demo-1
```

Important:

Do not confuse Pod deletion with PVC deletion.

StatefulSet storage is normally preserved through Pod recreation when the PVC remains.

---

# 15. StatefulSet Scale Down and PVC Confusion

After:

```bash
kubectl scale statefulset stateful-demo --replicas=2
```

Pods with higher ordinals can be removed:

```text
stateful-demo-2
stateful-demo-3
stateful-demo-4
```

But PVCs normally remain.

Check:

```bash
kubectl get pvc
```

This is intentional and allows storage to be reused if those identities are recreated.

---

# 16. Deployment Rollout Is Stuck

Check:

```bash
kubectl rollout status deployment/<deployment>
```

Then:

```bash
kubectl get pods
kubectl get rs
kubectl describe deployment <deployment>
```

Inspect failing/new Pods:

```bash
kubectl describe pod <pod>
kubectl logs <pod>
```

Common causes:

- Image cannot be pulled
- Container crashes
- Readiness probe failure
- Resource shortage
- Invalid configuration
- Secret/ConfigMap missing

---

# 17. Deployment Image Update Does Not Become Ready

Example:

```bash
kubectl set image deployment/strategy-demo nginx=nginx:1.28
```

Then:

```bash
kubectl rollout status deployment/strategy-demo
```

If it hangs, inspect:

```bash
kubectl get pods
kubectl describe pod <new-pod>
kubectl logs <new-pod>
```

Also check ReplicaSets:

```bash
kubectl get rs
```

The new ReplicaSet may exist but its Pods may not become Ready.

---

# 18. Deployment Rollout Failed

Check:

```bash
kubectl rollout status deployment/<name>
kubectl describe deployment <name>
kubectl get rs
kubectl get pods
```

Find the newest ReplicaSet and inspect its Pods.

If the new version is known to be bad, rollback:

```bash
kubectl rollout undo deployment/<name>
```

Verify:

```bash
kubectl rollout status deployment/<name>
```

---

# 19. Rollback Warning About last-applied-configuration

When using:

```bash
kubectl rollout undo deployment/strategy-demo
```

you may see a warning related to:

```text
last-applied-configuration
```

This does not necessarily mean the rollout failed.

Verify actual rollout state:

```bash
kubectl rollout status deployment/strategy-demo
kubectl get pods
kubectl get rs
```

The operational result is more important than the warning itself.

---

# 20. Deployment Has Unexpected Downtime During Rolling Update

Inspect:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1
```

Understand:

```text
maxUnavailable
= how many Pods can be unavailable

maxSurge
= temporary extra Pods allowed
```

Also check application readiness.

A Pod being `Running` does not automatically mean it is ready to receive traffic.

---

# 21. Job vs Deployment Troubleshooting

If an application is expected to keep running but was created as a Job:

```text
Job -> process completes -> Pod Completed
```

This may be interpreted as a failure when it is actually normal Job behavior.

For a long-running application, use an appropriate workload such as Deployment.

---

# 22. General Event Investigation

One of the most useful commands:

```bash
kubectl get events --sort-by=.lastTimestamp
```

This can reveal:

```text
FailedScheduling
FailedMount
Failed
BackOff
Pulling
Pulled
Created
Started
```

Events are often the fastest way to identify what Kubernetes is trying to do.

---

# 23. General Workload Troubleshooting Flow

```text
Workload problem
      |
      v
Check controller
      |
      +--> Job
      +--> CronJob
      +--> DaemonSet
      +--> StatefulSet
      +--> Deployment
      |
      v
Check Pods
      |
      v
kubectl describe pod
      |
      v
Check Events
      |
      v
Check logs
      |
      v
Check dependencies
      |
      v
Fix root cause
      |
      v
Verify desired state
```

---

# 24. Interview Scenario — Job Failed

### Question

"A Kubernetes Job failed. How do you troubleshoot it?"

### Answer

I would first check:

```bash
kubectl get job <job>
kubectl describe job <job>
```

Then identify the Job Pods:

```bash
kubectl get pods -l job-name=<job>
```

I would inspect:

```bash
kubectl describe pod <pod>
kubectl logs <pod>
```

I would check the exit code, application error, Events, and `backoffLimit`. I would fix the underlying issue instead of only increasing retries.

---

# 25. Interview Scenario — CronJob Not Running

### Answer

I would check:

```bash
kubectl get cronjob <name>
kubectl describe cronjob <name>
```

Then verify:

- schedule
- suspend setting
- last schedule
- concurrency policy

Then check whether Jobs were created:

```bash
kubectl get jobs
```

If a Job exists, troubleshoot it like a normal Job.

---

# 26. Interview Scenario — DaemonSet Missing on a Node

### Answer

I would compare:

```bash
kubectl get daemonset
kubectl get nodes
kubectl get pods -o wide
```

Then inspect the missing node and Pod scheduling Events.

I would check:

- node readiness
- taints/tolerations
- node selectors
- affinity
- resource availability

---

# 27. Interview Scenario — StatefulSet Lost Data

### Answer

I would first determine whether the Pod or the PVC was deleted.

Commands:

```bash
kubectl get pods
kubectl get pvc
kubectl get pv
```

Then inspect:

```bash
kubectl describe pvc <pvc>
```

A StatefulSet Pod can be recreated with the same identity and reuse its PVC. Data loss depends on what happened to the underlying storage and PVC lifecycle.

---

# 28. Interview Scenario — Deployment Release Is Bad

### Answer

I would inspect the rollout:

```bash
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
```

I would inspect the new ReplicaSet and Pods.

If the previous revision is known to be healthy and rollback is appropriate:

```bash
kubectl rollout undo deployment/<name>
```

Then verify:

```bash
kubectl rollout status deployment/<name>
```

---

# 29. Quick Troubleshooting Commands

```bash
# Workload status
kubectl get deployments
kubectl get jobs
kubectl get cronjobs
kubectl get daemonsets
kubectl get statefulsets

# Pods
kubectl get pods -o wide
kubectl describe pod <pod>

# Events
kubectl get events --sort-by=.lastTimestamp

# Logs
kubectl logs <pod>
kubectl logs job/<job>

# Deployment
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>

# Storage
kubectl get pvc
kubectl get pv
kubectl describe pvc <pvc>
```

---

# 30. Key Troubleshooting Rules

```text
Job failure
  -> Check Job + Pod + logs

CronJob failure
  -> Check CronJob -> Job -> Pod

DaemonSet missing
  -> Check node + scheduling constraints

StatefulSet issue
  -> Check Pod + PVC + PV + StorageClass

Deployment rollout issue
  -> Check Deployment -> ReplicaSet -> Pod

Pod Pending
  -> kubectl describe pod
  -> inspect Events

Pod Running but application failing
  -> check logs + readiness + dependencies

Storage problem
  -> inspect PVC/PV/StorageClass
```
