# Kubernetes & Amazon EKS – Complete Learning Notes

## Scope

Final notes for the Kubernetes learning completed before project-based learning.

### Completed
1. Kubernetes Basics & Architecture
2. kubectl
3. Pods
4. ReplicaSets
5. Deployments, Rolling Updates & Rollbacks
6. Probes
7. Services
8. Networking
9. Configuration
10. Storage
11. Workloads
12. Scheduling
13. Security
14. Helm
15. Observability
16. Autoscaling
17. Amazon EKS

Advanced production depth is intentionally project-driven and will be learned when required by projects.

---

## 1. Kubernetes Basics

Kubernetes is a container orchestration platform used to deploy, manage, scale and troubleshoot containerized applications.

It solves deployment, scaling, self-healing, service discovery, rolling updates, configuration, storage and scheduling problems.

### Architecture

```text
                 Kubernetes Cluster
                        |
          +-------------+-------------+
          |                           |
     Control Plane                Data Plane
          |                           |
 API Server / Scheduler          Worker Nodes
 Controllers / etcd              kubelet/runtime
                                 kube-proxy/Pods
```

- **API Server:** entry point for Kubernetes API operations.
- **etcd:** stores cluster state.
- **Scheduler:** selects nodes for Pods.
- **Controller Manager:** reconciles desired and actual state.
- **kubelet:** manages Pods on a node.
- **Container runtime:** runs containers.
- **kube-proxy:** supports Service networking.

---

## 2. kubectl

`kubectl` communicates with the Kubernetes API Server.

```bash
kubectl get pods -A
kubectl describe pod <pod>
kubectl logs <pod>
kubectl logs <pod> --previous
kubectl exec -it <pod> -- sh
kubectl get nodes
kubectl get events --sort-by=.lastTimestamp
```

Core troubleshooting pattern:

```text
get → describe → logs → exec → events
```

---

## 3. Pods

A Pod is Kubernetes' smallest deployable unit.

Containers in one Pod share the network namespace/IP and can share volumes.

Pods are normally managed by controllers rather than manually created for production applications.

---

## 4. ReplicaSets

ReplicaSet maintains a requested number of matching Pods.

```text
Desired = 3
Current = 2
    ↓
ReplicaSet creates another Pod
    ↓
Current = 3
```

Deployments normally manage ReplicaSets.

---

## 5. Deployments

Deployment manages stateless application releases and provides:

- Replica management
- Rolling updates
- Rollbacks
- Revision history
- Declarative updates

Useful commands:

```bash
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>
```

A Pod being `Running` alone does not prove the release is healthy; verify readiness and application behavior.

---

## 6. Probes

### Startup
Determines whether a slow-starting application has finished initialization.

### Readiness
Determines whether a Pod should receive traffic.

### Liveness
Determines whether Kubernetes should restart a container.

```text
Startup   → Is startup complete?
Readiness → Can I receive traffic?
Liveness  → Should I be restarted?
```

---

## 7. Common Pod States

### Pending
Usually scheduling, capacity, storage or placement constraints.

### CrashLoopBackOff
Repeated container crashes. Investigate application errors, configuration, dependencies and probes.

```bash
kubectl describe pod <pod>
kubectl logs <pod>
kubectl logs <pod> --previous
```

### ImagePullBackOff
Investigate image name/tag, registry access, credentials and connectivity.

---

## 8. Services

A Service provides a stable network endpoint for a group of Pods.

### ClusterIP
Internal cluster access.

### NodePort
Exposes a port on nodes.

### LoadBalancer
Requests an external/cloud load balancer where supported.

```text
Client
  ↓
Service
  ↓
EndpointSlice
  ↓
Ready Pods
```

Check:

```bash
kubectl get svc
kubectl get endpoints
kubectl get endpointslice
```

Service discovery uses Kubernetes DNS:

```text
service-name
service-name.namespace
service-name.namespace.svc.cluster.local
```

---

## 9. Ingress

Ingress defines HTTP/HTTPS routing rules.

Example:

```text
/users  → user-service
/orders → order-service
```

An Ingress Controller implements those rules.

Typical flow:

```text
User → Load Balancer → Ingress Controller → Service → Pod
```

---

## 10. Kubernetes Networking

Important concepts:

- Pod IP
- Service IP
- DNS
- CNI
- kube-proxy
- NetworkPolicy
- Ingress

### Pod-to-Pod

```text
Pod A → network → Pod B
```

### Pod-to-Service

```text
Pod → Service → EndpointSlice → Pod
```

### Pod-to-Internet

Conceptually:

```text
Pod → CNI/node → private subnet → NAT Gateway → Internet Gateway → Internet
```

Exact cloud path should be verified from VPC routes/NAT rather than assumed.

---

## 11. Configuration

### ConfigMap
Non-sensitive application configuration.

### Secret
Sensitive configuration such as passwords, tokens and keys.

### Namespace
Logical isolation and organization boundary.

Typical environments:

```text
dev
test
prod
monitoring
```

---

## 12. Resources

### Requests
Resources used for scheduling decisions.

### Limits
Maximum resource usage for a container.

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

Too-high requests can cause Pending Pods. Too-low memory limits can cause OOMKilled.

---

## 13. Storage

### container filesystem
Normally temporary.

### emptyDir
Temporary Pod-level shared storage.

### hostPath
Mounts a node path; useful in selected cases but less portable.

### PV
Represents persistent storage.

### PVC
Requests persistent storage.

### StorageClass
Defines dynamic provisioning behavior.

```text
Pod → PVC → PV → Storage backend
PVC → StorageClass → CSI driver → Cloud storage
```

### StatefulSet
Used for workloads needing stable identity and persistent storage.

`volumeClaimTemplates` can create storage per replica:

```text
db-0 → pvc-db-0
db-1 → pvc-db-1
db-2 → pvc-db-2
```

### EKS
- EBS: block storage.
- EFS: shared filesystem.
- CSI drivers integrate cloud storage with Kubernetes.

---

## 14. Workloads

- **Deployment:** stateless applications.
- **StatefulSet:** stable identity/storage.
- **DaemonSet:** one Pod on selected/all nodes.
- **Job:** run-to-completion task.
- **CronJob:** scheduled Jobs.

DaemonSets are common for node agents such as logging, monitoring and networking components.

---

## 15. Scheduling

Important concepts:

- Resource requests
- Labels
- NodeSelector
- Affinity
- Anti-affinity
- Taints
- Tolerations
- Topology/failure-domain placement

Production goal:

```text
Replica 1 → AZ-A
Replica 2 → AZ-B
Replica 3 → AZ-C
```

Avoid concentrating critical replicas on one failure domain.

---

## 16. Security

Security layers:

```text
AWS IAM
  ↓
Kubernetes authentication
  ↓
Kubernetes RBAC
  ↓
Network controls
  ↓
Pod/application security
```

### RBAC
Uses:

- Role
- ClusterRole
- RoleBinding
- ClusterRoleBinding

### ServiceAccount
Identity for workloads inside Kubernetes.

### NetworkPolicy
Controls allowed Pod traffic where supported.

Do not confuse:

```text
IAM          → AWS permissions
RBAC         → Kubernetes API permissions
NetworkPolicy → Pod network traffic
Security Group → AWS network boundary
```

---

## 17. Helm

Helm is a Kubernetes package manager.

Typical chart:

```text
mychart/
├── Chart.yaml
├── values.yaml
└── templates/
```

Example:

```yaml
replicaCount: 2
```

Template:

```yaml
replicas: {{ .Values.replicaCount }}
```

Environment override:

```bash
helm upgrade --install myapp ./mychart -f values-dev.yaml
```

Helm provides reusable templates, versioned releases and rollback capability.

---

## 18. Observability

Three major areas:

```text
Metrics
Logs
Traces
```

Tools covered:

- CloudWatch
- Container Insights
- Prometheus
- Grafana
- Fluent Bit
- Kubernetes events

Useful:

```bash
kubectl top pods
kubectl top nodes
kubectl get events --sort-by=.lastTimestamp
```

---

## 19. Autoscaling

### HPA
Scales Pod replicas.

### Cluster Autoscaler
Adjusts node count.

### Karpenter
Provisions suitable AWS capacity dynamically.

### Fargate
Runs selected Pods using serverless compute.

Remember:

```text
HPA → Pods
Cluster Autoscaler → Nodes
Karpenter → AWS capacity
```

---

# Amazon EKS

## 20. What is EKS?

Amazon Elastic Kubernetes Service is AWS's managed Kubernetes service.

AWS manages the EKS control plane; data-plane management depends on the chosen capacity model.

### EKS vs Minikube

| Minikube | EKS |
|---|---|
| Local learning | AWS managed Kubernetes |
| Local resources | AWS infrastructure |
| Simple setup | Production-oriented |
| Limited AWS integration | Deep AWS integration |

---

## 21. EKS Networking

EKS integrates with AWS VPC.

Important components:

- VPC
- Subnets
- Route tables
- ENIs
- Security Groups
- VPC CNI
- NAT Gateway
- Internet Gateway

### VPC CNI

Provides AWS VPC networking for Pods. Pod IP allocation depends on CNI configuration, ENI/IP capacity, prefix delegation and instance limits.

Do **not** say every Pod necessarily gets its own ENI.

---

## 22. EKS Lab Results

Cluster used:

```text
Name: eks-lab
Region: ap-south-1
Kubernetes: 1.34
VPC: 192.168.0.0/16
```

Verified:

- Multi-AZ worker nodes
- Pod IP allocation
- ENIs
- VPC CNI
- Pod-to-Pod communication
- ClusterIP Service communication
- EndpointSlice
- CoreDNS
- Pod-to-Internet connectivity

Useful commands:

```bash
kubectl get pods -o wide
kubectl get svc
kubectl get endpoints
kubectl get endpointslice
kubectl exec <pod> -- curl -I http://<service>
```

---

## 23. CoreDNS

CoreDNS provides Kubernetes DNS.

Typical Pod resolver:

```text
nameserver 10.100.0.10
search default.svc.cluster.local
       svc.cluster.local
       cluster.local
```

Troubleshooting:

```bash
kubectl get pods -n kube-system
kubectl logs -n kube-system <coredns-pod>
kubectl exec <pod> -- cat /etc/resolv.conf
```

---

## 24. EKS Add-ons

Covered:

- VPC CNI
- CoreDNS
- kube-proxy

```text
VPC CNI    → Pod networking
CoreDNS    → DNS
kube-proxy → Service networking behavior
```

---

## 25. EKS Security

### IAM
AWS permissions.

### EKS Access Entries
Modern IAM-to-EKS access mechanism.

### IRSA
IAM Roles for Service Accounts.

### EKS Pod Identity
AWS workload identity mechanism.

Production principle:

> Give workloads only the AWS permissions they actually require.

---

## 26. EKS Load Balancing

### ALB
Layer 7 HTTP/HTTPS routing.

### NLB
Layer 4 network traffic such as TCP/UDP/TLS.

### AWS Load Balancer Controller
Watches Kubernetes resources and configures AWS load-balancing resources.

Flow:

```text
User
 ↓
ALB/NLB
 ↓
Ingress/Service
 ↓
Pod
```

Target modes:

- Instance
- IP

The controller was studied conceptually; detailed deployment/configuration is reserved for projects.

---

## 27. EKS Storage

### EBS CSI
Block storage integration.

```text
Pod → PVC → StorageClass → EBS CSI → EBS
```

### EFS CSI
Shared filesystem integration.

Use EFS when multiple workloads need shared filesystem access.

---

## 28. EKS Autoscaling

Covered:

- HPA
- Cluster Autoscaler
- Karpenter
- EKS Auto Mode
- Fargate

---

## 29. EKS Observability

Covered:

- CloudWatch
- Container Insights
- Prometheus
- Grafana
- Fluent Bit
- EKS control-plane logging

Monitor:

```text
Cluster
Nodes
Pods
Applications
Dependencies
User experience
```

---

## 30. EKS Cluster Upgrade

Production upgrade sequence:

```text
1. Current/target version
2. Upgrade Insights
3. Deprecated APIs
4. Workload health
5. PDBs
6. Capacity
7. Recovery/backup readiness
8. Control-plane upgrade
9. Validate
10. Compatible add-ons
11. Node-group upgrade
12. Validate workloads
13. Monitor
```

Important:

> Control-plane upgrade and worker-node upgrade are separate operations.

Lab baseline:

```text
Cluster: eks-lab
Region: ap-south-1
Version: 1.34
Status: ACTIVE
Managed nodes: 2
Add-ons: coredns, kube-proxy, vpc-cni
```

Upgrade Insights for the target version showed passing checks for:

- Amazon Linux compatibility
- EKS add-on compatibility
- Kubelet version skew
- kube-proxy version skew
- Cluster health issues

---

# 31. Production Troubleshooting Mental Model

Trace the request:

```text
User
 ↓
DNS
 ↓
Load Balancer
 ↓
Ingress
 ↓
Service
 ↓
EndpointSlice
 ↓
Pod
 ↓
Application
 ↓
Dependency
```

Classify symptoms:

```text
Pending           → scheduling/capacity/storage
CrashLoopBackOff  → application/config/probe/dependency
ImagePullBackOff  → image/registry/auth
Timeout           → DNS/route/network/security/LB
Refused           → destination reached but listener unavailable
Unauthorized      → authentication
Forbidden         → authorization/RBAC
```

---

# 32. Interview Q&A

### What is Kubernetes?
A container orchestration platform that automates deployment, scaling, networking and lifecycle management.

### Pod vs container?
A container is the runtime unit; a Pod is Kubernetes' smallest deployable unit and can contain one or more containers.

### Deployment vs ReplicaSet?
ReplicaSet maintains replicas; Deployment manages ReplicaSets and provides rolling updates and rollbacks.

### Service vs Ingress?
Service provides stable access to Pods. Ingress defines HTTP/HTTPS routing rules.

### Readiness vs liveness?
Readiness controls traffic eligibility; liveness controls restart behavior.

### Requests vs limits?
Requests influence scheduling; limits cap container resource usage.

### PV vs PVC?
PV represents storage; PVC requests storage.

### StatefulSet vs Deployment?
StatefulSet provides stable identity/storage patterns; Deployment is generally used for stateless workloads.

### HPA vs Cluster Autoscaler?
HPA scales Pods; Cluster Autoscaler changes node count.

### RBAC vs IAM?
RBAC controls Kubernetes API permissions; IAM controls AWS permissions.

### What does VPC CNI do?
Provides AWS VPC networking for EKS Pods.

### Why CoreDNS?
Provides Kubernetes DNS and service discovery.

### What is IRSA?
A mechanism allowing a Kubernetes ServiceAccount to use an AWS IAM role.

### What is EKS?
AWS's managed Kubernetes service.

### How do you troubleshoot a Pod?
Check status, describe output, logs, previous logs and events, then inspect configuration, networking, resources and dependencies.

### How do you troubleshoot a Service?
Check Service selector, Pod labels, EndpointSlice, readiness and DNS, then test connectivity from a client Pod.

### How do you troubleshoot EKS networking?
Start with Pod IP/node/subnet, then inspect VPC CNI, routes, Security Groups, NetworkPolicy, NAT and DNS.

### How do you approach an EKS upgrade?
Check compatibility and Upgrade Insights, verify workloads/PDBs/capacity, upgrade control plane, validate add-ons, upgrade nodes separately, then validate and monitor.

---

# 33. Final Engineering Mindset

The objective is not to memorize commands.

The important skill is:

```text
Observe
 ↓
Classify
 ↓
Collect evidence
 ↓
Find root cause
 ↓
Fix safely
 ↓
Verify
 ↓
Prevent recurrence
```

