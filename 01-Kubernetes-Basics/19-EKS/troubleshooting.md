# Kubernetes & Amazon EKS – Troubleshooting Notes

## Troubleshooting Method

Always use:

```text
Symptom
 ↓
Evidence
 ↓
Possible causes
 ↓
Isolation
 ↓
Root cause
 ↓
Resolution
 ↓
Verification
```

Do not change multiple things at once.

---

# 1. Universal First Checks

```bash
kubectl get pods -A
kubectl get nodes
kubectl get svc -A
kubectl get ingress -A
kubectl get events --sort-by=.lastTimestamp
```

For one Pod:

```bash
kubectl describe pod <pod>
kubectl logs <pod>
kubectl logs <pod> --previous
```

---

# 2. Pod Pending

### Symptoms
Pod remains `Pending`.

### Check

```bash
kubectl describe pod <pod>
kubectl get events --sort-by=.lastTimestamp
kubectl describe node <node>
```

### Common root causes
- Insufficient CPU/memory
- Taints/tolerations
- NodeSelector/affinity mismatch
- Node unavailable
- PVC not available

### Resolution
Fix the scheduling constraint or provide capacity.

### Verify

```bash
kubectl get pod <pod> -w
```

---

# 3. CrashLoopBackOff

### Symptoms
Container repeatedly starts and exits.

### Check

```bash
kubectl logs <pod>
kubectl logs <pod> --previous
kubectl describe pod <pod>
```

### Common causes
- Application crash
- Wrong command/arguments
- Missing environment variable
- ConfigMap/Secret problem
- Dependency failure
- Liveness probe failure

### Resolution
Fix the actual application/configuration/probe problem.

### Verify
Pod becomes stable and Ready.

---

# 4. ImagePullBackOff

### Check

```bash
kubectl describe pod <pod>
```

Look at Events.

### Causes
- Wrong image/tag
- Private registry authentication
- Image unavailable
- Registry/network/DNS issue

### Resolution
Correct image reference or registry authentication.

---

# 5. Running but Not Ready

### Check

```bash
kubectl describe pod <pod>
kubectl logs <pod>
```

### Causes
- Wrong readiness path
- Wrong port
- Application initialization incomplete
- Dependency unavailable
- Application listening elsewhere

### Important
A Running but unready Pod should not receive normal Service traffic.

---

# 6. Service Not Working

### Check

```bash
kubectl get svc
kubectl describe svc <service>
kubectl get endpoints <service>
kubectl get endpointslice
kubectl get pods --show-labels
```

### Most common root cause

Service selector does not match Pod labels.

```text
Service:
app: frontend

Pod:
app: backend

Result:
No matching endpoints
```

### Resolution
Correct labels or selector.

### Verify

```bash
kubectl get endpoints <service>
kubectl exec <client> -- curl http://<service>
```

---

# 7. Service Has No Endpoints

Check:

```bash
kubectl get endpoints <service>
kubectl get endpointslice
kubectl get pods --show-labels
kubectl describe svc <service>
```

Possible causes:

- Selector mismatch
- Pods not Ready
- Wrong namespace
- Pods unavailable

Trace:

```text
Service selector
 ↓
Matching Pods
 ↓
Ready state
 ↓
EndpointSlice
```

---

# 8. DNS Failure

### Check

```bash
kubectl exec <pod> -- cat /etc/resolv.conf
kubectl get pods -n kube-system
kubectl logs -n kube-system <coredns-pod>
```

### Causes
- CoreDNS not running
- CoreDNS configuration
- Network path to CoreDNS
- Incorrect service/namespace name
- NetworkPolicy blocking DNS

---

# 9. Pod-to-Pod Failure

### Check

```bash
kubectl get pods -o wide
kubectl exec <client> -- curl <pod-ip>:<port>
```

Then inspect:

- Pod IP
- Node
- CNI
- NetworkPolicy
- Security controls
- Application listener

For EKS:

```bash
kubectl get pods -n kube-system
kubectl get daemonset -n kube-system
```

---

# 10. Pod-to-Service Failure

Trace:

```text
DNS
 ↓
Service
 ↓
EndpointSlice
 ↓
Pod
 ↓
Application
```

Commands:

```bash
kubectl get svc
kubectl get endpoints
kubectl get endpointslice
kubectl exec <pod> -- nslookup <service>
kubectl exec <pod> -- curl -I http://<service>
```

---

# 11. Pod-to-Internet Failure in EKS

Conceptual path:

```text
Pod
 ↓
VPC CNI
 ↓
Node ENI
 ↓
Private subnet
 ↓
Route table
 ↓
NAT Gateway
 ↓
Internet Gateway
 ↓
Internet
```

Check:

- Pod/node subnet
- Route table
- NAT Gateway
- Security Groups
- Network ACLs
- DNS
- NetworkPolicy

A successful request proves connectivity, but exact AWS path should be verified from VPC resources.

---

# 12. Ingress 404

### Check

```bash
kubectl get ingress
kubectl describe ingress <ingress>
kubectl get svc
kubectl get endpoints
```

### Possible causes

- Wrong host
- Wrong path
- Wrong IngressClass
- Wrong Service name
- Wrong Service port
- Controller configuration
- Application itself returns 404

Trace:

```text
Client
 ↓
Load Balancer
 ↓
Ingress Controller
 ↓
Ingress Rule
 ↓
Service
 ↓
Pod
```

---

# 13. RBAC Forbidden

`forbidden` generally indicates an authorization problem.

Check:

```bash
kubectl auth can-i get pods
kubectl auth can-i get pods -n <namespace>
```

Inspect:

- Role
- ClusterRole
- RoleBinding
- ClusterRoleBinding
- ServiceAccount

---

# 14. Unauthorized vs Forbidden

```text
Unauthorized → authentication problem
Forbidden    → authorization/RBAC problem
```

This distinction is important in production and interviews.

---

# 15. PVC Pending

### Check

```bash
kubectl get pvc
kubectl describe pvc <pvc>
kubectl get storageclass
kubectl get pv
```

### Causes

- No StorageClass
- Incorrect StorageClass
- CSI driver problem
- Provisioning failure
- AZ constraints
- Backend capacity issue

### Resolution
Fix StorageClass/CSI/backend problem.

---

# 16. Storage Mount Failure

### Check

```bash
kubectl describe pod <pod>
kubectl describe pvc <pvc>
kubectl get pv
kubectl get storageclass
```

Look for:

- Mount errors
- Access-mode mismatch
- CSI errors
- Volume attachment problems
- Cloud IAM issues
- AZ restrictions

---

# 17. StatefulSet Failure

```bash
kubectl get statefulset
kubectl get pods
kubectl get pvc
kubectl describe statefulset <name>
```

Check the affected replica's:

- Pod
- PVC
- Events
- Storage backend

Remember:

```text
StatefulSet → stable identity + persistent storage pattern
```

---

# 18. Deployment Rollout Stuck

### Check

```bash
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl get pods
kubectl describe deployment <name>
kubectl describe pod <pod>
```

### Causes
- Bad image
- Readiness failure
- Insufficient capacity
- Bad configuration
- Dependency failure

Rollback when appropriate:

```bash
kubectl rollout undo deployment/<name>
```

---

# 19. HPA Not Scaling

### Check

```bash
kubectl get hpa
kubectl describe hpa <hpa>
kubectl top pods
```

### Causes

- Metrics unavailable
- Resource requests missing
- Target not reached
- HPA configuration issue
- Metrics component problem

Remember:

> HPA scales Pods, not nodes.

---

# 20. HPA Scales but Pods Stay Pending

Trace:

```text
HPA
 ↓
More Pods
 ↓
Scheduler
 ↓
Insufficient node capacity
 ↓
Node autoscaling
```

Then investigate Cluster Autoscaler/Karpenter and node capacity.

---

# 21. DaemonSet Not Running Everywhere

```bash
kubectl get daemonset -A
kubectl describe daemonset <name>
kubectl get nodes
```

Check:

- Node selectors
- Taints
- Tolerations
- Resource availability

---

# 22. Pod Scheduling Problem

```bash
kubectl describe pod <pod>
kubectl describe node <node>
```

Look for:

- Taints
- Labels
- NodeSelector
- Affinity/anti-affinity
- Resource pressure

---

# 23. EKS Node NotReady

```bash
kubectl get nodes
kubectl describe node <node>
kubectl get pods -n kube-system -o wide
```

Check:

- kubelet
- VPC CNI
- kube-proxy
- Node conditions
- Instance health
- Networking
- IAM
- Resource pressure

---

# 24. EKS VPC CNI Problem

```bash
kubectl get pods -n kube-system -l k8s-app=aws-node
kubectl logs -n kube-system <aws-node-pod>
kubectl get daemonset -n kube-system aws-node
```

Investigate:

- Available IPs
- ENI/IP capacity
- Prefix delegation
- Subnet capacity
- Security Groups
- IAM permissions
- CNI configuration

