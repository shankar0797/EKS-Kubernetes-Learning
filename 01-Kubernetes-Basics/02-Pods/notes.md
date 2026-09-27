# Kubernetes Pod

## 1. What is a Pod?

A Pod is the smallest deployable and schedulable unit in Kubernetes.

Kubernetes does not normally schedule individual containers directly. It schedules Pods.

A Pod can contain one or more containers.

For our lab:

```text
Pod
└── nginx container
```

---

## 2. Why do we use Pods?

A Pod provides a common execution environment for its containers.

Containers inside the same Pod can share:

* Network namespace
* Pod IP address
* Storage volumes
* Lifecycle

In a simple application, one Pod commonly contains one application container.

---

## 3. Pod Architecture

Our current environment:

```text
EC2
└── Minikube
    └── Kubernetes Node
        └── Pod
            └── Nginx Container
```

Kubernetes flow:

```text
kubectl
   |
   v
API Server
   |
   v
Scheduler
   |
   v
Node
   |
   v
Kubelet
   |
   v
containerd
   |
   v
Nginx Container
```

---

# 4. Pod Manifest

File:

```text
nginx-pod.yaml
```

```yaml
apiVersion: v1
kind: Pod

metadata:
  name: nginx-pod

spec:
  containers:
    - name: nginx
      image: nginx:1.27
      ports:
        - containerPort: 80
```

---

# 5. Understanding the YAML

### apiVersion

```yaml
apiVersion: v1
```

Specifies the Kubernetes API version used for the Pod resource.

### kind

```yaml
kind: Pod
```

Specifies that we are creating a Pod.

### metadata

```yaml
metadata:
  name: nginx-pod
```

Defines metadata for the Pod.

The Pod name is:

```text
nginx-pod
```

### spec

```yaml
spec:
```

Defines the desired state of the Pod.

### containers

```yaml
containers:
  - name: nginx
    image: nginx:1.27
```

Defines the container that should run inside the Pod.

---

# 6. Validate the Manifest

Command:

```bash
kubectl apply --dry-run=client -f nginx-pod.yaml
```

### Why?

Validates the manifest locally without creating the actual Pod.

Expected:

```text
pod/nginx-pod created (dry run)
```

---

# 7. Create the Pod

Command:

```bash
kubectl apply -f nginx-pod.yaml
```

### Why?

Creates the Pod according to the desired state defined in the YAML.

Expected:

```text
pod/nginx-pod created
```

---

# 8. Check Pod Status

Command:

```bash
kubectl get pods
```

Expected:

```text
NAME        READY   STATUS    RESTARTS   AGE
nginx-pod   1/1     Running   0          ...
```

### Understanding READY

```text
1/1
```

means:

```text
1 container expected
1 container ready
```

If we see:

```text
0/1
```

the Pod exists but its container is not ready.

---

# 9. Get Detailed Pod Information

Command:

```bash
kubectl get pod nginx-pod -o wide
```

This provides additional information such as:

* Pod IP
* Node
* Status
* Readiness

Example:

```text
NAME        READY   STATUS    IP           NODE
nginx-pod   1/1     Running   10.244.0.3   minikube
```

---

# 10. Describe the Pod

Command:

```bash
kubectl describe pod nginx-pod
```

### Why?

Provides detailed information about:

* Scheduling
* Container state
* Image
* Volumes
* Conditions
* Events

The most important section during troubleshooting is:

```text
Events:
```

---

# 11. Pod Events

During our successful deployment we observed events such as:

```text
Scheduled
Pulling
Pulled
Created
Started
```

This represents approximately:

```text
Scheduler assigns Pod
        ↓
Kubelet pulls image
        ↓
Image available
        ↓
Container created
        ↓
Container started
```

---

# 12. Container Logs

Command:

```bash
kubectl logs nginx-pod
```

### Why?

Shows logs produced by the container.

Useful when investigating application startup problems or runtime failures.

---

# 13. Enter the Container

Command:

```bash
kubectl exec -it nginx-pod -- /bin/bash
```

### Why?

Allows us to execute commands inside the running container.

Inside the container:

```bash
hostname
```

Test Nginx:

```bash
curl localhost
```

Exit:

```bash
exit
```

---

# 14. Application Health Verification

We verified the Nginx application directly:

```bash
kubectl exec nginx-pod -- curl -I http://localhost
```

Result:

```text
HTTP/1.1 200 OK
Server: nginx/1.27.5
```

This proves:

```text
Pod exists
    ↓
Container is running
    ↓
Nginx is listening
    ↓
HTTP request succeeds
```

---

# 15. Intentional Failure — ImagePullBackOff

We intentionally changed:

```yaml
image: nginx:1.27
```

to:

```yaml
image: nginx:image-does-not-exist
```

Then applied the manifest.

Command:

```bash
kubectl apply -f nginx-pod.yaml
```

Pod status became:

```text
READY   STATUS
0/1     ImagePullBackOff
```

---

# 16. Troubleshooting ImagePullBackOff

First check:

```bash
kubectl get pods
```

Then:

```bash
kubectl describe pod nginx-pod
```

