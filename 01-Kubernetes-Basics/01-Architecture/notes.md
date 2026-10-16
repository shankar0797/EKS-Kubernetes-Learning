# Kubernetes Architecture

## 1. What is Kubernetes?

Kubernetes is a container orchestration platform used to deploy, manage, scale, and maintain containerized applications.

It provides:

- Container orchestration
- Self-healing
- Scaling
- Service discovery
- Rolling updates
- Configuration and secret management
- Resource management

---

# 2. Kubernetes Cluster Architecture

A Kubernetes cluster has two major parts:

```text
Kubernetes Cluster
│
├── Control Plane
│
└── Worker Nodes
Control Plane

The Control Plane manages the Kubernetes cluster and maintains the desired state.

Main components:

Control Plane
│
├── API Server
├── etcd
├── Scheduler
└── Controller Manager
3. API Server

The API Server is the main entry point to the Kubernetes cluster.

kubectl communicates with the API Server.

Example:

kubectl get pods

Flow:

kubectl
   ↓
API Server
   ↓
Kubernetes resources

Responsibilities:

Receives API requests
Validates requests
Authenticates/authorizes requests
Reads/writes cluster state through etcd
Acts as the communication hub for Kubernetes components
4. etcd

etcd is the distributed key-value database used by Kubernetes.

It stores cluster state and configuration.

Examples of information stored:

Pods
Deployments
Services
ConfigMaps
Secrets
Cluster configuration
Desired state

Important:

etcd stores Kubernetes state; it does not run containers.

5. Scheduler

The Scheduler decides which worker node should run a newly created Pod.

Example:

New Pod
   ↓
API Server
   ↓
Scheduler
   ↓
Select suitable Worker Node
   ↓
kubelet
   ↓
Container starts

Scheduler considers factors such as:

Available resources
CPU/memory requests
Node selectors
Taints/tolerations
Affinity/anti-affinity
Other scheduling constraints
6. Controller Manager

Controllers continuously compare:

Desired State
      ↓
Actual State

and take action when they differ.

Example:

Deployment wants 3 Pods
        ↓
Only 2 Pods running
        ↓
Controller detects difference
        ↓
Creates another Pod
        ↓
3 Pods running

Controllers provide the reconciliation/self-healing behavior of Kubernetes.

Examples:

Deployment Controller
ReplicaSet Controller
Node Controller
Job Controller
7. Worker Node

Worker nodes are where application workloads run.

Main components:

Worker Node
│
├── kubelet
├── Container Runtime
└── kube-proxy
8. kubelet

kubelet runs on every worker node.

It is responsible for making sure Pods assigned to the node are running correctly.

Responsibilities:

Receives Pod specifications
Communicates with API Server
Starts/stops containers through container runtime
Reports Pod/node status
Performs container health checks
9. Container Runtime

The container runtime actually runs the containers.

Examples include:

containerd
CRI-O

In our Minikube lab:

Kubernetes
    ↓
kubelet
    ↓
containerd
    ↓
Containers
10. kube-proxy

kube-proxy supports Kubernetes Service networking.

It helps implement network rules that allow traffic to reach Service backends.

Conceptually:

Client
   ↓
Service
   ↓
kube-proxy networking rules
   ↓
Pod

Modern Kubernetes networking can use different implementations, but kube-proxy is the traditional/default component to understand for fundamentals.

11. Complete Request Flow

When we run:

kubectl apply -f deployment.yaml

Conceptually:

kubectl
   ↓
API Server
   ↓
etcd
   ↓
Deployment Controller
   ↓
ReplicaSet
   ↓
Scheduler
   ↓
Worker Node
   ↓
kubelet
   ↓
Container Runtime
   ↓
Container
12. Desired State vs Actual State

This is one of the most important Kubernetes concepts.

Example:

replicas: 3

This represents the desired state.

If only two Pods are running:

Desired State = 3
Actual State  = 2

Kubernetes reconciles the difference:

Desired = 3
Actual  = 2
       ↓
Controller creates Pod
       ↓
Desired = 3
Actual  = 3
13. Our Minikube Lab Architecture

Our lab uses a single-node Minikube cluster.

EC2
│
└── Minikube
     │
     ├── Control Plane
     │
     └── Worker workload

Because this is a single-node lab, the control-plane and worker workload run on the same Minikube node.

Useful commands:

minikube status
kubectl get nodes
kubectl cluster-info
kubectl get pods -A
14. Important Commands

Check cluster:

kubectl cluster-info
kubectl get nodes
kubectl get nodes -o wide

Check all system Pods:

kubectl get pods -A

Describe a node:

kubectl describe node <node-name>

Check Minikube:

minikube status
minikube version
15. Interview Quick Answers
What is Kubernetes?

A container orchestration platform used to deploy, manage, scale, and maintain containerized applications.

What is the API Server?

The central API endpoint through which Kubernetes components and clients communicate with the cluster.

What is etcd?

A distributed key-value store that maintains Kubernetes cluster state and configuration.

What does the Scheduler do?

It selects a suitable worker node for newly created Pods based on scheduling constraints and available resources.

What does kubelet do?

It runs on worker nodes and ensures that the Pods assigned to the node are running according to their specification.

What is Controller Manager?

It runs controllers that continuously reconcile desired state with actual state.

What is container runtime?

The component responsible for actually running containers, such as containerd or CRI-O.

What is kube-proxy?

A node-level networking component traditionally responsible for implementing Kubernetes Service traffic rules.

16. One-Minute Architecture Explanation

"A Kubernetes cluster consists of a Control Plane and Worker Nodes. The API Server is the entry point for Kubernetes operations. etcd stores cluster state, the Scheduler assigns Pods to suitable nodes, and Controllers continuously reconcile the desired and actual state. On worker nodes, kubelet manages Pods and communicates with the container runtime, while kube-proxy supports Service networking. Kubernetes follows a desired-state model, where controllers continuously work to make the actual environment match the declared configuration."
# 17. Questions & Answers

### Q1. What is Kubernetes?
Kubernetes is a container orchestration platform used to deploy, manage, scale, and maintain containerized applications.

### Q2. What are the main components of the Control Plane?
- API Server
- etcd
- Scheduler
- Controller Manager

### Q3. What are the main components of a Worker Node?
- kubelet
- Container Runtime
- kube-proxy

### Q4. What happens when you run `kubectl get pods`?

```text
kubectl
   ↓
