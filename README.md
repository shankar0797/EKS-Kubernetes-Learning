# EKS & Kubernetes Production Learning

Hands-on Kubernetes and Amazon EKS learning path focused on
production troubleshooting, DevOps practices, and interview preparation.

## Learning Approach

Each topic follows:

1. Concept
2. Architecture
3. Why it is used
4. Hands-on implementation
5. Verification
6. Intentional failure
7. Troubleshooting
8. Root cause analysis
9. Fix
10. Verification
11. Documentation
12. Interview scenario

## Environment

- AWS EC2
- Amazon Linux 2023
- Kubernetes
- Minikube
- Docker
- containerd
- kubectl

## Topics

### Kubernetes Fundamentals

- Architecture
- Pods
- ReplicaSets
- Deployments
- Services
- Namespaces
- ConfigMaps
- Secrets
- Rolling Updates
- Rollbacks
- Resource Requests & Limits

### Advanced Kubernetes

- Probes
- Storage
- Ingress
- Networking
- RBAC
- Network Policies
- Autoscaling
- Monitoring
- Logging

### Amazon EKS

- EKS Architecture
- VPC CNI
- EKS IAM
- Pod Identity
- IRSA
- EKS Networking
- EBS CSI
- Load Balancers
- Autoscaling
- Karpenter
- CloudWatch
- Prometheus
- Grafana

### Production Troubleshooting

- ImagePullBackOff
- CrashLoopBackOff
- Pending Pods
- Service without Endpoints
- DNS failures
- Readiness failures
- Liveness failures
- Node NotReady
- CPU/Memory pressure
- Storage failures
- ECR authentication
- ALB 5xx errors
- IAM permission issues

## Current Progress

- [x] Kubernetes cluster created
- [x] kubectl configured
- [x] Cluster architecture inspected
- [x] First Pod deployed
- [x] ImagePullBackOff troubleshooting
- [x] Application health verified
- [ ] Deployment
- [ ] ReplicaSet
- [ ] Service
- [ ] ConfigMap
- [ ] Secret