Look at:

```text
Events:
```

We found:

```text
Failed to pull image
```

and:

```text
ErrImagePull
```

and:

```text
ImagePullBackOff
```

The configured image was:

```text
nginx:image-does-not-exist
```

The registry returned:

```text
not found
```

---

# 17. Root Cause

The container image/tag did not exist.

The problem was:

```text
nginx:image-does-not-exist
```

not Kubernetes itself.

---

# 18. Fix

Changed the image back to:

```yaml
image: nginx:1.27
```

Then:

```bash
kubectl apply -f nginx-pod.yaml
```

---

# 19. Verify Recovery

Command:

```bash
kubectl get pod nginx-pod -o wide
```

Result:

```text
READY   STATUS
1/1     Running
```

Container state:

```text
State: Running
Ready: True
```

Application verification:

```bash
kubectl exec nginx-pod -- curl -I http://localhost
```

Result:

```text
HTTP/1.1 200 OK
```

---

# 20. Important Kubernetes Statuses

### Pending

Pod cannot currently be scheduled or started.

Possible causes:

* Insufficient CPU
* Insufficient memory
* Node selector mismatch
* Taints/tolerations
* PVC unavailable

### Running

Pod has been started.

Important:

Running does NOT automatically mean the application is healthy.

### ErrImagePull

Kubernetes attempted to pull the image but failed.

### ImagePullBackOff

Kubernetes is backing off before retrying the image pull.

Common causes:

* Wrong image name
* Wrong tag
* Private registry authentication
* Missing ImagePullSecret
* ECR permission problem
* Network/DNS problem

### CrashLoopBackOff

Container starts but repeatedly crashes.

Common causes:

* Application startup failure
* Incorrect configuration
* Missing environment variable
* Dependency unavailable
* Application exits immediately

---

# 21. Production Troubleshooting Checklist

If a Pod is not working:

```text
1. kubectl get pods
        ↓
2. kubectl describe pod <pod>
        ↓
3. Check Events
        ↓
4. kubectl logs <pod>
        ↓
5. Check container state
        ↓
6. Check image
        ↓
7. Check configuration
        ↓
8. Check resources
        ↓
9. Check networking
        ↓
10. Fix and verify
```

---

# 22. Commands Learned

```bash
kubectl apply -f nginx-pod.yaml

kubectl apply --dry-run=client -f nginx-pod.yaml

kubectl get pods

kubectl get pod nginx-pod -o wide

kubectl describe pod nginx-pod

kubectl logs nginx-pod

kubectl exec -it nginx-pod -- /bin/bash

kubectl exec nginx-pod -- curl -I http://localhost
```

---

# 23. What We Learned

### Conceptual

* Pod is the smallest Kubernetes deployable unit.
* Kubernetes schedules Pods.
* A Pod can contain one or more containers.
* Pod IP comes from the Kubernetes Pod network.
* Kubelet manages Pods on a node.
* containerd runs the containers.

### Practical

We learned how to:

* Create a Pod
* Inspect a Pod
* View Pod events
* View container logs
* Enter a container
* Test the application
* Troubleshoot ImagePullBackOff
* Identify root cause from Events
* Fix the image
* Verify application recovery

---

# 24. Interview Questions

### Q1. What is a Pod?

A Pod is the smallest deployable and schedulable unit in Kubernetes and can contain one or more containers.

### Q2. Is a Pod the same as a container?

No. A Pod is a Kubernetes abstraction that provides an execution environment for one or more containers.

### Q3. How do you troubleshoot ImagePullBackOff?

I first run:

```bash
kubectl get pods
```

Then:

```bash
kubectl describe pod <pod-name>
```

I check the Events section to determine whether the issue is an invalid image/tag, registry authentication, network/DNS, or registry availability.

### Q4. Does Running mean the application is healthy?

Not necessarily. I verify container readiness and application functionality using container logs, probes, or an application-level health check.

### Q5. What is the difference between ErrImagePull and ImagePullBackOff?

`ErrImagePull` means the image pull failed. `ImagePullBackOff` means Kubernetes is backing off and retrying the image pull.

### Q6. What is the difference between Pod IP and Service IP?

A Pod receives an IP from the Pod network and that IP can change when the Pod is recreated. A Service provides a stable network endpoint for accessing a group of Pods.

---

# 25. Production Scenario

**Scenario:**

A developer says:

> "My application Pod is down."

My initial approach:

```bash
kubectl get pods
```

If I see:

```text
ImagePullBackOff
```

I run:

```bash
kubectl describe pod <pod-name>
```

Then I inspect:

```text
Events
```

I identify the exact image-pull error, fix the underlying issue, and verify:

```bash
kubectl get pods
```

followed by an application-level health check.

---

# 26. Lab Status

* [x] Create Pod
* [x] Verify Pod
* [x] Inspect Pod
* [x] View logs
* [x] Execute commands inside Pod
* [x] Test Nginx
* [x] Break image
* [x] Troubleshoot ImagePullBackOff
* [x] Fix image
* [x] Verify recovery

Next topic:

**ReplicaSet → Deployment**
