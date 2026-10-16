# Kubernetes Configuration --- Troubleshooting

## 1. ConfigMap Missing

### Problem

Pod references a ConfigMap that does not exist.

### Troubleshooting

``` bash
kubectl get configmap
kubectl describe pod <pod-name>
```

Check Pod Events.

### Root Cause

The referenced ConfigMap name does not exist in the namespace.

### Resolution

Create the ConfigMap or correct the reference:

``` yaml
configMapRef:
  name: app-config
```

------------------------------------------------------------------------

## 2. Secret Missing

### Problem

Pod references a Secret that does not exist.

### Troubleshooting

``` bash
kubectl get secret
kubectl describe pod <pod-name>
```

Check Events.

### Root Cause

The Secret name in the Pod specification does not match an existing
Secret.

### Resolution

Correct the reference:

``` yaml
secretRef:
  name: app-secret
```

------------------------------------------------------------------------

## 3. ConfigMap Updated but Pod Has Old Environment Value

### Problem

ConfigMap shows:

``` text
APP_ENV=production
```

but the running container still shows:

``` text
APP_ENV=development
```

### Root Cause

The ConfigMap was injected as an environment variable. Environment
variables are populated when the container starts.

### Troubleshooting

``` bash
kubectl get configmap app-config -o yaml

kubectl exec <pod> --   env | grep APP_ENV
```

### Resolution

Restart/recreate the Pod:

``` bash
kubectl delete pod configmap-demo
kubectl apply -f configmap-pod.yaml
```

Then verify again.

------------------------------------------------------------------------

## 4. Mounted ConfigMap File Missing

### Troubleshooting

``` bash
kubectl describe pod <pod>
kubectl exec <pod> -- ls -l /etc/app-config
```

Check:

``` yaml
volumes:
  - name: config-volume
    configMap:
      name: app-config

volumeMounts:
  - name: config-volume
    mountPath: /etc/app-config
```

### Common Causes

-   Wrong ConfigMap name
-   Wrong volume name
-   Wrong `volumeMounts.name`
-   Wrong mount path
-   Missing ConfigMap key

### Resolution

Make sure:

``` text
volumes.name == volumeMounts.name
```

and:

``` text
volumes.configMap.name == actual ConfigMap name
```

------------------------------------------------------------------------

## 5. ConfigMap Key Missing

### Problem

Pod references:

``` yaml
configMapKeyRef:
  name: app-config
  key: APP_ENVIRONMENT
```

but ConfigMap contains:

``` text
APP_ENV
```

### Troubleshooting

``` bash
kubectl describe configmap app-config
kubectl get configmap app-config -o yaml
```

### Root Cause

The referenced key does not exist.

### Resolution

Use the correct key or add the required key.

------------------------------------------------------------------------

## 6. Secret Key Missing

### Problem

Pod references:

``` yaml
secretKeyRef:
  name: app-secret
  key: DB_PASSWORD
```

but the Secret does not contain that key.

### Troubleshooting

``` bash
kubectl describe secret app-secret
```

### Root Cause

The Secret exists but the requested key does not.

### Resolution

Use the correct key or update the Secret.

------------------------------------------------------------------------

## 7. Secret Appears in Container Environment

### Problem

A command such as:

``` bash
kubectl exec secret-demo -- env
```

prints Secret values.

### Explanation

The Secret was injected into the container environment.

### Good Practice

Do not print real production credentials during troubleshooting.

Avoid:

-   Credentials in Git
-   Credentials in application logs
-   Credentials in screenshots
-   Sharing Secret values
-   Unnecessary `env` dumps

------------------------------------------------------------------------

## 8. Secret Looks Like Random Characters

Example:

``` text
DB_PASSWORD: TXlQYXNzd29yZDEyMw==
```

This is Base64 encoding.

It is not encryption.

Lab decoding:

``` bash
echo 'TXlQYXNzd29yZDEyMw==' | base64 -d
```

------------------------------------------------------------------------

## 9. Configuration Troubleshooting Flow

``` text
Pod problem
    |
    v
kubectl describe pod
    |
    v
Check Events
    |
    +--> ConfigMap exists?
    |
    +--> Secret exists?
    |
    +--> Key exists?
    |
    +--> Correct object name?
    |
    +--> Correct volume/mount?
    |
    v
Fix YAML
    |
    v
Apply/recreate Pod
    |
    v
Verify configuration
```

