# Kubernetes Workloads — Notes

## 05. Workloads Overview

Kubernetes Workload resources manage Pods according to the application's purpose.

| Workload | Main purpose |
|---|---|
| Deployment | Long-running stateless applications |
| ReplicaSet | Maintains desired number of Pods; normally managed by Deployment |
| Job | Run finite work until successful completion |
| CronJob | Run Jobs on a schedule |
| DaemonSet | Run one Pod on every applicable node |
| StatefulSet | Run stateful applications with stable identity and storage |

> StatefulSet was covered deeply in the Storage section because its most important practical behavior in our lab was stable identity + persistent storage.

---

# 1. Job

## Definition

A **Job** creates Pods that run a finite task and continues retrying until the required successful completions are achieved.

Typical use cases:

- Database migration
- Batch processing
- Data import/export
- One-time maintenance
- Backup task

### Mental model

```text
Job
 |
 +--> Pod
       |
       +--> Task completes
              |
              +--> Job Complete
```

Unlike a Deployment, a Job is not intended to keep an application running forever.

---

# 2. Basic Job Lab

Example:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: hello-job
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: hello
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              echo "Hello Kubernetes Job"
              echo "This task is running..."
              sleep 5
              echo "Job completed successfully"
```

Apply:

```bash
kubectl apply -f job.yaml
```

Check:

```bash
kubectl get jobs
kubectl get pods
```

Expected:

```text
hello-job   Complete   1/1
```

Pod:

```text
hello-job-xxxxx   0/1   Completed
```

Logs:

```bash
kubectl logs job/hello-job
```

Expected:

```text
Hello Kubernetes Job
This task is running...
Job completed successfully
```

---

# 3. Job Status

Use:

```bash
kubectl describe job hello-job
```

Important fields:

```text
Parallelism
Completions
Backoff Limit
Pods Statuses
```

Example:

```text
Parallelism: 1
Completions: 1
Backoff Limit: 6
Succeeded: 1
Failed: 0
```

### Meaning

- **Completions** = number of successful task executions required.
- **Parallelism** = maximum number of Pods running simultaneously.
- **BackoffLimit** = number of retries allowed after failures.

---

# 4. Failed Job and backoffLimit

Example:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: failed-job
spec:
  backoffLimit: 2
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: failure
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              echo "Starting job..."
              echo "Something went wrong!"
              exit 1
```

Apply:

```bash
kubectl apply -f failed-job.yaml
```

Check:

```bash
kubectl get pods -l job-name=failed-job
kubectl describe job failed-job
```

You can see multiple failed Pods.

With:

```yaml
backoffLimit: 2
```

the initial attempt plus retries can result in three attempts before the Job reaches:

```text
BackoffLimitExceeded
```

---

# 5. Parallel Jobs

Example:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-job
spec:
  completions: 5
  parallelism: 2
  backoffLimit: 2
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: worker
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              echo "Worker started"
              echo "Pod: $HOSTNAME"
              sleep 10
              echo "Worker completed"
```

Meaning:

```text
5 successful tasks required
2 workers maximum at a time
```

Conceptually:

```text
Batch 1 -> Worker 1 + Worker 2
Batch 2 -> Worker 3 + Worker 4
Batch 3 -> Worker 5
```

Verify:

```bash
kubectl get job parallel-job
kubectl get pods -l job-name=parallel-job
```

---

# 6. Job Important Concepts

### completions

How many successful executions are required.

```yaml
completions: 5
```

### parallelism

Maximum number of active Pods at the same time.

```yaml
parallelism: 2
```

### backoffLimit

Failure retry limit.

```yaml
backoffLimit: 2
```

### activeDeadlineSeconds

Limits how long a Job may remain active.

### ttlSecondsAfterFinished

Can automatically clean up completed Jobs after the specified period.

---

# 7. CronJob

## Definition

A **CronJob** creates Jobs according to a schedule.

Mental model:

```text
CronJob
   |
   +--> Job
          |
          +--> Pod
                 |
                 +--> Container
