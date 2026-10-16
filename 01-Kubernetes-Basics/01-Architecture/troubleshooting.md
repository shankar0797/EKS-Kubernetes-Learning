# Kubernetes Architecture — Troubleshooting

## 1. Basic Troubleshooting Flow

When a Kubernetes cluster or workload has a problem:

```text
Check cluster
     ↓
Check nodes
     ↓
Check Pods
     ↓
Describe resource
     ↓
Check Events
     ↓
Check logs
     ↓
Identify root cause
2. Check Cluster
kubectl cluster-info

Then:

kubectl get nodes

Expected:

NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   ...   ...

If the node is not Ready:

kubectl describe node minikube

Check:

Conditions
Events
Memory pressure
Disk pressure
PID pressure
kubelet-related issues
3. Check Minikube
minikube status

Expected:

host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured

If Minikube is stopped:

minikube start

Verify:

kubectl get nodes
4. Node NotReady

Check:

kubectl get nodes
kubectl describe node <node>

Look at:

Conditions
Events

Possible causes:

kubelet stopped
container runtime problem
disk pressure
memory pressure
network problem
node unavailable
5. Pod Troubleshooting

Start with:

kubectl get pods -A

Then:

kubectl describe pod <pod>

Then:

kubectl logs <pod>

For a previously running container:

kubectl logs <pod> --previous
6. Important Principle

Do not immediately restart or delete a failed Pod.

First collect evidence:

Status
   ↓
Reason
   ↓
Events
   ↓
Logs
   ↓
Configuration
   ↓
Root Cause

Then apply the fix.

7. Architecture Troubleshooting Interview Scenario
Scenario

"Your application Pods are not starting. How do you troubleshoot?"

Answer:

"I first check the cluster and node status using kubectl get nodes. If the node is Ready, I check the Pod status using kubectl get pods. I then use kubectl describe pod to inspect the Pod state and Events, and kubectl logs if the container has started. Based on the evidence, I determine whether the problem is scheduling, image pulling, container configuration, application failure, networking, resources, or another dependency."

8. Key Commands Cheat Sheet
kubectl cluster-info

kubectl get nodes

kubectl get nodes -o wide

kubectl describe node <node>

kubectl get pods -A

kubectl describe pod <pod>

kubectl logs <pod>

kubectl logs <pod> --previous

kubectl get events --sort-by=.lastTimestamp

minikube status

minikube start
9. Key Learning

The most important architecture concept is:

API Server
    ↓
Desired State
    ↓
Controllers / Scheduler
    ↓
kubelet
    ↓
Container Runtime
    ↓
Running Workload

Kubernetes continuously reconciles:

Desired State ≠ Actual State
            ↓
       Take action
            ↓
Desired State = Actual State

These are the **first two GitHub-ready files** for `01-Architecture`. We should create them directly in your existing directory, review them, then commit this section before moving to `02-Pods`.
# Kubernetes Architecture — Troubleshooting Notes

## Issue 1 — Minikube stopped

### Symptom

```bash
minikube status

showed the cluster components were not running.

Diagnosis
minikube status
kubectl get nodes
Resolution
minikube start
Verification
kubectl get nodes
kubectl cluster-info
Issue 2 — ImagePullBackOff
Symptom

Pod was not starting and showed:

ErrImagePull
ImagePullBackOff
Troubleshooting
kubectl describe pod <pod>

Checked Events.

Root Cause

Invalid/nonexistent container image.

Resolution

Corrected the image name/tag and reapplied the manifest.

Verification
kubectl get pods

Pod became:

Running
Issue 3 — Failed Deployment Rollout
Symptom

Deployment rollout did not become healthy after changing the image.

Troubleshooting
kubectl rollout status deployment <name>
kubectl get rs
kubectl get pods
kubectl describe pod <pod>
Root Cause

New ReplicaSet was created using an invalid image.

Learning

Deployment creates a new ReplicaSet during a rollout. Always trace:

Deployment
   ↓
ReplicaSet
   ↓
Pod
   ↓
Events
General Rule

When troubleshooting Kubernetes:

Check the highest-level resource.
Follow the ownership chain.
Check the actual Pod.
Check Events.
Check logs if the container started.
Fix the root cause.
Verify recovery.
Deployment
    ↓
ReplicaSet
    ↓
Pod
    ↓
Container
    ↓
Application