API Server
   ↓
API Server reads cluster state
   ↓
Pod information returned
   ↓
kubectl displays result
Q5. What happens when you run kubectl apply -f deployment.yaml?
kubectl
   ↓
API Server
   ↓
Deployment stored/updated
   ↓
Deployment Controller
   ↓
ReplicaSet
   ↓
Scheduler
   ↓
kubelet
   ↓
Container Runtime
   ↓
Pod
Q6. Why is etcd important?

etcd stores Kubernetes cluster state. If etcd loses the required cluster state, Kubernetes cannot correctly maintain the desired configuration.

Q7. Does etcd run containers?

No.

etcd stores Kubernetes state. The container runtime runs containers.

Q8. Does the Scheduler start containers?

No.

The Scheduler selects the node where a Pod should run. kubelet on that node works with the container runtime to start the container.

Q9. What is the difference between Scheduler and kubelet?
Scheduler	kubelet
Selects node	Runs/manages Pods on node
Control Plane	Worker Node
Decides placement	Ensures workload runs
Q10. What is the difference between Controller Manager and Scheduler?

Scheduler: decides where a new Pod should run.

Controllers: continuously reconcile desired state and actual state.

Q11. What is desired state?

The state declared by the user/application configuration.

Example:

replicas: 3

Desired state = 3 Pods.

Q12. What is reconciliation?

Kubernetes continuously compares desired state with actual state and takes corrective action.

Desired = 3
Actual = 2
     ↓
Controller creates Pod
     ↓
Desired = 3
Actual = 3
Q13. What happens if a Pod is deleted?

If the Pod is managed by a ReplicaSet/Deployment:

Pod deleted
    ↓
Controller detects difference
    ↓
Replacement Pod created

A standalone Pod does not have this controller-based self-healing.

Q14. What happens if a worker node goes down?

The Control Plane detects that the node is unavailable. Kubernetes can reschedule managed workloads onto available nodes, depending on workload/controller configuration and timing.

Q15. What is kubelet?

kubelet is the node agent responsible for ensuring that Pods assigned to its node are running correctly.

Q16. What is a container runtime?

The software that actually starts and manages containers.

Examples:

containerd
CRI-O
Q17. What is kube-proxy?

kube-proxy is traditionally responsible for implementing networking rules used by Kubernetes Services.

Q18. Can a Kubernetes cluster have multiple Control Plane nodes?

Yes. Production clusters commonly use multiple Control Plane nodes for high availability.

Q19. Can one worker node run multiple Pods?

Yes.

A worker node can run many Pods, subject to available resources and scheduling constraints.

Q20. Why shouldn't applications depend on Pod IPs?

Pod IPs are ephemeral.

Pods can be recreated and receive different IP addresses.

Services provide stable application access.

Q21. What is the difference between Kubernetes and Docker?

Docker/container runtimes run containers.

Kubernetes orchestrates containerized workloads across a cluster.

Q22. Does Kubernetes require Docker?

No.

Kubernetes uses a CRI-compatible container runtime such as containerd or CRI-O.

Q23. What is self-healing in Kubernetes?

Kubernetes controllers automatically work to restore the desired state.

Example:

Deployment wants 3 Pods
        ↓
1 Pod crashes
        ↓
Only 2 healthy Pods
        ↓
Controller creates replacement
        ↓
3 Pods restored
Q24. What is the role of the API Server?