```

Typical use cases:

- Daily backup
- Database cleanup
- Report generation
- Scheduled data processing
- Periodic maintenance

---

# 8. Basic CronJob

Example:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hello-cronjob
spec:
  schedule: "*/1 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: hello
              image: busybox:1.36
              command:
                - sh
                - -c
                - |
                  echo "Hello from Kubernetes CronJob"
                  echo "Execution time: $(date)"
```

Apply:

```bash
kubectl apply -f cronjob.yaml
```

Check:

```bash
kubectl get cronjobs
kubectl get jobs
kubectl get pods
```

The CronJob automatically creates Jobs according to its schedule.

---

# 9. Cron Schedule

Example:

```text
*/1 * * * *
```

means every minute.

Cron fields:

```text
minute hour day-of-month month day-of-week
```

Examples:

```text
*/5 * * * *    every 5 minutes
0 * * * *      every hour
0 2 * * *      every day at 02:00
0 0 * * 0      every Sunday at midnight
```

---

# 10. CronJob History

Useful fields:

```yaml
successfulJobsHistoryLimit: 3
failedJobsHistoryLimit: 1
```

These control how many completed Job objects Kubernetes retains.

Example:

```yaml
spec:
  schedule: "*/5 * * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

---

# 11. CronJob concurrencyPolicy

Possible values:

```text
Allow
Forbid
Replace
```

### Allow

Multiple scheduled Jobs may run concurrently.

### Forbid

Do not start a new Job while the previous one is still running.

### Replace

Replace the currently running Job with the new scheduled Job.

---

# 12. CronJob suspend

A CronJob can temporarily be suspended.

Conceptually:

```yaml
spec:
  suspend: true
```

This prevents new Jobs from being scheduled.

It does not mean deleting the CronJob.

---

# 13. CronJob Troubleshooting Note

If a historical Pod has already disappeared, this command can return NotFound:

```bash
kubectl logs <old-pod-name>
```

A better approach is to identify the current Job:

```bash
kubectl get jobs
```

Then:

```bash
kubectl logs job/<job-name>
```

---

# 14. DaemonSet

## Definition

A **DaemonSet** ensures that a Pod runs on every node that matches its scheduling requirements.

Typical use cases:

- Log collection agent
- Monitoring agent
- Security agent
- Node-level networking components
- Host monitoring

Mental model:

```text
Node 1 -> Agent Pod
Node 2 -> Agent Pod
Node 3 -> Agent Pod
```

---

# 15. Basic DaemonSet

Example:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-agent
spec:
  selector:
    matchLabels:
      app: node-agent
  template:
    metadata:
      labels:
        app: node-agent
    spec:
      containers:
        - name: agent
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              echo "DaemonSet agent started"
              echo "Node: $NODE_NAME"
              while true; do
                echo "Agent running..."
                sleep 30
              done
          env:
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
```

Apply:

```bash
kubectl apply -f daemonset.yaml
```

Check:

```bash
kubectl get daemonset
kubectl get pods -o wide
```

On a single-node Minikube cluster, normally one DaemonSet Pod is created.

---

# 16. Verify Node Identity

Logs:

```bash
kubectl logs <daemonset-pod>
```

Expected:

```text
DaemonSet agent started
Node: minikube
Agent running...
```

The Pod receives the node name through the Downward API:

```yaml
fieldPath: spec.nodeName
```

---

# 17. DaemonSet Self-Healing

Delete the current DaemonSet Pod:

```bash
kubectl delete pod <daemonset-pod>
```

Then:

```bash
kubectl get pods -w
```

The DaemonSet controller notices that the desired Pod is missing and creates a replacement.

Conceptually:

```text
Desired:
1 agent Pod on minikube

Current:
0

DaemonSet controller
       |
       v
Create replacement
       |
       v
Current = 1
```

This is the same Kubernetes reconciliation model used by other controllers.

---

# 18. DaemonSet Status

Run:

```bash
kubectl get daemonset node-agent
```

