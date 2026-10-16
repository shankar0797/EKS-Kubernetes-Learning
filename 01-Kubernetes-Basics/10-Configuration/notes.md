# Kubernetes Configuration --- Notes

## 1. Overview

Kubernetes Configuration keeps application configuration outside the
container image.

Topics covered: - ConfigMaps - Environment-variable injection -
Individual-key injection - ConfigMap volume/file mounts - ConfigMap
update behavior - Secrets - `stringData` - `data` and Base64 - Secret
environment-variable injection - Individual Secret-key injection -
Combined ConfigMap + Secret configuration

------------------------------------------------------------------------

## 2. Why Externalize Configuration?

Use the same application image across environments while changing
configuration at runtime.

``` text
Same Docker image
      |
      +-- DEV configuration
      +-- TEST configuration
      +-- PROD configuration
```

This avoids rebuilding the application image for every environment.

------------------------------------------------------------------------

# 3. ConfigMap

A ConfigMap stores **non-sensitive** application configuration.

Example:

``` yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: production
  LOG_LEVEL: info
  APP_PORT: "8080"
```

Typical values: - Application environment - Log level - Ports - Feature
flags - Non-sensitive URLs/settings

Do not use ConfigMaps for passwords or credentials.

------------------------------------------------------------------------

# 4. Create and Inspect

``` bash
kubectl apply -f configmap.yaml
kubectl get configmap
kubectl describe configmap app-config
```

------------------------------------------------------------------------

# 5. ConfigMap → Environment Variables

We used:

``` yaml
envFrom:
  - configMapRef:
      name: app-config
```

Result:

``` text
ConfigMap
APP_ENV=production
APP_PORT=8080
LOG_LEVEL=info
       |
       v
Container environment
```

Verify:

``` bash
kubectl exec configmap-demo --   env | grep -E 'APP_ENV|LOG_LEVEL|APP_PORT'
```

------------------------------------------------------------------------

# 6. Individual ConfigMap Key

``` yaml
env:
  - name: ENVIRONMENT
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: APP_ENV
```

This maps:

``` text
APP_ENV=production
        ↓
ENVIRONMENT=production
```

------------------------------------------------------------------------

# 7. ConfigMap as a Volume

ConfigMaps can be mounted as files:

``` yaml
volumeMounts:
  - name: config-volume
    mountPath: /etc/app-config

volumes:
  - name: config-volume
    configMap:
      name: app-config
```

Inspect:

``` bash
kubectl exec configmap-volume-demo -- ls -l /etc/app-config
kubectl exec configmap-volume-demo -- cat /etc/app-config/application.properties
```

------------------------------------------------------------------------

# 8. ConfigMap Update Behavior

We tested:

``` text
Initial ConfigMap:
APP_ENV=development
```

Running Pod:

``` text
APP_ENV=development
```

After updating the ConfigMap:

``` text
APP_ENV=production
```

the existing container still showed:

``` text
APP_ENV=development
```

because environment variables are populated when the container starts.

After recreating the Pod, it received:

``` text
APP_ENV=production
```

Interview answer:

> Updating a ConfigMap does not update environment variables inside an
> already-running container. The container needs to restart/recreate to
> receive the new environment-variable value.

Mounted ConfigMap files behave differently: Kubernetes can update the
mounted files after a ConfigMap changes, although the application must
reread/reload the file.

------------------------------------------------------------------------

# 9. Secrets

Secrets are intended for sensitive configuration such as:

``` text
DB_USERNAME
DB_PASSWORD
API_TOKEN
TLS private keys
```

Example:

``` yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
stringData:
  DB_USERNAME: appuser
  DB_PASSWORD: MyPassword123
  API_TOKEN: abc123-secret-token
```

Verify:

``` bash
kubectl get secret
kubectl describe secret app-secret
```

------------------------------------------------------------------------

# 10. `stringData` vs `data`

With `stringData`, write plaintext values:

``` yaml
stringData:
  DB_USERNAME: appuser
```

With `data`, provide Base64-encoded values:

``` yaml
data:
  DB_USERNAME: YXBwdXNlcg==
```

**Base64 is encoding, not encryption.**

Lab verification:

``` bash
echo 'TXlQYXNzd29yZDEyMw==' | base64 -d
```

------------------------------------------------------------------------

# 11. Secret → Environment Variables

``` yaml
envFrom:
  - secretRef:
      name: app-secret
```

Verify:

``` bash
kubectl exec secret-demo --   env | grep -E 'DB_USERNAME|DB_PASSWORD|API_TOKEN'
```

The lab produced:

``` text
DB_USERNAME=appuser
API_TOKEN=abc123-secret-token
DB_PASSWORD=MyPassword123
```

------------------------------------------------------------------------

# 12. Individual Secret Key

``` yaml
env:
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: app-secret
        key: DB_PASSWORD
```

This maps:

``` text
DB_PASSWORD
     ↓
DATABASE_PASSWORD
```

------------------------------------------------------------------------

# 13. Combined ConfigMap + Secret Injection

The final demo consumed both:

``` yaml
envFrom:
  - configMapRef:
      name: app-config
  - secretRef:
      name: app-secret

env:
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: app-secret
        key: DB_PASSWORD
```

Verified values:

``` text
APP_ENV=production
APP_PORT=8080
LOG_LEVEL=info
DB_USERNAME=appuser
API_TOKEN=abc123-secret-token
DATABASE_PASSWORD=MyPassword123
```

Architecture:

``` text
ConfigMap ─────┐
               ├──> Pod ───> Application
Secret ────────┘
```

------------------------------------------------------------------------

# 14. Security Considerations

A Kubernetes Secret should not be treated as automatically encrypted
merely because it is called a Secret.

Important controls include:

-   RBAC
-   Encryption at rest
-   Restricted Secret access
-   External secret-management systems
-   Avoiding credentials in Git
-   Avoiding credentials in logs

Also remember that once a Secret is injected into a container
environment, processes with sufficient access may be able to read it.

Do not expose real production credentials with commands such as:

``` bash
kubectl exec <pod> -- env
```

------------------------------------------------------------------------

# 15. Kubernetes Service Environment Variables

During the lab, `env` also displayed variables such as:

``` text
KUBERNETES_SERVICE_HOST
SERVICES_DEMO_SERVICE_HOST
INGRESS_APP_ONE_SERVICE_HOST
```

These were Kubernetes-provided Service-related variables, not values
from our ConfigMap or Secret.

Our application configuration was:

``` text
APP_ENV
APP_PORT
LOG_LEVEL
DB_USERNAME
API_TOKEN
DATABASE_PASSWORD
```

------------------------------------------------------------------------

# 16. Interview Questions

### What is a ConfigMap?

A Kubernetes object used to store non-sensitive application
configuration separately from the container image.

### What is a Secret?

A Kubernetes object intended for sensitive configuration such as
passwords, tokens, and credentials.

### ConfigMap vs Secret?

ConfigMap is for non-sensitive configuration; Secret is intended for
sensitive configuration.

### Does updating a ConfigMap update environment variables in an existing Pod?

No. Environment variables are populated when the container starts.

### Does Base64 encrypt a Secret?

No. Base64 is encoding, not encryption.

### How can ConfigMaps and Secrets be consumed?

Common methods are environment variables, individual keys, and mounted
files.

### Why externalize configuration?

To reuse the same application image across environments while changing
configuration independently.

------------------------------------------------------------------------

# 17. Quick Revision Commands

``` bash
kubectl get configmap
kubectl describe configmap app-config
kubectl get configmap app-config -o yaml

kubectl get secret
kubectl describe secret app-secret
kubectl get secret app-secret -o yaml

kubectl get pods
kubectl describe pod <pod>

kubectl exec <pod> -- env
kubectl exec <pod> -- ls -l <mount-path>
kubectl exec <pod> -- cat <config-file>
```

------------------------------------------------------------------------

# 18. Phase Outcome

Completed:

-   ConfigMaps
-   Environment injection
-   Individual key injection
-   ConfigMap volume mounts
-   ConfigMap update behavior
-   Secrets
-   `stringData`
-   `data` / Base64
-   Secret environment injection
-   Individual Secret keys
-   Combined ConfigMap + Secret injection
-   Configuration troubleshooting

Next phase: **04 --- Kubernetes Storage**

