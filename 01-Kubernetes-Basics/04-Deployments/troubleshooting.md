# Kubernetes Deployments — Troubleshooting

## 1. Deployment Not Ready

### Initial checks

```bash
kubectl get deployments
kubectl get rs
kubectl get pods

Then:

kubectl describe deployment <deployment>

Check:

Desired replicas
Updated replicas
Available replicas
Conditions
Events
2. Failed Rolling Update — Invalid Image
Scenario

We intentionally changed the image to:

image: nginx:1.999-not-exist
Symptoms

The Deployment rollout did not complete successfully.

Pods showed:

ErrImagePull
ImagePullBackOff
Troubleshooting
kubectl rollout status deployment/nginx-deployment
kubectl get rs
kubectl get pods
kubectl describe pod <pod>
Finding

The new ReplicaSet was created, but its Pods could not pull the configured image.

Root Cause

Invalid/nonexistent image tag.

Important architecture
Deployment
     ↓
New ReplicaSet
     ↓
New Pods
     ↓
ImagePullBackOff
Fix

Correct the image version.

Then:

kubectl apply -f nginx-deployment.yaml

or:

kubectl set image deployment/nginx-deployment \
  nginx=nginx:1.29
Verification
kubectl rollout status deployment/nginx-deployment
kubectl get pods

Expected:

Deployment successfully rolled out
Pods Running/Ready
3. Rollback After Failed Release
Scenario

A new application version is not healthy.

Check:

kubectl rollout history deployment/nginx-deployment

Rollback:

kubectl rollout undo deployment/nginx-deployment

Verify:

kubectl rollout status deployment/nginx-deployment
kubectl get rs
kubectl get pods
Learning

Deployments retain ReplicaSet history so that previous versions can be restored.

4. Controlled Rolling Update

We used:

strategy:
  type: RollingUpdate

  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1

With:

replicas: 5

Conceptually:

Desired = 5

Maximum unavailable = 1
Maximum surge = 1

During update:
old Pods gradually decrease
new Pods gradually increase

This provides controlled replacement rather than deleting all old Pods at once.

5. Troubleshooting Chain

Always follow:

Deployment
    ↓
ReplicaSet
    ↓
Pod
    ↓
Container
    ↓
Application

Commands:

kubectl get deployment
kubectl rollout status deployment/<name>
kubectl get rs
kubectl get pods
kubectl describe pod <pod>
kubectl get events --sort-by=.lastTimestamp
kubectl logs <pod>
6. Deployment Shows Updated<Desired

Example:

READY       UP-TO-DATE
2/5         2

Possible causes:

New Pods failing
ImagePullBackOff
CrashLoopBackOff
Scheduling problem
Readiness failure
Resource shortage

Check:

kubectl get rs
kubectl get pods
kubectl describe pod <pod>
7. Deployment Shows Pods Running but Not Ready

Example:

5 Pods Running
but only
3 Pods Ready

Possible causes:

Readiness probe failure
Application startup issue
Dependency unavailable
Wrong application port
Configuration problem

Check:

kubectl describe pod <pod>
kubectl logs <pod>
8. Deployment Rollout Appears Stuck

Check:

kubectl rollout status deployment/<name>
kubectl get rs
kubectl get pods
kubectl get events --sort-by=.lastTimestamp

Look for:

ImagePullBackOff
CrashLoopBackOff
Pending
Readiness probe failures
Insufficient resources
9. Important Production Rule

Do not immediately rollback every failed rollout.

First determine:

What failed?
Why did it fail?
Is rollback required?
Can the issue be fixed safely?

If the new release is causing a production outage, rollback can be an appropriate mitigation while the root cause is investigated.

10. Interview Scenario
Question

"A Deployment rollout is stuck. How do you troubleshoot it?"

Answer

"I first check kubectl rollout status and the Deployment conditions. Then I inspect the ReplicaSets to determine whether the new ReplicaSet was created. I check the new Pods with kubectl get pods and kubectl describe pod, especially Events, container state and readiness. If the container started, I check logs. Based on the evidence, I determine whether the issue is an image, scheduling, resource, configuration, readiness, or application problem."

11. Interview Scenario
Question

"How do you achieve zero/minimal downtime during deployment?"

Answer

"I use a Deployment with a RollingUpdate strategy and configure appropriate maxUnavailable and maxSurge values. I also use readiness probes so that new Pods only receive traffic after the application is ready. The exact settings depend on the application's availability and capacity requirements."

12. Interview Scenario
Question

"What happens internally when you update a Deployment image?"

Answer
New image
   ↓
Deployment Pod template changes
   ↓
New ReplicaSet
   ↓
New Pods
   ↓
Readiness
   ↓
Old ReplicaSet scales down

The old ReplicaSet is retained for rollout history.

13. Interview Scenario
Question

"How would you rollback a bad release?"

Answer:

kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>
kubectl rollout status deployment/<name>

Then verify Pods and application health.

14. Deployment Checklist
Deployment
   ↓
Correct image?
   ↓
ReplicaSet created?
   ↓
Pods scheduled?
   ↓
Pods running?
   ↓
Pods ready?
   ↓
Application healthy?
   ↓
Rollout complete?
15. Key Learning

A Deployment is not just a way to run Pods.

It is a release management mechanism:

Deployment
     ↓
Version 1
     ↓
ReplicaSet 1
     ↓
Pods

Update
     ↓
Version 2
     ↓
ReplicaSet 2
     ↓
New Pods
     ↓
Gradual replacement
     ↓
Rollback available# Kubernetes Deployments — Troubleshooting

## 1. Deployment Not Ready

### Initial checks

```bash
kubectl get deployments
kubectl get rs
kubectl get pods