Important columns:

```text
DESIRED
CURRENT
READY
UP-TO-DATE
AVAILABLE
```

On our one-node Minikube cluster:

```text
DESIRED = 1
CURRENT = 1
READY = 1
```

---

# 19. StatefulSet

## Definition

A **StatefulSet** manages stateful applications that require stable identity and/or persistent storage.

Important features:

- Stable Pod names
- Stable ordinal identity
- Stable storage through PVCs
- Ordered behavior
- Persistent identity across Pod recreation

Example Pods:

```text
stateful-demo-0
stateful-demo-1
stateful-demo-2
```

Unlike Deployment Pods, these identities are stable.

---

# 20. StatefulSet Storage

Example:

```yaml
volumeClaimTemplates:
  - metadata:
      name: app-data
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 1Gi
      storageClassName: standard
```

For three replicas, Kubernetes creates separate PVCs:

```text
app-data-stateful-demo-0
app-data-stateful-demo-1
app-data-stateful-demo-2
```

Each Pod gets its own storage.

---

# 21. StatefulSet Lab Behavior

We used:

```text
stateful-demo-0
stateful-demo-1
stateful-demo-2
```

Each Pod wrote a different identity file.

Example:

```text
Pod 0 -> DATA FROM POD 0
Pod 1 -> DATA FROM POD 1
Pod 2 -> DATA FROM POD 2
```

When:

```bash
kubectl delete pod stateful-demo-1
```

the StatefulSet recreated:

```text
stateful-demo-1
```

and the Pod reused its PVC, so its data remained.

---

# 22. StatefulSet Scaling

Scale from 3 to 5:

```bash
kubectl scale statefulset stateful-demo --replicas=5
```

New Pods:

```text
stateful-demo-3
stateful-demo-4
```

Scale back:

```bash
kubectl scale statefulset stateful-demo --replicas=2
```

Pods 2, 3, and 4 are removed.

The PVCs normally remain.

Scale back to 5:

```bash
kubectl scale statefulset stateful-demo --replicas=5
```

Pods 2, 3, and 4 are recreated and their existing PVCs can be reused.

---

# 23. Important StatefulSet Point

StatefulSet provides stable identity and storage behavior.

It does **not automatically provide database replication or application-level HA**.

For a database, replication/failover must be provided by:

- the database itself
- an operator
- a managed database service
- another appropriate architecture

---

# 24. Deployment Strategies

Deployment is normally used for long-running stateless applications.

Common strategies:

```text
RollingUpdate
Recreate
```

---

# 25. RollingUpdate

RollingUpdate replaces old Pods gradually.

Example:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1
```

### maxUnavailable

Maximum number of Pods that may be unavailable during the update.

### maxSurge

Maximum number of additional Pods Kubernetes can temporarily create above the desired replica count.

---

# 26. RollingUpdate Lab

Example Deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: strategy-demo
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: strategy-demo
  template:
    metadata:
      labels:
        app: strategy-demo
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
```

Apply:

```bash
kubectl apply -f deployment.yaml
```

Check:

```bash
kubectl rollout status deployment/strategy-demo
```

---

# 27. Update the Deployment

Update image:

```bash
kubectl set image deployment/strategy-demo nginx=nginx:1.28
```

Watch:

```bash
kubectl rollout status deployment/strategy-demo
```

Check Pods:

```bash
kubectl get pods
```

Check ReplicaSets:

```bash
kubectl get rs
```

You should see an old ReplicaSet scaled down and a new ReplicaSet scaled up.

Conceptually:

```text
Old RS
3 Pods
   |
   | gradual replacement
   v
New RS
3 Pods
```

---

# 28. Rollout History

Check:

```bash
kubectl rollout history deployment/strategy-demo
```

This shows deployment revisions.

---

# 29. Rollback

If a release has a problem:

```bash
kubectl rollout undo deployment/strategy-demo
```

Verify:

```bash
kubectl rollout status deployment/strategy-demo
```

Check:

```bash
kubectl get rs
```

