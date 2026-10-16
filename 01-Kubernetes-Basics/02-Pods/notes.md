# Kubernetes Pods — Notes

## 1. What is a Pod?

A Pod is the smallest deployable unit in Kubernetes.

A Pod usually contains one application container, but it can contain multiple tightly coupled containers.

```text
Pod
│
├── Application Container
│
└── Optional Sidecar Container

Containers inside the same Pod share:

Network namespace
Pod IP
localhost
Volumes
2. Why does Kubernetes use Pods?

Kubernetes doesn't directly manage individual containers as its basic scheduling unit.

Instead:

Kubernetes
    ↓
Pod
    ↓
Container(s)

The Pod provides a common execution environment for one or more containers.

3. Pod Lifecycle

A simplified lifecycle:

Pod created
    ↓
Pending
    ↓
ContainerCreating
    ↓
Running
    ↓
Succeeded / Failed

A Pod can also remain:

Running

while its container is unhealthy or repeatedly restarting.

Therefore, always check the container state and readiness.

4. Create a Pod

Example:

apiVersion: v1
kind: Pod

metadata:
  name: nginx-pod

spec:
  containers:
    - name: nginx
      image: nginx:1.29
      ports:
        - containerPort: 80

Create:

kubectl apply -f nginx-pod.yaml
5. Check Pods
kubectl get pods

More details:

kubectl get pods -o wide

Example:

NAME         READY   STATUS    RESTARTS   AGE
nginx-pod    1/1     Running   0          1m

Meaning:

READY     = containers Ready / total containers
STATUS    = Pod phase/status
RESTARTS  = container restart count
AGE       = Pod age
6. Get Detailed Pod Information
kubectl describe pod nginx-pod

Important sections:

Node
IP
Containers
Image
Command
State
Last State
Restart Count
Conditions
Volumes
Events

The Events section is especially useful for troubleshooting.

7. Pod IP

Check:

kubectl get pod nginx-pod -o wide

Example:

IP           NODE
10.244.0.10   minikube

Pod IPs are generally ephemeral.

If the Pod is recreated, it may receive a different IP.

Therefore applications should generally use a Kubernetes Service rather than relying on a Pod IP.

8. Access a Pod

Run a shell:

kubectl exec -it nginx-pod -- /bin/sh

Inside:

hostname

Check local HTTP service:

wget -qO- http://localhost

Exit:

exit
9. View Logs
kubectl logs nginx-pod

For a specific container in a multi-container Pod:

kubectl logs nginx-pod -c <container-name>

For the previous container instance:

kubectl logs nginx-pod --previous

--previous is useful when a container restarted and the current instance doesn't contain the logs you need.

10. Delete a Pod
kubectl delete pod nginx-pod

Important:

A standalone Pod will not automatically recreate itself.

Standalone Pod
     ↓
Delete
     ↓
Pod gone

A Deployment/ReplicaSet provides controller-based self-healing.

11. Pod vs Container

A Pod is not the same thing as a container.

Pod
│
├── Container A
└── Container B

The Pod provides the shared environment.

The container runs the application process.

12. Pod Networking

Each Pod normally receives its own IP.

Containers in the same Pod can communicate using:

localhost

Example:

Container A
    |
 localhost
    |
Container B

They share the Pod network namespace.

13. Pod Labels

Labels identify and categorize Kubernetes resources.

Example:

metadata:
  labels:
    app: nginx
    environment: dev

Query:

kubectl get pods -l app=nginx

Show labels:

kubectl get pods --show-labels

Labels become especially important for:

ReplicaSets
Deployments
Services
NetworkPolicies
14. Pod Restart vs Pod Recreation

These are different.

Container restart

Same Pod:

Pod
 ↓
Container crashes
 ↓
Container restarted
 ↓
Same Pod

Restart count increases.

Pod recreation
Old Pod
   ↓
Deleted
   ↓
New Pod

New Pod can have:

New name
New IP
New container ID
15. Important Pod Statuses
Status	Meaning
Pending	Pod has not completed scheduling/startup
ContainerCreating	Container setup is in progress
Running	Pod has running containers
Succeeded	Containers completed successfully
Failed	Containers terminated unsuccessfully
CrashLoopBackOff	Container repeatedly crashes and Kubernetes backs off restarts
ImagePullBackOff	Kubernetes cannot pull the image

Always use:

kubectl describe pod <pod>

to determine the actual reason.

16. Pod Troubleshooting Flow
kubectl get pods
       ↓
Check STATUS
       ↓
kubectl describe pod
       ↓
Check State / Last State
       ↓
Check Events
       ↓
kubectl logs
       ↓
kubectl exec
       ↓
Check configuration
       ↓
Root cause
       ↓
Fix
       ↓
Verify
17. Important Commands
kubectl get pods

kubectl get pods -o wide

kubectl get pods --show-labels

kubectl describe pod <pod>

kubectl logs <pod>

kubectl logs <pod> --previous

kubectl logs <pod> -c <container>

kubectl exec -it <pod> -- /bin/sh

kubectl delete pod <pod>

kubectl get pod <pod> -o yaml

kubectl get pod <pod> -o json
18. Interview Q&A
Q1. What is a Pod?

A Pod is the smallest deployable unit in Kubernetes and provides the execution environment for one or more containers.

Q2. Can a Pod contain multiple containers?

Yes. Containers in the same Pod share networking and can share volumes.

Q3. Why are multiple containers placed in one Pod?

When containers are tightly coupled and need to share lifecycle, network, or storage.

A common example is an application container with a sidecar.

Q4. Do containers in the same Pod have different IP addresses?

Normally no. Containers in the same Pod share the Pod's network namespace and IP.

Q5. How do containers in the same Pod communicate?

Using localhost and the appropriate container port.

Q6. Are Pod IPs permanent?

No. Pod IPs are generally ephemeral.

Q7. How do you check a Pod's IP?
kubectl get pod <pod> -o wide
Q8. How do you troubleshoot a Pod that isn't running?
kubectl get pod <pod>
kubectl describe pod <pod>
kubectl logs <pod>

Then inspect Events and container state.

Q9. What is the difference between kubectl logs and kubectl describe?

kubectl logs shows application/container output.

kubectl describe shows Kubernetes resource state, configuration, conditions, and Events.

Q10. When would you use kubectl logs --previous?

When the container restarted and you need logs from the previous container instance.

Q11. What happens when a standalone Pod is deleted?

It is permanently removed unless another controller is responsible for recreating it.

Q12. What happens when a Deployment-managed Pod is deleted?

The Deployment/ReplicaSet detects the missing replica and creates a replacement Pod.

Q13. What does 1/1 mean?

One container is Ready out of one container in the Pod.

Q14. What does 0/1 Running mean?

The container is running, but it is not currently Ready.

A readiness probe failure is one possible reason.

Q15. What does Restart Count mean?

It shows how many times a container inside the Pod has been restarted.

Q16. Does restarting a container create a new Pod?

No.

The container restarts inside the same Pod.

Q17. How can you enter a running Pod?
kubectl exec -it <pod> -- /bin/sh
Q18. What is the difference between Pod deletion and container restart?

Pod deletion removes the Pod object and its containers.

Container restart keeps the same Pod but restarts the container process.

Q19. Why shouldn't applications use Pod IPs directly?

Because Pod IPs can change when Pods are recreated. Kubernetes Services provide stable access.

Q20. What is the first command you normally run when troubleshooting Pods?

Usually:

kubectl get pods

Then:

kubectl describe pod <pod>

and logs when applicable.