Anything requiring deeper production implementation will be learned during the project phase.
# Kubernetes & Amazon EKS – Complete Learning Notes

## Scope

Final notes for the Kubernetes learning completed before project-based learning.

### Completed
1. Kubernetes Basics & Architecture
2. kubectl
3. Pods
4. ReplicaSets
5. Deployments, Rolling Updates & Rollbacks
6. Probes
7. Services
8. Networking
9. Configuration
10. Storage
11. Workloads
12. Scheduling
13. Security
14. Helm
15. Observability
16. Autoscaling
17. Amazon EKS

Advanced production depth is intentionally project-driven and will be learned when required by projects.

---

## 1. Kubernetes Basics

Kubernetes is a container orchestration platform used to deploy, manage, scale and troubleshoot containerized applications.

It solves deployment, scaling, self-healing, service discovery, rolling updates, configuration, storage and scheduling problems.

### Architecture

```text
                 Kubernetes Cluster
                        |
          +-------------+-------------+
          |                           |
     Control Plane                Data Plane
          |                           |
 API Server / Scheduler          Worker Nodes
 Controllers / etcd              kubelet/runtime
                                 kube-proxy/Pods
```

- **API Server:** entry point for Kubernetes API operations.
- **etcd:** stores cluster state.
- **Scheduler:** selects nodes for Pods.
- **Controller Manager:** reconciles desired and actual state.
- **kubelet:** manages Pods on a node.
- **Container runtime:** runs containers.
- **kube-proxy:** supports Service networking.

---

## 2. kubectl

`kubectl` communicates with the Kubernetes API Server.

```bash
kubectl get pods -A
kubectl describe pod <pod>
kubectl logs <pod>
kubectl logs <pod> --previous
kubectl exec -it <pod> -- sh
kubectl get nodes
kubectl get events --sort-by=.lastTimestamp
```

Core troubleshooting pattern:

```text
get → describe → logs → exec → events
```

---

## 3. Pods

A Pod is Kubernetes' smallest deployable unit.

Containers in one Pod share the network namespace/IP and can share volumes.

Pods are normally managed by controllers rather than manually created for production applications.

---

## 4. ReplicaSets

ReplicaSet maintains a requested number of matching Pods.

```text
Desired = 3
Current = 2
    ↓
ReplicaSet creates another Pod
    ↓
Current = 3
```

Deployments normally manage ReplicaSets.

---

## 5. Deployments

Deployment manages stateless application releases and provides:

- Replica management
- Rolling updates
- Rollbacks
- Revision history
- Declarative updates

Useful commands:

```bash
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>
```

A Pod being `Running` alone does not prove the release is healthy; verify readiness and application behavior.

---

## 6. Probes

### Startup
Determines whether a slow-starting application has finished initialization.

### Readiness
Determines whether a Pod should receive traffic.

### Liveness
Determines whether Kubernetes should restart a container.

```text
Startup   → Is startup complete?
Readiness → Can I receive traffic?
Liveness  → Should I be restarted?
```

---

## 7. Common Pod States

### Pending
Usually scheduling, capacity, storage or placement constraints.

### CrashLoopBackOff
Repeated container crashes. Investigate application errors, configuration, dependencies and probes.

```bash
kubectl describe pod <pod>
kubectl logs <pod>
kubectl logs <pod> --previous
```

### ImagePullBackOff
Investigate image name/tag, registry access, credentials and connectivity.

---

## 8. Services

A Service provides a stable network endpoint for a group of Pods.

### ClusterIP
Internal cluster access.

### NodePort
Exposes a port on nodes.

### LoadBalancer
Requests an external/cloud load balancer where supported.

```text
Client
  ↓
Service
  ↓
EndpointSlice
  ↓
Ready Pods
```

Check:

```bash
kubectl get svc
kubectl get endpoints
kubectl get endpointslice
```

Service discovery uses Kubernetes DNS:

```text
service-name
service-name.namespace
service-name.namespace.svc.cluster.local
```

---

## 9. Ingress

Ingress defines HTTP/HTTPS routing rules.

Example:

```text
/users  → user-service
/orders → order-service
```

An Ingress Controller implements those rules.

Typical flow:

```text
User → Load Balancer → Ingress Controller → Service → Pod
```

---

## 10. Kubernetes Networking

Important concepts:

- Pod IP
- Service IP
- DNS
- CNI
- kube-proxy
- NetworkPolicy
- Ingress

### Pod-to-Pod

```text
Pod A → network → Pod B
```

### Pod-to-Service

```text
Pod → Service → EndpointSlice → Pod
```

### Pod-to-Internet

Conceptually:

```text
Pod → CNI/node → private subnet → NAT Gateway → Internet Gateway → Internet
```

Exact cloud path should be verified from VPC routes/NAT rather than assumed.

---

## 11. Configuration

### ConfigMap
Non-sensitive application configuration.

### Secret
Sensitive configuration such as passwords, tokens and keys.

### Namespace
Logical isolation and organization boundary.

Typical environments:

```text
dev
test
prod
monitoring
```

---

## 12. Resources

### Requests
Resources used for scheduling decisions.

### Limits
Maximum resource usage for a container.

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

Too-high requests can cause Pending Pods. Too-low memory limits can cause OOMKilled.

---

## 13. Storage

### container filesystem
Normally temporary.

### emptyDir
Temporary Pod-level shared storage.

### hostPath
Mounts a node path; useful in selected cases but less portable.

### PV
Represents persistent storage.

### PVC
Requests persistent storage.

### StorageClass
Defines dynamic provisioning behavior.

```text
Pod → PVC → PV → Storage backend
PVC → StorageClass → CSI driver → Cloud storage
```

### StatefulSet
Used for workloads needing stable identity and persistent storage.

`volumeClaimTemplates` can create storage per replica:

```text
db-0 → pvc-db-0
db-1 → pvc-db-1
db-2 → pvc-db-2
```

### EKS
- EBS: block storage.
- EFS: shared filesystem.
- CSI drivers integrate cloud storage with Kubernetes.

---

## 14. Workloads

- **Deployment:** stateless applications.
- **StatefulSet:** stable identity/storage.
- **DaemonSet:** one Pod on selected/all nodes.
- **Job:** run-to-completion task.
- **CronJob:** scheduled Jobs.

DaemonSets are common for node agents such as logging, monitoring and networking components.

---

## 15. Scheduling

Important concepts:

- Resource requests
- Labels
- NodeSelector
- Affinity
- Anti-affinity
- Taints
- Tolerations
- Topology/failure-domain placement

Production goal:

```text
Replica 1 → AZ-A
Replica 2 → AZ-B
Replica 3 → AZ-C
```

Avoid concentrating critical replicas on one failure domain.

---

## 16. Security

Security layers:

```text
AWS IAM
  ↓
Kubernetes authentication
  ↓
Kubernetes RBAC
  ↓
Network controls
  ↓
Pod/application security
```

### RBAC
Uses:

- Role
- ClusterRole
- RoleBinding
- ClusterRoleBinding

### ServiceAccount
Identity for workloads inside Kubernetes.

### NetworkPolicy
Controls allowed Pod traffic where supported.

Do not confuse:

```text
IAM          → AWS permissions
RBAC         → Kubernetes API permissions
NetworkPolicy → Pod network traffic
Security Group → AWS network boundary
```

---

## 17. Helm

Helm is a Kubernetes package manager.

Typical chart:

```text
mychart/
├── Chart.yaml
├── values.yaml
└── templates/
```

Example:

```yaml
replicaCount: 2
```

Template:

```yaml
replicas: {{ .Values.replicaCount }}
```

Environment override:

```bash
helm upgrade --install myapp ./mychart -f values-dev.yaml
```

Helm provides reusable templates, versioned releases and rollback capability.

---

## 18. Observability

Three major areas:

```text
Metrics
Logs
Traces
```

Tools covered:

- CloudWatch
- Container Insights
- Prometheus
- Grafana
- Fluent Bit
- Kubernetes events

Useful:

```bash
kubectl top pods
kubectl top nodes
kubectl get events --sort-by=.lastTimestamp
```

---

## 19. Autoscaling

### HPA
Scales Pod replicas.

### Cluster Autoscaler
Adjusts node count.

### Karpenter
Provisions suitable AWS capacity dynamically.

### Fargate
Runs selected Pods using serverless compute.

Remember:

```text
HPA → Pods
Cluster Autoscaler → Nodes
Karpenter → AWS capacity
```

---

# Amazon EKS

## 20. What is EKS?

Amazon Elastic Kubernetes Service is AWS's managed Kubernetes service.

AWS manages the EKS control plane; data-plane management depends on the chosen capacity model.

### EKS vs Minikube

| Minikube | EKS |
|---|---|
| Local learning | AWS managed Kubernetes |
| Local resources | AWS infrastructure |
| Simple setup | Production-oriented |
| Limited AWS integration | Deep AWS integration |

---

## 21. EKS Networking

EKS integrates with AWS VPC.

Important components:

- VPC
- Subnets
- Route tables
- ENIs
- Security Groups
- VPC CNI
- NAT Gateway
- Internet Gateway

### VPC CNI

Provides AWS VPC networking for Pods. Pod IP allocation depends on CNI configuration, ENI/IP capacity, prefix delegation and instance limits.

Do **not** say every Pod necessarily gets its own ENI.

---

## 22. EKS Lab Results

Cluster used:

```text
Name: eks-lab
Region: ap-south-1
Kubernetes: 1.34
VPC: 192.168.0.0/16
```

Verified:

- Multi-AZ worker nodes
- Pod IP allocation
- ENIs
- VPC CNI
- Pod-to-Pod communication
- ClusterIP Service communication
- EndpointSlice
- CoreDNS
- Pod-to-Internet connectivity

Useful commands:

```bash
kubectl get pods -o wide
kubectl get svc
kubectl get endpoints
kubectl get endpointslice
kubectl exec <pod> -- curl -I http://<service>
```

---

## 23. CoreDNS

CoreDNS provides Kubernetes DNS.

Typical Pod resolver:

```text
nameserver 10.100.0.10
search default.svc.cluster.local
       svc.cluster.local
       cluster.local
```

Troubleshooting:

```bash
kubectl get pods -n kube-system
kubectl logs -n kube-system <coredns-pod>
kubectl exec <pod> -- cat /etc/resolv.conf
```

---

## 24. EKS Add-ons

Covered:

- VPC CNI
- CoreDNS
- kube-proxy

```text
VPC CNI    → Pod networking
CoreDNS    → DNS
kube-proxy → Service networking behavior
```

---

## 25. EKS Security

### IAM
AWS permissions.

### EKS Access Entries
Modern IAM-to-EKS access mechanism.

### IRSA
IAM Roles for Service Accounts.

### EKS Pod Identity
AWS workload identity mechanism.

Production principle:

> Give workloads only the AWS permissions they actually require.

---

## 26. EKS Load Balancing

### ALB
Layer 7 HTTP/HTTPS routing.

### NLB
Layer 4 network traffic such as TCP/UDP/TLS.

### AWS Load Balancer Controller
Watches Kubernetes resources and configures AWS load-balancing resources.

Flow:

```text
User
 ↓
ALB/NLB
 ↓
Ingress/Service
 ↓
Pod
```

Target modes:

- Instance
- IP

The controller was studied conceptually; detailed deployment/configuration is reserved for projects.

---

## 27. EKS Storage

### EBS CSI
Block storage integration.

```text
Pod → PVC → StorageClass → EBS CSI → EBS
```

### EFS CSI
Shared filesystem integration.

Use EFS when multiple workloads need shared filesystem access.

---

## 28. EKS Autoscaling

Covered:

- HPA
- Cluster Autoscaler
- Karpenter
- EKS Auto Mode
- Fargate

---

## 29. EKS Observability

Covered:

- CloudWatch
- Container Insights
- Prometheus
- Grafana
- Fluent Bit
- EKS control-plane logging

Monitor:

```text
Cluster
Nodes
Pods
Applications
Dependencies
User experience
```

---

## 30. EKS Cluster Upgrade

Production upgrade sequence:

```text
1. Current/target version
2. Upgrade Insights
3. Deprecated APIs
4. Workload health
5. PDBs
6. Capacity
7. Recovery/backup readiness
8. Control-plane upgrade
9. Validate
10. Compatible add-ons
11. Node-group upgrade
12. Validate workloads
13. Monitor
```

Important:

> Control-plane upgrade and worker-node upgrade are separate operations.

Lab baseline:

```text
Cluster: eks-lab
Region: ap-south-1
Version: 1.34
Status: ACTIVE
Managed nodes: 2
Add-ons: coredns, kube-proxy, vpc-cni
```

Upgrade Insights for the target version showed passing checks for:

- Amazon Linux compatibility
- EKS add-on compatibility
- Kubelet version skew
- kube-proxy version skew
- Cluster health issues

---

# 31. Production Troubleshooting Mental Model

Trace the request:

```text
User
 ↓
DNS
 ↓
Load Balancer
 ↓
Ingress
 ↓
Service
 ↓
EndpointSlice
 ↓
Pod
 ↓
Application
 ↓
Dependency
```

Classify symptoms:

```text
Pending           → scheduling/capacity/storage
CrashLoopBackOff  → application/config/probe/dependency
ImagePullBackOff  → image/registry/auth
Timeout           → DNS/route/network/security/LB
Refused           → destination reached but listener unavailable
Unauthorized      → authentication
Forbidden         → authorization/RBAC
```

---

# 32. Interview Q&A

### What is Kubernetes?
A container orchestration platform that automates deployment, scaling, networking and lifecycle management.

### Pod vs container?
A container is the runtime unit; a Pod is Kubernetes' smallest deployable unit and can contain one or more containers.

### Deployment vs ReplicaSet?
ReplicaSet maintains replicas; Deployment manages ReplicaSets and provides rolling updates and rollbacks.

### Service vs Ingress?
Service provides stable access to Pods. Ingress defines HTTP/HTTPS routing rules.

### Readiness vs liveness?
Readiness controls traffic eligibility; liveness controls restart behavior.

### Requests vs limits?
Requests influence scheduling; limits cap container resource usage.

### PV vs PVC?
PV represents storage; PVC requests storage.

### StatefulSet vs Deployment?
StatefulSet provides stable identity/storage patterns; Deployment is generally used for stateless workloads.

### HPA vs Cluster Autoscaler?
HPA scales Pods; Cluster Autoscaler changes node count.

### RBAC vs IAM?
RBAC controls Kubernetes API permissions; IAM controls AWS permissions.

### What does VPC CNI do?
Provides AWS VPC networking for EKS Pods.

### Why CoreDNS?
Provides Kubernetes DNS and service discovery.

### What is IRSA?
A mechanism allowing a Kubernetes ServiceAccount to use an AWS IAM role.

### What is EKS?
AWS's managed Kubernetes service.

### How do you troubleshoot a Pod?
Check status, describe output, logs, previous logs and events, then inspect configuration, networking, resources and dependencies.

### How do you troubleshoot a Service?
Check Service selector, Pod labels, EndpointSlice, readiness and DNS, then test connectivity from a client Pod.

### How do you troubleshoot EKS networking?
Start with Pod IP/node/subnet, then inspect VPC CNI, routes, Security Groups, NetworkPolicy, NAT and DNS.

### How do you approach an EKS upgrade?
Check compatibility and Upgrade Insights, verify workloads/PDBs/capacity, upgrade control plane, validate add-ons, upgrade nodes separately, then validate and monitor.

---

# 33. Final Engineering Mindset

The objective is not to memorize commands.

The important skill is:

```text
Observe
 ↓
Classify
 ↓
Collect evidence
 ↓
Find root cause
 ↓
Fix safely
 ↓
Verify
 ↓
Prevent recurrence
```

Anything requiring deeper production implementation will be learned during the project phase.
