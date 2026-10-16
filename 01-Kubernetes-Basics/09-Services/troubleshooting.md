# Kubernetes Networking --- Troubleshooting

This file contains the main networking problems encountered during the
lab and the troubleshooting approach used.

------------------------------------------------------------------------

# 1. Service Has No Endpoints

## Problem

A Service exists, but traffic does not reach any Pods.

## Symptoms

``` bash
kubectl get svc
kubectl get endpoints <service>
```

Endpoints are empty.

## Troubleshooting

Check Service selector:

``` bash
kubectl describe svc <service>
```

Check Pod labels:

``` bash
kubectl get pods --show-labels
```

Compare:

``` text
Service selector
        vs
Pod labels
```

## Root Cause

During the lab, the Service selector was intentionally changed from:

``` yaml
selector:
  app: services-demo
```

to:

``` yaml
selector:
  app: wrong-app
```

No Pods matched the selector.

## Resolution

Restore:

``` yaml
selector:
  app: services-demo
```

Apply:

``` bash
kubectl apply -f service.yaml
```

Verify:

``` bash
kubectl get endpoints services-demo
```

------------------------------------------------------------------------

# 2. Pod Running but Not Ready

## Problem

A Pod is Running but should not receive application traffic.

## Example

The readiness probe was configured as:

``` yaml
readinessProbe:
  httpGet:
    path: /does-not-exist
    port: 80
```

## Symptoms

Pod can be Running but NotReady.

EndpointSlice can show:

``` text
ready: false
serving: false
```

## Root Cause

The readiness probe failed because the application did not serve the
requested path.

## Resolution

Change the probe to a valid application endpoint, for example:

``` yaml
readinessProbe:
  httpGet:
    path: /
    port: 80
```

Apply the Deployment and wait for readiness.

## Key Lesson

``` text
Running != Ready
```

------------------------------------------------------------------------

# 3. NodePort Not Reachable on Port 80

## Problem

The NodePort Service was created, but accessing the node IP on port 80
did not work.

## Root Cause

The Service was exposed on the assigned NodePort:

``` text
32580
```

not directly on port 80 of the Minikube node.

## Resolution

Find the NodePort:

``` bash
kubectl get svc services-nodeport
```

Test:

``` bash
curl http://192.168.49.2:32580
```

or:

``` bash
minikube service services-nodeport --url
```

------------------------------------------------------------------------

# 4. LoadBalancer Shows EXTERNAL-IP `<pending>`{=html}

## Problem

The LoadBalancer Service showed:

``` text
EXTERNAL-IP   <pending>
```

## Explanation

This was a Minikube environment, not a managed cloud environment with an
automatically provisioned external load balancer.

## Test

``` bash
minikube service services-loadbalancer --url
```

The Service could still be tested through Minikube's exposed path.

## Interview Point

Do not assume every Kubernetes LoadBalancer Service immediately creates
a cloud load balancer. The actual behavior depends on the Kubernetes
environment and cloud integration.

------------------------------------------------------------------------

# 5. DNS Service Resolution Failure

## Problem

A Service name could not be resolved.

## Troubleshooting

Test:

``` bash
kubectl exec service-client -- nslookup services-demo
```

Test a known invalid name:

``` bash
kubectl exec service-client -- nslookup does-not-exist
```

Check CoreDNS:

``` bash
kubectl get pods -n kube-system
```

## Key Components

``` text
Application
   |
   v
CoreDNS
   |
   v
Service DNS record
```

------------------------------------------------------------------------

# 6. Ingress Returns 404

## Problem

Request:

``` bash
curl -i http://192.168.49.2:31800/one
```

initially returned 404.

## Investigation

The Ingress Controller was receiving the request and routing toward the
backend.

Direct backend testing showed:

``` text
/      -> 200
/one   -> 404
```

The backend NGINX application served `/`, not `/one`.

## Root Cause

The Ingress route and backend application path did not match.

## Resolution

Added:

``` yaml
annotations:
  nginx.ingress.kubernetes.io/rewrite-target: /
```

Now:

``` text
Client:
  /one

Ingress:
  /one -> /one route
  rewrite /one -> /

Backend:
  /
```

The backend returned HTTP 200.

## Key Lesson

A 404 can come from different layers.

Always determine whether it is:

``` text
Ingress/default backend 404
        OR
Backend application 404
```

------------------------------------------------------------------------

# 7. Ingress References a Non-Existent Service

## Problem

The `/one` route was temporarily changed to:

``` text
ingress-app-xyz
```

but that Service did not exist.

## Symptoms

``` bash
kubectl describe ingress ingress-demo
```

showed an error similar to:

``` text
services "ingress-app-xyz" not found
```

Controller logs reported that the Service object could not be found.

Request:

``` bash
curl -i http://192.168.49.2:31800/one
```

returned:

``` text
503 Service Unavailable
```

while `/two` continued working.

## Root Cause

Ingress backend referenced a Service name that did not exist.

## Resolution

Restore:

``` yaml
service:
  name: ingress-app-one
```

Apply:

``` bash
kubectl apply -f ingress.yaml
```

Verify:

``` bash
kubectl describe ingress ingress-demo
kubectl get svc
```

------------------------------------------------------------------------

# 8. Ingress Troubleshooting --- Remaining Scenarios

These scenarios were reviewed conceptually rather than all being
deliberately broken during the lab.

## Wrong Service Port

Problem:

Ingress references a Service port that does not exist.

Check:

``` bash
kubectl describe ingress <name>
kubectl get svc <service>
kubectl describe svc <service>
```

Difference:

``` text
Wrong Service Name:
Service object does not exist

Wrong Service Port:
Service exists, but referenced port is invalid
```

------------------------------------------------------------------------

## No Service Endpoints

Check:

``` bash
kubectl get endpoints <service>
kubectl get endpointslice
kubectl get pods --show-labels
```

Likely causes:

-   Wrong selector
-   Wrong Pod labels
-   Pods not Ready
-   Deployment problem

------------------------------------------------------------------------

## Pod Not Ready

Check:

``` bash
kubectl get pods
kubectl describe pod <pod>
```

Inspect:

``` text
Readiness probe
Pod conditions
Events
```

A Pod can exist as an endpoint but not be considered ready for serving
traffic.

------------------------------------------------------------------------

## Wrong IngressClass

Check:

``` bash
kubectl get ingressclass
kubectl describe ingress <name>
```

Confirm:

``` yaml
ingressClassName: nginx
```

and that the intended controller manages that class.

------------------------------------------------------------------------

## Unmatched Path

Example:

``` text
/unknown
```

does not match:

``` text
/one
/two
```

The request may be handled by the Ingress Controller's default backend
behavior and return 404.

------------------------------------------------------------------------

## Host/Header Mismatch

If the Ingress contains:

``` yaml
host: app.example.com
```

the request must normally include:

``` http
Host: app.example.com
```

Test:

``` bash
curl -H "Host: app.example.com" http://<ingress-address>
```

Without the expected Host header, the rule may not match.

------------------------------------------------------------------------

## TLS/HTTPS Problem

Troubleshooting commands:

``` bash
kubectl describe ingress <name>
kubectl get secret
kubectl describe secret <tls-secret>
```

Check:

-   TLS Secret exists
-   Secret is in the correct namespace
-   Certificate/key are valid
-   Ingress references the correct Secret

------------------------------------------------------------------------

# 9. NetworkPolicy --- Unauthorized Traffic

## Problem

`np-web` should accept traffic from `np-client`, but not from an
unauthorized Pod.

Policy:

``` yaml
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

## Authorized Test

``` bash
kubectl exec np-client -- \
  curl -s --max-time 5 http://10.244.0.33
```

Result:

``` text
nginx response
```

Allowed.

## Unauthorized Test

Unauthorized Pod label:

``` text
run=np-unauthorized
```

It does not match:

``` text
app=np-client
```

Test:

``` bash
kubectl exec np-unauthorized -- \
  curl -s --max-time 5 http://10.244.0.33
```

Result:

``` text
command terminated with exit code 28
```

Exit code 28 indicates a timeout.

## Root Cause

NetworkPolicy only allowed ingress from Pods matching:

``` text
app=np-client
```

The unauthorized Pod did not match the selector.

## Resolution

No resolution was needed --- the block was the intended behavior.

------------------------------------------------------------------------

# 10. Important NetworkPolicy Troubleshooting Commands

``` bash
kubectl get networkpolicy
kubectl describe networkpolicy <name>

kubectl get pods --show-labels

kubectl get pod <pod> -o wide

kubectl get endpoints <service>
kubectl get endpointslice

kubectl get pods -n kube-system
kubectl get ds -n kube-system
```

When NetworkPolicy appears not to work, first verify:

1.  Policy selects the intended Pods.
2.  Source selector matches the intended client.
3.  Correct port/protocol is specified.
4.  Pod IP is correct.
5.  Pods are Running.
6.  The cluster networking plugin supports/enforces NetworkPolicy.

------------------------------------------------------------------------

# 11. Practical Troubleshooting Flow

For Service problems:

``` text
Client
  |
  v
Service
  |
  +--> Is Service present?
  |
  +--> Is selector correct?
  |
  +--> Are endpoints present?
  |
  +--> Are Pods Ready?
  |
  +--> Is targetPort correct?
  |
  v
Application
```

For Ingress problems:

``` text
Client
  |
  v
Ingress Controller
  |
  +--> Is controller running?
  |
  +--> Is IngressClass correct?
  |
  +--> Does path/host match?
  |
  +--> Does Service exist?
  |
  +--> Does Service port exist?
  |
  +--> Are endpoints available?
  |
  v
Application
```

For NetworkPolicy problems:

``` text
Source Pod
  |
  v
NetworkPolicy
  |
  +--> Does policy select destination?
  |
  +--> Does source match allowed selector?
  |
  +--> Is port allowed?
  |
  +--> Does CNI enforce NetworkPolicy?
  |
  v
Destination Pod
```

------------------------------------------------------------------------

# 12. Interview Summary

When troubleshooting Kubernetes networking, do not immediately assume
the problem is the network.

Work layer by layer:

``` text
DNS
 ↓
Service
 ↓
Selector
 ↓
EndpointSlice
 ↓
Pod readiness
 ↓
Target port
 ↓
Application
 ↓
Ingress
 ↓
NetworkPolicy
```

The most useful commands are:

``` bash
kubectl get svc
kubectl describe svc <name>
kubectl get endpoints
kubectl get endpointslice
kubectl get pods --show-labels
kubectl describe pod <name>
kubectl get ingress
kubectl describe ingress <name>
kubectl get networkpolicy
kubectl describe networkpolicy <name>
kubectl get events
```

The key principle is:

> Troubleshoot Kubernetes networking from the client-facing layer toward
> the backend, verifying each hop instead of guessing.
