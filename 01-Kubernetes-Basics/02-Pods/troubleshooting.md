# Kubernetes Pods — Troubleshooting

# 1. Pod ImagePullBackOff

## Problem

We intentionally used an invalid/nonexistent image.

Example:

```yaml
image: nginx:<invalid-tag>
Symptoms
ErrImagePull
ImagePullBackOff
Initial checks
kubectl get pods
kubectl describe pod <pod>
Finding

The Pod Events showed that Kubernetes could not pull the requested image.

Root Cause

Invalid/nonexistent image tag.

Fix

Correct the image name/tag.

Example:

image: nginx:1.29

Apply:

kubectl apply -f nginx-pod.yaml
Verification
kubectl get pods

Expected:

1/1   Running
Interview explanation

"I would first check the Pod status and then inspect Events using kubectl describe pod. If the Pod is in ImagePullBackOff, I would verify the image repository, image name, tag, registry authentication, and network connectivity."

2. Understanding Pod Self-Healing
Problem

We deleted a Pod managed by a ReplicaSet/Deployment.

kubectl delete pod <pod>
Observation

The deleted Pod disappeared and a replacement Pod was created.

Flow
Deployment
    ↓
ReplicaSet
    ↓
3 Pods
    ↓
Delete 1 Pod
    ↓
2 Pods
    ↓
ReplicaSet detects difference
    ↓
Replacement Pod
    ↓
3 Pods
Root Cause / Learning

The Pod itself does not provide self-healing.

The controller maintains the desired number of replicas.

3. Standalone Pod vs Managed Pod
Standalone Pod

Created directly:

kubectl apply -f pod.yaml

If deleted:

Pod deleted
↓
No controller
↓
No replacement
Deployment-managed Pod
Deployment
↓
ReplicaSet
↓
Pod

If deleted:

Pod deleted
↓
ReplicaSet detects missing replica
↓
Replacement created
4. Pod Troubleshooting Checklist
Step 1 — Check status
kubectl get pods -o wide
Step 2 — Describe
kubectl describe pod <pod>

Check:

State
Last State
Reason
Exit Code
Restart Count
Conditions
Events
Step 3 — Logs
kubectl logs <pod>

If restarted:

kubectl logs <pod> --previous
Step 4 — Enter the container
kubectl exec -it <pod> -- /bin/sh

Then inspect:

hostname
env
ls
wget

depending on the image/tools available.

Step 5 — Check configuration

Inspect:

Image
Command
Arguments
Environment variables
Volumes
Probes
Resource requests/limits
Security context
5. Important Troubleshooting Principle

Do not assume:

Pod problem = application problem

The failure may be:

Scheduling
Image
Configuration
Secret
ConfigMap
Resources
Networking
Probe
Permissions
Application
Dependency

Always collect evidence first.

6. Minimal Container Troubleshooting

Some container images are intentionally minimal.

For example, an Nginx image may not contain:

ps
top
curl

If a command isn't available, don't assume the container is broken.

Use tools that actually exist in the image or use a temporary troubleshooting container/tool.

Example:

kubectl exec <pod> -- nginx -t

or:

kubectl exec <pod> -- wget -qO- http://localhost

depending on the image.

7. Pod Troubleshooting Interview Scenario
Scenario

A Pod shows:

0/1 Error

What do you do?

Answer:

1. kubectl get pod
2. kubectl describe pod
3. Check State/Last State
4. Check Exit Code
5. Check Events
6. kubectl logs
7. kubectl logs --previous if restarted
8. Inspect image/command/config/resources
9. Identify root cause
10. Fix and verify
8. Pod Troubleshooting Interview Scenario
Scenario

A Pod is Running but 0/1 Ready.

Possible causes:

Readiness probe failing
Application not ready
Dependency unavailable
Port/configuration issue

Check:

kubectl describe pod <pod>
kubectl logs <pod>

If a Service exists, also check whether the Pod is present in its endpoints.

9. Pod Troubleshooting Interview Scenario
Scenario

A Pod keeps restarting.

Check:

kubectl describe pod <pod>

Look at:

Last State
Reason
Exit Code
Restart Count

Then:

kubectl logs <pod> --previous

Possible causes:

Application crash
OOMKilled
Liveness probe failure
Configuration failure
Dependency failure
Permission problem
10. Production Mindset

Never start with:

kubectl delete pod

as the first troubleshooting action.

First understand:

What happened?
Why did it happen?
What evidence proves it?

Then fix the root cause.

Deleting a Pod can temporarily hide the symptom without solving the underlying issue.


### What we'll do before moving on

We'll create these two files in your existing directory:

```text
~/EKS-Kubernetes-Learning/01-Kubernetes-Basics/02-Pods/
├── notes.md
└── troubleshooting.md

Then we'll review them together, make any corrections, and only after you're happy we'll commit:

git add 01-Kubernetes-Basics/02-Pods/
git commit -m "Add Kubernetes Pods notes and troubleshooting"
git push origin main
