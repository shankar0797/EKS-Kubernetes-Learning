# Kubernetes Networking --- Notes

## 1. Overview

Kubernetes networking allows Pods, Services, and external clients to
communicate with each other.

In this section we covered:

-   Services
-   ClusterIP
-   NodePort
-   LoadBalancer
-   ExternalName
-   Service Discovery / DNS
-   Endpoints / EndpointSlices
-   kube-proxy
-   Ingress
-   Ingress Controller
-   NetworkPolicy

Lab environment:

-   Kubernetes: Minikube
-   Node: `minikube`
-   Kubernetes version: v1.37.0
-   Pod network: `10.244.0.0/16`
-   Minikube node IP: `192.168.49.2`

------------------------------------------------------------------------

# 2. Kubernetes Service

A Service provides a stable network endpoint for a changing set of Pods.

Pods are temporary:

``` text
Pod A -> 10.244.0.27
Pod B -> 10.244.0.28
Pod C -> 10.244.0.30
```

Pod IPs can change when Pods are recreated.

A Service provides:

``` text
Service
ClusterIP: 10.x.x.x
       |
       +---- Pod A
       +---- Pod B
       +---- Pod C
```

The Service selects Pods using labels.

### Example

Deployment labels:

``` yaml
labels:
  app: services-demo
```

Service:

``` yaml
selector:
  app: services-demo
```

The selector connects the Service to matching Pods.

------------------------------------------------------------------------

# 3. ClusterIP

ClusterIP is the default Service type.

Example:

``` yaml
apiVersion: v1
kind: Service
metadata:
  name: services-demo
spec:
  type: ClusterIP
  selector:
    app: services-demo
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

Flow:

``` text
Client Pod
    |
    | HTTP :80
    v
ClusterIP
    |
    +---- Pod :80
    +---- Pod :80
    +---- Pod :80
```

ClusterIP is normally reachable only from inside the cluster.

Test:

``` bash
kubectl exec service-client -- curl http://services-demo
```

DNS test:

``` bash
kubectl exec service-client -- \
  curl -s http://services-demo.default.svc.cluster.local
```

------------------------------------------------------------------------

# 4. Service Port vs TargetPort vs ContainerPort

This is an important interview topic.

``` text
Service port       = port exposed by the Service
targetPort         = port on the backend Pod
containerPort      = container metadata describing the application port
```

Example:

``` yaml
ports:
  - port: 8080
    targetPort: 80
```

Traffic:

``` text
Client
  |
  | Service :8080
  v
Service
  |
  | forwards to :80
  v
Pod :80
```

`containerPort` does not itself publish the port.

------------------------------------------------------------------------

# 5. Service Selector

The Service finds backend Pods using labels.

Example:

``` yaml
selector:
  app: services-demo
```

If the selector is changed to:

``` yaml
selector:
  app: wrong-app
```

the Service finds no matching Pods.

Result:

``` text
Service
   |
   X
No matching endpoints
```

Useful troubleshooting:

``` bash
kubectl describe svc services-demo
kubectl get pods --show-labels
kubectl get endpoints services-demo
kubectl get endpointslice
```

------------------------------------------------------------------------

# 6. EndpointSlices

EndpointSlices maintain the backend endpoints associated with a Service.

Example:

``` text
Service
  |
  v
EndpointSlice
  |
  +---- 10.244.0.27:80
  +---- 10.244.0.28:80
  +---- 10.244.0.30:80
```

EndpointSlice is important because Pod IPs are dynamic.

When a Pod was deleted in the lab:

``` text
Old Pod -> 10.244.0.26
```

the Deployment created a replacement:

``` text
New Pod -> 10.244.0.30
```

The Service ClusterIP remained stable while the backend Pod IP changed.

------------------------------------------------------------------------

# 7. Readiness and Services

A Pod can be:

``` text
Running != Ready
```

A readiness probe determines whether the Pod should receive traffic.

We created a readiness probe that initially pointed to a non-existent
path:

``` yaml
readinessProbe:
  httpGet:
    path: /does-not-exist
    port: 80
```

The new Pod became NotReady.

EndpointSlice could contain the endpoint with:

``` text
ready: false
serving: false
```

The Service normally sends traffic only to ready endpoints.

Important:

``` text
Container is running
        !=
Application is ready for traffic
```

------------------------------------------------------------------------

# 8. NodePort

NodePort exposes a Service through a port on each Kubernetes node.

Example:

``` yaml
type: NodePort
```

Our NodePort was:

``` text
NodePort: 32580
```

Minikube IP:

``` text
192.168.49.2
```

Test:

``` bash
curl http://192.168.49.2:32580
```

Flow:

``` text
External Client
      |
      | :32580
      v
Kubernetes Node
      |
      v
Service
      |
      v