It provides the Kubernetes API and acts as the main communication endpoint between users and cluster components.

Q25. What is the most important Kubernetes architecture concept?

Kubernetes is based on declarative desired state and continuous reconciliation.

18. Problems We Faced During the Lab
Problem 1 — Minikube was stopped

We checked:

minikube status

The cluster was not running.

Resolution
minikube start

Then:

kubectl get nodes

Verified the node became Ready.

Learning

Always check cluster/node health before troubleshooting individual workloads.

Problem 2 — Understanding Control Plane vs Worker

Our Minikube environment is a single-node cluster.

Conceptually:

Minikube Node
├── Control Plane components
└── Workload execution
Learning

A single-node Minikube setup is excellent for learning but is not equivalent to a production multi-node EKS cluster.

Problem 3 — ImagePullBackOff during Pod lab

We intentionally used an invalid image.

Observed:

ErrImagePull
ImagePullBackOff
Troubleshooting
kubectl describe pod <pod>

Events showed the image could not be pulled.

Root Cause

Invalid/nonexistent container image.

Learning

For image problems, kubectl describe pod and Events are usually more useful than application logs because the container may never have started.

Problem 4 — Understanding Pod self-healing

We deleted a Pod managed by a ReplicaSet.

Observed:

Pod deleted
    ↓
ReplicaSet detected missing replica
    ↓
Replacement Pod created
Learning

Self-healing comes from controllers such as ReplicaSet/Deployment, not from the Pod itself.

Problem 5 — Failed Deployment rollout

We intentionally deployed a nonexistent Nginx image.

The Deployment created a new ReplicaSet, but the new Pods could not start.

Troubleshooting
kubectl rollout status deployment <name>
kubectl get rs
kubectl get pods
kubectl describe pod <pod>
Learning

Deployment troubleshooting should follow:

Deployment
   ↓
ReplicaSet
   ↓
Pod
   ↓
Events
19. Architecture Troubleshooting Checklist

When a Kubernetes environment has a problem:

Cluster level
kubectl cluster-info
kubectl get nodes
kubectl get nodes -o wide
Node level
kubectl describe node <node>

Check:

Ready condition
MemoryPressure
DiskPressure
PIDPressure
Events
Workload level
kubectl get pods -A
kubectl describe pod <pod>
kubectl logs <pod>
Event level
kubectl get events --sort-by=.lastTimestamp
Minikube level
minikube status
20. Production Incident Flow
Application issue
       ↓
Is cluster healthy?
       ↓
kubectl get nodes
       ↓
Is node healthy?
       ↓
kubectl describe node
       ↓
Is Pod healthy?
       ↓
kubectl get pods
       ↓
Describe Pod
       ↓
Check Events
       ↓
Check Logs
       ↓
Check configuration/resources/network
       ↓
Identify root cause
       ↓
Fix
       ↓
Verify
21. Architecture Interview Scenario
Scenario

A developer says:

"My Deployment YAML is correct, but the Pod isn't running. What do you check?"

Answer:

"I wouldn't assume the YAML is the problem. I would first check the Pod status with kubectl get pods, then use kubectl describe pod to inspect its state and Events. I would check whether the node is Ready, whether the Pod was scheduled, whether the image can be pulled, whether there are resource constraints, and whether the container has actually started. If it started, I would check the application logs. I would use the evidence to identify whether the issue is scheduling, node health, image, configuration, resources, or application related."

22. Architecture Interview Scenario — High CPU
Scenario

A production Kubernetes node has high CPU.

First checks:

kubectl top nodes
kubectl top pods -A
kubectl get nodes

Then investigate:

Which Pod consumes CPU?
Which namespace?
Does the Deployment have appropriate resource requests/limits?
Is HPA configured?
Is there unusual traffic?
Is the application stuck in a CPU-intensive loop?

Do not immediately restart the Pod without understanding the cause.

23. Architecture Interview Scenario — Node NotReady
kubectl get nodes

If:

minikube   NotReady

then:

kubectl describe node minikube

Check Conditions and Events.

Potential causes:

kubelet failure
container runtime failure
memory pressure
disk pressure
network issue
node resource exhaustion

For an actual EC2/EKS environment, also investigate the underlying EC2 instance and node services.

24. Quick Architecture Memory Map
                 CONTROL PLANE
                      │
        ┌─────────────┼─────────────┐
        │             │             │
    API Server    Scheduler    Controllers
        │                           │
        │                           │
       etcd                  Desired vs Actual
        │                           │
        └─────────────┬─────────────┘
                      │
                      ↓
                 WORKER NODE
                      │
             ┌────────┼────────┐
             │        │        │
          kubelet  Runtime  kube-proxy
             │        │
             └────┬───┘
                  ↓
                 Pods
Remember
API Server  → communication
etcd        → state
Scheduler   → placement
Controllers → reconciliation
kubelet     → node agent
Runtime     → containers
kube-proxy  → Service networking