------------------------------------------------------------------------

## 10. Quick Troubleshooting Table

  -------------------------------------------------------------------------
  Problem                             First checks
  ----------------------------------- -------------------------------------
  ConfigMap missing                   `kubectl get configmap`

  Secret missing                      `kubectl get secret`

  Wrong key                           `kubectl describe configmap/secret`

  Pod won't start                     `kubectl describe pod`

  Old environment value               Check environment-variable
                                      injection/update behavior

  File missing                        Check `volumes` and `volumeMounts`

  Secret exposed                      Review commands, logs, and access
                                      controls
  -------------------------------------------------------------------------

------------------------------------------------------------------------

## 11. Interview Troubleshooting Explanation

> I first check the Pod status and describe the Pod to inspect Events.
> Then I verify that the referenced ConfigMap or Secret exists in the
> same namespace and that the required key exists. If configuration is
> injected through environment variables, I remember that updating the
> ConfigMap or Secret does not change the existing process environment,
> so I restart the Pod. If configuration is mounted as a file, I verify
> the volume and volumeMount definitions and inspect the mounted file.

------------------------------------------------------------------------

## 12. Production Considerations

Typical production pattern:

``` text
ConfigMap
    ↓
Non-sensitive configuration

Secret / external secret manager
    ↓
Sensitive credentials
```

Additional controls can include:

-   RBAC
-   Encryption at rest
-   Restricted Secret access
-   External secret-management systems
-   Cloud IAM integration
-   Avoiding credentials in source control
-   Avoiding credentials in logs

For EKS, AWS Secrets Manager integration will be covered later.

------------------------------------------------------------------------

## 13. Phase Outcome

You should now be able to distinguish:

``` text
ConfigMap problem
Secret problem
Key problem
Volume/mount problem
Environment-variable update behavior
Application reload behavior
```

Core commands:

``` bash
kubectl get configmap
kubectl describe configmap <name>

kubectl get secret
kubectl describe secret <name>

kubectl get pod
kubectl describe pod <name>

kubectl exec <pod> -- env
kubectl exec <pod> -- ls -l <mount-path>
kubectl exec <pod> -- cat <config-file>
```

Next phase: **04 --- Kubernetes Storage**
# Kubernetes Configuration --- Troubleshooting

## 1. ConfigMap Missing

### Problem

Pod references a ConfigMap that does not exist.

### Troubleshooting

``` bash
kubectl get configmap
kubectl describe pod <pod-name>
```

Check Pod Events.

### Root Cause

The referenced ConfigMap name does not exist in the namespace.

### Resolution

Create the ConfigMap or correct the reference:

``` yaml
configMapRef:
  name: app-config
```

------------------------------------------------------------------------

## 2. Secret Missing

### Problem

Pod references a Secret that does not exist.

### Troubleshooting

``` bash
kubectl get secret
kubectl describe pod <pod-name>
```

Check Events.

### Root Cause

The Secret name in the Pod specification does not match an existing
Secret.

### Resolution

Correct the reference:

``` yaml
secretRef:
  name: app-secret
```

------------------------------------------------------------------------

## 3. ConfigMap Updated but Pod Has Old Environment Value

### Problem

ConfigMap shows:

``` text
APP_ENV=production
```

but the running container still shows:

``` text
APP_ENV=development
```

### Root Cause

The ConfigMap was injected as an environment variable. Environment
variables are populated when the container starts.

### Troubleshooting

``` bash
kubectl get configmap app-config -o yaml

kubectl exec <pod> --   env | grep APP_ENV
```

### Resolution

Restart/recreate the Pod:

``` bash
kubectl delete pod configmap-demo
kubectl apply -f configmap-pod.yaml
```

Then verify again.

------------------------------------------------------------------------

## 4. Mounted ConfigMap File Missing

### Troubleshooting

``` bash
kubectl describe pod <pod>
kubectl exec <pod> -- ls -l /etc/app-config
```

Check:

``` yaml
volumes:
  - name: config-volume
    configMap:
      name: app-config

volumeMounts:
  - name: config-volume
    mountPath: /etc/app-config
```

### Common Causes

-   Wrong ConfigMap name
-   Wrong volume name
-   Wrong `volumeMounts.name`
-   Wrong mount path
-   Missing ConfigMap key

### Resolution

Make sure:

``` text
volumes.name == volumeMounts.name
```

and:

``` text
volumes.configMap.name == actual ConfigMap name
```

------------------------------------------------------------------------

## 5. ConfigMap Key Missing

### Problem

Pod references:

``` yaml
configMapKeyRef:
  name: app-config
  key: APP_ENVIRONMENT
```

but ConfigMap contains:

``` text
APP_ENV
```

### Troubleshooting

``` bash
kubectl describe configmap app-config
kubectl get configmap app-config -o yaml
```

### Root Cause

The referenced key does not exist.

### Resolution

Use the correct key or add the required key.

------------------------------------------------------------------------

## 6. Secret Key Missing

### Problem

Pod references:

``` yaml
secretKeyRef:
  name: app-secret
  key: DB_PASSWORD
```

but the Secret does not contain that key.

### Troubleshooting

``` bash
kubectl describe secret app-secret
```

### Root Cause

The Secret exists but the requested key does not.

### Resolution

Use the correct key or update the Secret.

------------------------------------------------------------------------

## 7. Secret Appears in Container Environment

### Problem

A command such as:

``` bash
kubectl exec secret-demo -- env
```

prints Secret values.

### Explanation

The Secret was injected into the container environment.

### Good Practice

Do not print real production credentials during troubleshooting.

Avoid:

-   Credentials in Git
-   Credentials in application logs
-   Credentials in screenshots
-   Sharing Secret values
-   Unnecessary `env` dumps

------------------------------------------------------------------------

## 8. Secret Looks Like Random Characters

Example:

``` text
DB_PASSWORD: TXlQYXNzd29yZDEyMw==
```

This is Base64 encoding.

It is not encryption.

Lab decoding:

``` bash
echo 'TXlQYXNzd29yZDEyMw==' | base64 -d
```

------------------------------------------------------------------------

## 9. Configuration Troubleshooting Flow

``` text
Pod problem
    |
    v
kubectl describe pod
    |
    v
Check Events
    |
    +--> ConfigMap exists?
    |
    +--> Secret exists?
    |
    +--> Key exists?
    |
    +--> Correct object name?
    |
    +--> Correct volume/mount?
    |
    v
Fix YAML
    |
    v
Apply/recreate Pod
    |
    v
Verify configuration
```

------------------------------------------------------------------------

## 10. Quick Troubleshooting Table

  -------------------------------------------------------------------------
  Problem                             First checks
  ----------------------------------- -------------------------------------
  ConfigMap missing                   `kubectl get configmap`

  Secret missing                      `kubectl get secret`

  Wrong key                           `kubectl describe configmap/secret`

  Pod won't start                     `kubectl describe pod`

  Old environment value               Check environment-variable
                                      injection/update behavior

  File missing                        Check `volumes` and `volumeMounts`

  Secret exposed                      Review commands, logs, and access
                                      controls
  -------------------------------------------------------------------------

------------------------------------------------------------------------

## 11. Interview Troubleshooting Explanation

> I first check the Pod status and describe the Pod to inspect Events.
> Then I verify that the referenced ConfigMap or Secret exists in the
> same namespace and that the required key exists. If configuration is
> injected through environment variables, I remember that updating the
> ConfigMap or Secret does not change the existing process environment,
> so I restart the Pod. If configuration is mounted as a file, I verify
> the volume and volumeMount definitions and inspect the mounted file.

------------------------------------------------------------------------

## 12. Production Considerations

Typical production pattern:

``` text
ConfigMap
    ↓
Non-sensitive configuration

Secret / external secret manager
    ↓
Sensitive credentials
```

Additional controls can include:

-   RBAC
-   Encryption at rest
-   Restricted Secret access
-   External secret-management systems
-   Cloud IAM integration
-   Avoiding credentials in source control
-   Avoiding credentials in logs

For EKS, AWS Secrets Manager integration will be covered later.

------------------------------------------------------------------------

## 13. Phase Outcome

You should now be able to distinguish:

``` text
ConfigMap problem
Secret problem
Key problem
Volume/mount problem
Environment-variable update behavior
Application reload behavior
```

Core commands:

``` bash
kubectl get configmap
kubectl describe configmap <name>

kubectl get secret
kubectl describe secret <name>

kubectl get pod
kubectl describe pod <name>

kubectl exec <pod> -- env
kubectl exec <pod> -- ls -l <mount-path>
kubectl exec <pod> -- cat <config-file>
```

Next phase: **04 --- Kubernetes Storage**