Important:

> EKS can run out of Pod IP capacity even when CPU and memory are still available.

---

# 25. CoreDNS Problem in EKS

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system <coredns-pod>
kubectl get svc -n kube-system
kubectl exec <pod> -- cat /etc/resolv.conf
```

Check:

- CoreDNS Pods
- CoreDNS Service
- DNS configuration
- Network connectivity to DNS

---

# 26. kube-proxy Problem

```bash
kubectl get pods -n kube-system -l k8s-app=kube-proxy
kubectl logs -n kube-system <kube-proxy-pod>
```

Investigate when Service networking behaves unexpectedly.

---

# 27. EKS IAM Problem

Classify first:

```text
AWS authentication
 ↓
AWS IAM authorization
 ↓
Kubernetes authorization
 ↓
Pod workload IAM
```

Useful:

```bash
aws sts get-caller-identity
kubectl auth can-i <verb> <resource>
```

For workload IAM inspect:

- ServiceAccount
- IRSA or EKS Pod Identity
- IAM role
- Trust relationship
- IAM permissions

---

# 28. ALB / Load Balancer Controller Problem

```bash
kubectl get ingress
kubectl describe ingress <ingress>
kubectl get svc
kubectl get endpoints
```

Controller:

```bash
kubectl get deployment -A | grep load-balancer
kubectl logs -n <namespace> <controller-pod>
```

Trace:

```text
Ingress
 ↓
AWS Load Balancer Controller
 ↓
ALB
 ↓
Target Group
 ↓
Node/Pod
```

Common causes:

- Wrong IngressClass
- IAM permissions
- Wrong annotations
- Wrong Service port
- Unhealthy targets
- Security Groups
- Subnet configuration

---

# 29. EKS Storage Troubleshooting

## EBS

Check:

- EBS CSI driver
- IAM
- PVC
- StorageClass
- AZ
- Volume attachment

## EFS

Check:

- EFS CSI driver
- Mount targets
- Security Groups
- Network connectivity
- Access points where applicable

---

# 30. EKS Upgrade Troubleshooting

## Before upgrade

```bash
aws eks describe-cluster   --name eks-lab   --region ap-south-1   --query 'cluster.{Name:name,Version:version,Status:status,PlatformVersion:platformVersion}'   --output table

kubectl get nodes
kubectl get pods -A
kubectl get pdb -A
kubectl get events --sort-by=.lastTimestamp
```

Check:

- Cluster health
- Workloads
- PDBs
- Capacity
- Deprecated APIs
- Upgrade Insights
- Add-on compatibility
- CSI/controller compatibility
- Recovery/backup readiness

### Key rule

```text
Control plane upgrade
        ≠
Worker node upgrade
```

They are separate operations.

---

# 31. Upgrade Failure: Deprecated APIs

### Symptoms

- Upgrade warnings
- Upgrade failure
- Manifests/controllers fail after version change

### Resolution

Identify affected API, update manifests/controllers, test and then upgrade.

---

# 32. Upgrade Failure: Add-on Incompatibility

Possible components:

- VPC CNI
- CoreDNS
- kube-proxy
- EBS CSI
- EFS CSI
- AWS Load Balancer Controller
- Monitoring/logging agents

Resolution:

1. Check supported versions.
2. Upgrade compatible add-ons.
3. Validate after each change.

---

# 33. Upgrade Failure: Node Drain Blocked

Check:

```bash
kubectl get pdb -A
kubectl describe pdb <pdb> -n <namespace>
```

Possible causes:

- PDB too restrictive
- Too few replicas
- Readiness failures
- Insufficient replacement capacity

Resolution:

- Ensure enough replicas.
- Review PDB.
- Ensure capacity.
- Fix readiness problems.

---

# 34. Production Troubleshooting Checklist

When an application is broken:

```text
1. Pod status?
2. Pod Ready?
3. Application listening?
4. Logs?
5. Service correct?
6. EndpointSlice populated?
7. DNS working?
8. Ingress/LB routing?
9. Network/security allowed?
10. Resources sufficient?
11. Dependencies healthy?
```

---

# 35. Final Interview Framework

For any Kubernetes troubleshooting question:

> First I confirm the symptom, then inspect the affected resource using get/describe/logs/events. I isolate the failure layer—application, configuration, scheduling, networking, storage or security. Once the evidence identifies the root cause, I apply the smallest safe fix and verify recovery. Finally, I add preventive controls if the issue can recur.

This is the core troubleshooting approach to carry into projects.