Important:

Rollback does not simply erase history. Kubernetes creates another revision representing the rollback state.

---

# 30. Recreate Strategy

Example:

```yaml
strategy:
  type: Recreate
```

Behavior:

```text
Stop old Pods
      |
      v
Create new Pods
```

This can cause downtime.

Use cases are workload-dependent, for example when old and new versions must not run simultaneously.

---

# 31. RollingUpdate vs Recreate

| Feature | RollingUpdate | Recreate |
|---|---|---|
| Replacement | Gradual | All at once |
| Downtime | Usually minimized | Expected |
| Old/new Pods overlap | Possible | No |
| Typical use | Stateless production apps | Workloads requiring full stop/start |

---

# 32. Workload Selection Guide

```text
Long-running stateless app
        |
        v
    Deployment

Finite task
        |
        v
       Job

Scheduled finite task
        |
        v
     CronJob

One Pod per node
        |
        v
    DaemonSet

Stable identity + persistent state
        |
        v
    StatefulSet
```

---

# 33. Deployment vs Job

### Deployment

```text
Keep application running
```

Example:

```text
Web server
API server
Microservice
```

### Job

```text
Run task and finish
```

Example:

```text
Database migration
Batch processing
Backup
```

---

# 34. Deployment vs DaemonSet

### Deployment

Controls a desired number of replicas:

```text
replicas: 3
```

The Pods can be placed on nodes according to scheduling rules.

### DaemonSet

Controls one Pod per applicable node.

```text
Node 1 -> Pod
Node 2 -> Pod
Node 3 -> Pod
```

---

# 35. Workloads Internal Model

Most workload resources use controllers.

```text
Desired state
     |
     v
Controller
     |
     v
Compare desired vs current state
     |
     v
Create/update/delete resources
     |
     v
Actual state approaches desired state
```

Examples:

```text
Deployment -> ReplicaSet -> Pods
CronJob -> Job -> Pods
DaemonSet -> Pods
StatefulSet -> Pods + PVCs
Job -> Pods
```

This reconciliation model is one of the most important Kubernetes concepts.

---

# 36. Useful Commands

## Jobs

```bash
kubectl get jobs
kubectl describe job <job>
kubectl logs job/<job>
kubectl get pods -l job-name=<job>
```

## CronJobs

```bash
kubectl get cronjobs
kubectl describe cronjob <cronjob>
kubectl get jobs
```

## DaemonSets

```bash
kubectl get daemonsets
kubectl describe daemonset <daemonset>
kubectl get pods -o wide
```

## StatefulSets

```bash
kubectl get statefulsets
kubectl get pods
kubectl get pvc
kubectl describe statefulset <statefulset>
```

## Deployments

```bash
kubectl get deployments
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>
kubectl get rs
```

---

# 37. Interview Quick Answers

### What is a Job?

A controller that runs a finite task until the required successful completions are achieved.

### What is a CronJob?

A controller that creates Jobs according to a schedule.

### What is a DaemonSet?

A controller that ensures a Pod runs on every applicable node.

### What is a StatefulSet?

A controller for stateful workloads requiring stable identity and persistent storage behavior.

### What is RollingUpdate?

A Deployment strategy that gradually replaces old Pods with new Pods.

### What is Recreate?

A Deployment strategy that removes the old Pods before creating the new version.

### What is `maxSurge`?

The maximum temporary additional Pods allowed during a RollingUpdate.

### What is `maxUnavailable`?

The maximum number of Pods that may be unavailable during a RollingUpdate.

### Does StatefulSet provide database replication?

No. It provides stable identity/storage behavior; application-level replication is separate.

---

# 38. Quick Revision

```text
Deployment
  -> Long-running stateless application

Job
  -> Finite task

CronJob
  -> Scheduled Job

DaemonSet
  -> One Pod per applicable node

StatefulSet
  -> Stable identity + persistent state

RollingUpdate
  -> Gradual application update

Recreate
  -> Stop old version, then start new version
```
