# Kubernetes Deployments — Notes

## 1. What is a Deployment?

A Deployment is a Kubernetes controller used to manage application releases and ReplicaSets.

It provides:

- Declarative application management
- Replica management
- Rolling updates
- Rollbacks
- Revision history
- Controlled application updates

Architecture:

```text
Deployment
    |
    +-- ReplicaSet
          |
          +-- Pod
          +-- Pod
          +-- Pod
2. Why use Deployments?

Instead of manually managing Pods or ReplicaSets, a Deployment allows us to declare:

replicas: 3
image: nginx:1.29

Kubernetes continuously works to make the actual state match the desired state.

Deployment is commonly used for stateless applications such as:

Web applications
APIs
Microservices
Frontend applications
3. Basic Deployment

Example:

apiVersion: apps/v1
kind: Deployment

metadata:
  name: nginx-deployment

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
          image: nginx:1.28
          ports:
            - containerPort: 80

Apply:

kubectl apply -f nginx-deployment.yaml
4. Deployment Creates ReplicaSets

When a Deployment is created:

Deployment
    ↓
ReplicaSet
    ↓
Pods

The Deployment does not directly create the containers.

It creates/manages a ReplicaSet, and the ReplicaSet manages the Pods.

5. Verify Deployment
kubectl get deployments

Example:

NAME              READY   UP-TO-DATE   AVAILABLE
nginx-deployment  3/3     3            3

Check ReplicaSets:

kubectl get rs

Check Pods:

kubectl get pods -l app=nginx
6. Scaling a Deployment

Scale from 3 to 5:

kubectl scale deployment nginx-deployment --replicas=5

Verify:

kubectl get deployment nginx-deployment
kubectl get pods -l app=nginx

Scale down:

kubectl scale deployment nginx-deployment --replicas=3
7. Rolling Updates

A rolling update allows Kubernetes to gradually replace old Pods with new Pods.

Example:

Old version
nginx:1.28

        ↓

New version
nginx:1.29

Deployment creates a new ReplicaSet.

Deployment
    |
    +-- Old ReplicaSet
    |      |
    |      +-- old Pods
    |
    +-- New ReplicaSet
           |
           +-- new Pods

The new ReplicaSet is gradually scaled up while the old ReplicaSet is scaled down.

8. Update Deployment Image

Example:

kubectl set image deployment/nginx-deployment \
  nginx=nginx:1.29

Check rollout:

kubectl rollout status deployment/nginx-deployment

Watch Pods:

kubectl get pods -l app=nginx -w
9. Important Deployment Behavior

A Deployment does not update existing Pods in place.

Instead:

Old Deployment
     ↓
Old ReplicaSet
     ↓
Old Pods

New image
     ↓
New ReplicaSet
     ↓
New Pods

Then Kubernetes gradually removes the old Pods.

10. ReplicaSet History

After a rollout:

kubectl get rs

You may see:

NAME                         DESIRED   CURRENT   READY
nginx-deployment-old         0         0         0
nginx-deployment-new         3         3         3

The old ReplicaSet is retained for revision history.

It may be scaled to zero but is not necessarily deleted immediately.

11. Rolling Update Strategy

Example:

strategy:
  type: RollingUpdate

  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1
12. maxUnavailable

maxUnavailable controls how many existing Pods can be unavailable during an update.

Example:

maxUnavailable: 1

If we normally have:

5 Pods

Kubernetes can temporarily have at most one unavailable Pod due to the rollout.

13. maxSurge

maxSurge controls how many additional Pods can temporarily be created above the desired replica count.

Example:

maxSurge: 1

With:

replicas: 5

Kubernetes may temporarily have:

6 Pods

during the rollout.

14. maxUnavailable + maxSurge

Example:

replicas: 5

rollingUpdate:
  maxUnavailable: 1
  maxSurge: 1

Conceptually:

Desired = 5

During rollout:

Old Pods → gradually removed
New Pods → gradually created

Maximum extra Pods ≈ 1
Maximum unavailable due to rollout ≈ 1

These settings control the speed and availability characteristics of a rollout.

15. Zero/Minimal-Downtime Rolling Updates

For a production web application:

Users
  ↓
Service / Load Balancer
  ↓
Healthy Pods

During a rollout:

Old healthy Pods
       +
New healthy Pods
       ↓
Traffic continues
       ↓
Old Pods gradually removed

Readiness probes are important because a Pod should become Ready before it receives normal Service traffic.

16. Rollout Status

Check:

kubectl rollout status deployment/nginx-deployment

Successful result:

deployment "nginx-deployment" successfully rolled out
17. Rollout History

Check:

kubectl rollout history deployment/nginx-deployment

This shows Deployment revisions.

18. Rollback

If a new version causes problems:

kubectl rollout undo deployment/nginx-deployment

Check:

kubectl rollout status deployment/nginx-deployment

Verify:

kubectl get pods
kubectl get rs
19. Rollback to a Specific Revision

List revisions:

kubectl rollout history deployment/nginx-deployment

Then:

kubectl rollout undo deployment/nginx-deployment \
  --to-revision=<revision>
20. Failed Rollout Scenario

We intentionally changed the image to an invalid version:

image: nginx:1.999-not-exist

The Deployment created a new ReplicaSet, but the new Pods could not start.

Typical status:

ImagePullBackOff
ErrImagePull

The important architecture was:

Deployment
    ↓
New ReplicaSet
    ↓
New Pods
    ↓
ImagePullBackOff

The old ReplicaSet remained available while Kubernetes attempted the new rollout.

21. Troubleshooting a Failed Deployment

Start:

kubectl get deployment

Then:

kubectl rollout status deployment <deployment>

Check ReplicaSets:

kubectl get rs

Check Pods:

kubectl get pods

Describe the failing Pod:

kubectl describe pod <pod>

Check Events:

kubectl get events --sort-by=.lastTimestamp
22. Deployment Troubleshooting Chain

Remember:

Deployment
     ↓
ReplicaSet
     ↓
Pod
     ↓
Container
     ↓
Application

When a Deployment fails, don't troubleshoot only the Deployment.

Follow the chain downward.

23. Deployment Conditions

Useful fields:

kubectl describe deployment <deployment>

Look at:

Available
Progressing
Replica counts
Conditions
Events

Also:

kubectl get deployment

Important values:

READY
UP-TO-DATE
AVAILABLE
24. Important Commands
kubectl get deployments

kubectl describe deployment <name>

kubectl get rs

kubectl get pods

kubectl set image deployment/<name> \
  <container>=<image>

kubectl rollout status deployment/<name>

kubectl rollout history deployment/<name>

kubectl rollout undo deployment/<name>

kubectl scale deployment <name> --replicas=5

kubectl get events --sort-by=.lastTimestamp
25. Interview Q&A
Q1. What is a Deployment?

A Deployment manages application releases and ReplicaSets and provides features such as rolling updates and rollbacks.

Q2. What does a Deployment create?

A Deployment creates and manages ReplicaSets, which then create and manage Pods.

Q3. Does Deployment update Pods directly?

No.

It creates/manages ReplicaSets, and the ReplicaSets manage Pods.

Q4. What happens during a rolling update?

A new ReplicaSet is created for the new Pod template. New Pods are gradually created while old Pods are gradually removed.

Q5. What is maxUnavailable?

It controls the maximum number of Pods that can be unavailable during a rolling update.

Q6. What is maxSurge?

It controls how many additional Pods can temporarily be created above the desired replica count during a rolling update.

Q7. Why are old ReplicaSets retained?

They provide rollout history and allow rollback to previous application versions.

Q8. How do you check rollout status?
kubectl rollout status deployment/<name>
Q9. How do you check rollout history?
kubectl rollout history deployment/<name>
Q10. How do you rollback?
kubectl rollout undo deployment/<name>
Q11. What happens if the new image doesn't exist?

The new ReplicaSet is created, but its Pods may enter:

ErrImagePull
ImagePullBackOff

The rollout will not successfully complete.

Q12. How do you troubleshoot a failed rollout?
Deployment
 ↓
rollout status
 ↓
ReplicaSets
 ↓
Pods
 ↓
describe
 ↓
Events
 ↓
logs if container started
Q13. Why is readiness important during rolling updates?

A new Pod should only receive application traffic after it is ready. Readiness helps prevent traffic from reaching an application that hasn't finished starting or isn't healthy.

Q14. What is the difference between Deployment and ReplicaSet?
Deployment
→ manages application versions and releases

ReplicaSet
→ maintains desired number of Pods
Q15. Why use Deployment instead of manually creating ReplicaSets?

Deployment provides:

Rolling updates
Rollbacks
Revision history
Declarative release management
Q16. What is a revision?

A Deployment revision represents a version of the Deployment's Pod template, allowing Kubernetes to maintain rollout history.

Q17. Can you scale a Deployment?

Yes:

kubectl scale deployment <name> --replicas=5
Q18. What happens to the old ReplicaSet after a successful rollout?

It is generally scaled down to zero but retained for revision history.

26. Production Scenario — Failed Deployment
Scenario

A developer deploys a new application version and users report issues.

First checks:

kubectl rollout status deployment/<name>
kubectl get rs
kubectl get pods

Then:

kubectl describe pod <failing-pod>

Check:

Image
Events
Container state
Exit code
Readiness
Liveness
Configuration
Secrets
Resources

If the new version is confirmed as the cause, rollback:

kubectl rollout undo deployment/<name>

Then verify:

kubectl rollout status deployment/<name>
27. One-Minute Deployment Explanation

"A Deployment is a higher-level Kubernetes controller used to manage application releases. It creates and manages ReplicaSets, which manage the Pods. When we update the application image, the Deployment creates a new ReplicaSet and gradually replaces the old Pods using a rolling update strategy. maxUnavailable controls how many Pods can be unavailable, while maxSurge controls how many additional Pods can temporarily be created. If the new version fails, we can inspect the rollout, ReplicaSets, Pods and Events, and use kubectl rollout undo to roll back."