Pods
```

NodePort range is commonly:

``` text
30000-32767
```

------------------------------------------------------------------------

# 9. LoadBalancer

Example:

``` yaml
type: LoadBalancer
```

In Minikube we saw:

``` text
EXTERNAL-IP: <pending>
```

This is expected because Minikube does not automatically provide a cloud
load balancer like a managed cloud environment.

Minikube provided access through its node/NodePort path:

``` bash
minikube service services-loadbalancer --url
```

Important cloud distinction:

A Kubernetes `Service` of type `LoadBalancer` is not the same thing as
an Ingress.

In AWS environments, LoadBalancer Services and AWS Load Balancer
Controller/Ingress can use different AWS load-balancing mechanisms
depending on configuration.

------------------------------------------------------------------------

# 10. ExternalName

ExternalName is used to map a Kubernetes Service name to an external DNS
hostname.

Example:

``` yaml
apiVersion: v1
kind: Service
metadata:
  name: external-nginx
spec:
  type: ExternalName
  externalName: example.com
```

Characteristics:

-   No normal Pod selector
-   No normal Pod endpoints
-   Uses DNS alias behavior
-   CoreDNS returns the external hostname

Concept:

``` text
Application
    |
    | external-nginx
    v
CoreDNS
    |
    | DNS alias
    v
example.com
```

------------------------------------------------------------------------

# 11. Kubernetes DNS / Service Discovery

Kubernetes provides DNS-based service discovery.

A Service can normally be reached using:

``` text
<service-name>
```

or the fully qualified name:

``` text
<service-name>.<namespace>.svc.cluster.local
```

Example:

``` text
services-demo.default.svc.cluster.local
```

Our DNS server was:

``` text
10.96.0.10
```

which was provided by CoreDNS.

Test:

``` bash
kubectl exec service-client -- nslookup services-demo
```

Non-existent DNS name:

``` bash
kubectl exec service-client -- nslookup does-not-exist
```

returns an NXDOMAIN-style failure.

------------------------------------------------------------------------

# 12. kube-proxy

kube-proxy traditionally implements Service networking on nodes.

Conceptually:

``` text
Service
   |
   v
kube-proxy / networking dataplane
   |
   +---- Pod
   +---- Pod
   +---- Pod
```

It watches Service and EndpointSlice information and programs networking
rules.

Historically this commonly involved:

-   iptables
-   IPVS

Modern Kubernetes environments can also use alternative dataplanes,
including eBPF-based implementations depending on the networking stack.

For this lab, kube-proxy was covered primarily as theory.

------------------------------------------------------------------------

# 13. Ingress

Ingress provides HTTP/HTTPS routing to Services.

Instead of exposing every application individually:

``` text
Client -> Service A
Client -> Service B
Client -> Service C
```

we can use:

``` text
Client
   |
   v
Ingress
   |
   +---- /one  -> Service A
   |
   +---- /two  -> Service B
```

Our Ingress:

``` yaml
spec:
  ingressClassName: nginx
  rules:
    - http:
        paths:
          - path: /one
            pathType: Prefix
            backend:
              service:
                name: ingress-app-one
                port:
                  number: 80

          - path: /two
            pathType: Prefix
            backend:
              service:
                name: ingress-app-two
                port:
                  number: 80
```

------------------------------------------------------------------------

# 14. Ingress Controller

An Ingress resource is only a set of routing rules.

An Ingress Controller implements those rules.

We enabled the Minikube NGINX Ingress Controller:

``` bash
minikube addons enable ingress
```

Architecture:

``` text
Client
  |
  | HTTP
  v
NGINX Ingress Controller
  |
  | Ingress rules
  +-------------------+
  |                   |
  v                   v
Service A          Service B
  |                   |
  v                   v
Pods                Pods
```

Our controller was exposed through NodePort:

``` text
HTTP: 80:31800
HTTPS: 443:32767
```

Test:

``` bash
curl -i http://192.168.49.2:31800/one
curl -i http://192.168.49.2:31800/two
```

------------------------------------------------------------------------

# 15. Ingress Path Routing

Our routes:

``` text
/one -> ingress-app-one
/two -> ingress-app-two
```

We used:

``` yaml
pathType: Prefix
```

This means the path can match prefixes rather than requiring only an
exact URL.

------------------------------------------------------------------------

# 16. Ingress Rewrite

The backend NGINX application served `/`.

But the client requested:

``` text
/one
```

The backend did not have a `/one` resource, so it initially returned
404.

We used:

``` yaml
annotations:
  nginx.ingress.kubernetes.io/rewrite-target: /
```

Now:

``` text
Client request:
/one

        |
        v

Ingress Controller
        |
        | rewrite
        v

Backend request:
/
```

The backend returned its `/` page.

This demonstrates an important distinction:

``` text
Path routing:
Which Service receives the request?

Path rewriting:
What path does the backend application receive?
```

------------------------------------------------------------------------

# 17. Ingress Architecture Used in Lab

Final flow:

``` text
Client
   |
   | :31800
   v
Minikube Node
   |
   v
NGINX Ingress Controller
   |
   | /one
   v
ClusterIP Service
   |
   v
EndpointSlice
   |
   v