Then:

kubectl describe deployment <deployment>

Check:

Desired replicas
Updated replicas
Available replicas
Conditions
Events
2. Failed Rolling Update — Invalid Image
Scenario

We intentionally changed the image to:

image: nginx:1.999-not-exist
Symptoms

The Deployment rollout did not complete successfully.

Pods showed:

ErrImagePull
ImagePullBackOff
Troubleshooting
kubectl rollout status deployment/nginx-deployment
kubectl get rs
kubectl get pods
kubectl describe pod <pod>
Finding

The new ReplicaSet was created, but its Pods could not pull the configured image.

Root Cause

Invalid/nonexistent image tag.

Important architecture
Deployment
     ↓
New ReplicaSet
     ↓
New Pods
     ↓
ImagePullBackOff
Fix

Correct the image version.

Then:

kubectl apply -f nginx-deployment.yaml

or:

kubectl set image deployment/nginx-deployment \
  nginx=nginx:1.29
Verification
kubectl rollout status deployment/nginx-deployment
kubectl get pods

Expected:

Deployment successfully rolled out
Pods Running/Ready
3. Rollback After Failed Release
Scenario

A new application version is not healthy.

Check:

kubectl rollout history deployment/nginx-deployment

Rollback:

kubectl rollout undo deployment/nginx-deployment

Verify:

kubectl rollout status deployment/nginx-deployment
kubectl get rs
kubectl get pods
Learning

Deployments retain ReplicaSet history so that previous versions can be restored.

4. Controlled Rolling Update

We used:

strategy:
  type: RollingUpdate

  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1

With:

replicas: 5

Conceptually:

Desired = 5

Maximum unavailable = 1
Maximum surge = 1

During update:
old Pods gradually decrease
new Pods gradually increase

This provides controlled replacement rather than deleting all old Pods at once.

5. Troubleshooting Chain

Always follow:

Deployment
    ↓
ReplicaSet
    ↓
Pod
    ↓
Container
    ↓
Application

Commands:

kubectl get deployment
kubectl rollout status deployment/<name>
kubectl get rs
kubectl get pods
kubectl describe pod <pod>
kubectl get events --sort-by=.lastTimestamp
kubectl logs <pod>
6. Deployment Shows Updated<Desired

Example:

READY       UP-TO-DATE
2/5         2

Possible causes:

New Pods failing
ImagePullBackOff
CrashLoopBackOff
Scheduling problem
Readiness failure
Resource shortage

Check:

kubectl get rs
kubectl get pods
kubectl describe pod <pod>
7. Deployment Shows Pods Running but Not Ready

Example:

5 Pods Running
but only
3 Pods Ready

Possible causes:

Readiness probe failure
Application startup issue
Dependency unavailable
Wrong application port
Configuration problem

Check:

kubectl describe pod <pod>
kubectl logs <pod>
8. Deployment Rollout Appears Stuck

Check:

kubectl rollout status deployment/<name>
kubectl get rs
kubectl get pods
kubectl get events --sort-by=.lastTimestamp

Look for:

ImagePullBackOff
CrashLoopBackOff
Pending
Readiness probe failures
Insufficient resources
9. Important Production Rule

Do not immediately rollback every failed rollout.

First determine:

What failed?
Why did it fail?
Is rollback required?
Can the issue be fixed safely?

If the new release is causing a production outage, rollback can be an appropriate mitigation while the root cause is investigated.

10. Interview Scenario
Question

"A Deployment rollout is stuck. How do you troubleshoot it?"

Answer

"I first check kubectl rollout status and the Deployment conditions. Then I inspect the ReplicaSets to determine whether the new ReplicaSet was created. I check the new Pods with kubectl get pods and kubectl describe pod, especially Events, container state and readiness. If the container started, I check logs. Based on the evidence, I determine whether the issue is an image, scheduling, resource, configuration, readiness, or application problem."

11. Interview Scenario
Question

"How do you achieve zero/minimal downtime during deployment?"

Answer

"I use a Deployment with a RollingUpdate strategy and configure appropriate maxUnavailable and maxSurge values. I also use readiness probes so that new Pods only receive traffic after the application is ready. The exact settings depend on the application's availability and capacity requirements."

12. Interview Scenario
Question

"What happens internally when you update a Deployment image?"

Answer
New image
   ↓
Deployment Pod template changes
   ↓
New ReplicaSet
   ↓
New Pods
   ↓
Readiness
   ↓
Old ReplicaSet scales down

The old ReplicaSet is retained for rollout history.

13. Interview Scenario
Question

"How would you rollback a bad release?"

Answer:

kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>
kubectl rollout status deployment/<name>

Then verify Pods and application health.

14. Deployment Checklist
Deployment
   ↓
Correct image?
   ↓
ReplicaSet created?
   ↓
Pods scheduled?
   ↓
Pods running?
   ↓
Pods ready?
   ↓
Application healthy?
   ↓
Rollout complete?
15. Key Learning

A Deployment is not just a way to run Pods.

It is a release management mechanism:

Deployment
     ↓
Version 1
     ↓
ReplicaSet 1
     ↓
Pods

Update
     ↓
Version 2
     ↓
ReplicaSet 2
     ↓
New Pods
     ↓
Gradual replacement
     ↓
Rollback available