Pod
```

For `/two`, the same architecture routes to the second Service.

------------------------------------------------------------------------

# 18. NetworkPolicy

NetworkPolicy controls network traffic to and/or from selected Pods.

Think of it as a firewall policy for Pods.

Important directions:

``` text
Ingress = traffic entering a Pod
Egress  = traffic leaving a Pod
```

NetworkPolicy does not create networking. A network plugin/CNI must
enforce the policy.

------------------------------------------------------------------------

# 19. NetworkPolicy Lab

We created:

``` text
np-web
np-client
np-unauthorized
```

Labels:

``` text
np-web:
  app=np-web

np-client:
  app=np-client

np-unauthorized:
  run=np-unauthorized
```

Policy:

``` yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: np-web-policy
spec:
  podSelector:
    matchLabels:
      app: np-web

  policyTypes:
    - Ingress

  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: np-client

      ports:
        - protocol: TCP
          port: 80
```

Meaning:

``` text
Target:
  app=np-web

Allow:
  app=np-client -> TCP/80
```

------------------------------------------------------------------------

# 20. NetworkPolicy Test Results

Authorized:

``` text
np-client
   |
   | TCP/80
   v
np-web
```

Result:

``` text
nginx response
```

Allowed.

Unauthorized:

``` text
np-unauthorized
   |
   | TCP/80
   v
np-web
```

Result:

``` text
curl exit code 28
```

Exit code 28 indicates a timeout.

Therefore the NetworkPolicy was successfully enforced in the Minikube
environment.

------------------------------------------------------------------------

# 21. Important NetworkPolicy Interview Point

NetworkPolicy works with Pods, not Service names.

A Service may correctly have endpoints:

``` text
Service
   |
   v
EndpointSlice
   |
   v
Pods
```

but NetworkPolicy can still block traffic reaching those Pods.

------------------------------------------------------------------------

# 22. Networking Architecture Summary

A simplified Kubernetes networking model:

``` text
                    Kubernetes Cluster

External Client
      |
      | NodePort / LoadBalancer / Ingress
      v
+-----------------------+
| Service / Ingress     |
+-----------------------+
      |
      v
+-----------------------+
| EndpointSlice         |
+-----------------------+
      |
      v
+-----------------------+
| Pods                  |
| 10.244.x.x            |
+-----------------------+
      |
      | NetworkPolicy
      v
Traffic allowed/blocked
```

DNS provides service discovery:

``` text
Application
     |
     v
CoreDNS
     |
     v
Service ClusterIP
     |
     v
Pods
```

------------------------------------------------------------------------

# 23. Key Interview Questions

### What is a Kubernetes Service?

A stable network abstraction that exposes a set of Pods selected by
labels.

### Why do we need Services?

Pod IPs are dynamic. Services provide a stable endpoint and service
discovery.

### ClusterIP vs NodePort?

ClusterIP is normally internal to the cluster. NodePort exposes the
Service through a port on each node.

### What is targetPort?

The port on the backend Pod/application to which Service traffic is
forwarded.

### What is an EndpointSlice?

A scalable Kubernetes API object that tracks backend endpoints for
Services.

### Running vs Ready?

Running means the container is running. Ready means Kubernetes considers
the Pod ready to receive traffic.

### What is Ingress?

An API resource that defines HTTP/HTTPS routing rules to Services.

### What is an Ingress Controller?

The component that implements and enforces the Ingress rules.

### Ingress vs Service?

Service provides stable access to Pods. Ingress provides HTTP/HTTPS
routing across one or more Services.

### What is NetworkPolicy?

A policy controlling allowed network traffic to and/or from selected
Pods.

### Why might a NetworkPolicy not work?

The cluster's networking plugin/CNI must support and enforce
NetworkPolicy.

------------------------------------------------------------------------

# 24. Commands for Quick Revision

``` bash
kubectl get svc
kubectl describe svc <service>

kubectl get endpoints
kubectl get endpoints <service>

kubectl get endpointslice
kubectl get endpointslice -l kubernetes.io/service-name=<service>

kubectl get pods --show-labels

kubectl get ingress
kubectl describe ingress <name>

kubectl get ingressclass

kubectl get networkpolicy
kubectl describe networkpolicy <name>

kubectl get pods -n kube-system
kubectl get pods -n kube-system -o wide

minikube ip
minikube service <service> --url
```

------------------------------------------------------------------------

# 25. Networking Section Outcome

After completing this section, the following concepts were practically
demonstrated:

-   Stable Service networking
-   Label-based Service selection
-   ClusterIP
-   Service port and targetPort
-   EndpointSlices
-   Readiness and traffic routing
-   NodePort
-   LoadBalancer behavior in Minikube
-   Kubernetes DNS
-   ExternalName
-   kube-proxy theory
-   HTTP path routing with Ingress
-   NGINX Ingress Controller
-   Path rewriting
-   Ingress troubleshooting
-   Pod-level network access control with NetworkPolicy

Networking is now complete and the next learning phase is:

**03 --- Kubernetes Configuration**
