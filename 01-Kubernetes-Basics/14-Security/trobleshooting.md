# Kubernetes Security – Troubleshooting Guide

> **Approach:** Prove the failing layer first. Do not fix security problems by blindly adding permissions.

---

# 1. Security Troubleshooting Flow

```text
Security issue
     |
     +--> API access problem / 403?
     |       |
     |       +--> ServiceAccount
     |       +--> Role / ClusterRole
     |       +--> RoleBinding / ClusterRoleBinding
     |       +--> Namespace
     |       +--> API group
     |       +--> Resource
     |       +--> Verb
     |       +--> Subresource
     |
     +--> Container/runtime problem?
             |
             +--> UID/GID
             +--> runAsNonRoot
             +--> fsGroup
             +--> Volume permissions
             +--> readOnlyRootFilesystem
             +--> Capabilities
             +--> Privilege escalation
             +--> Pod Security
```

---

# 2. First Commands to Run

## RBAC

```bash
kubectl auth can-i get pods -n <namespace>
kubectl auth can-i delete pods -n <namespace>

kubectl auth can-i get pods \
  --as=system:serviceaccount:<namespace>:<serviceaccount> \
  -n <namespace>

kubectl auth can-i --list \
  --as=system:serviceaccount:<namespace>:<serviceaccount> \
  -n <namespace>
```

Inspect:

```bash
kubectl get role -A
kubectl get rolebinding -A
kubectl get clusterrole
kubectl get clusterrolebinding
```

## Container security

```bash
kubectl get pod <pod> -o yaml
kubectl describe pod <pod>
kubectl exec -it <pod> -- id
kubectl exec -it <pod> -- ls -ld /path
```

## Events

```bash
kubectl get events --sort-by=.lastTimestamp
```

---

# 3. Problem: Pod Gets 403 Forbidden

### Symptom

```text
403 Forbidden
```

or:

```text
User "system:serviceaccount:rbac-lab:app-sa" cannot get resource "pods"
```

### What it means

The request reached the API server and the identity was recognized, but authorization did not allow the operation.

### Troubleshooting

1. Find the ServiceAccount:

```bash
kubectl get pod <pod> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'
```

2. Test the exact permission:

```bash
kubectl auth can-i get pods \
  --as=system:serviceaccount:<namespace>:<serviceaccount> \
  -n <namespace>
```

3. Check the binding:

```bash
kubectl describe rolebinding <binding> -n <namespace>
```

4. Check the Role/ClusterRole:

```bash
kubectl describe role <role> -n <namespace>
```

5. Verify:

```text
subject
namespace
apiGroup
resource
verb
subresource
```

### Fix

Grant only the missing permission. Do not solve a simple missing `get` permission with `*` permissions.

---

# 4. Problem: Wrong ServiceAccount

### Symptom

Role and RoleBinding look correct, but the app still receives 403.

### Check

```bash
kubectl get pod <pod> -o jsonpath='{.spec.serviceAccountName}'
```

Expected:

```text
app-sa
```

Actual:

```text
default
```

### Root cause

The Pod is using a different identity from the one referenced by the RoleBinding.

### Fix

```yaml
spec:
  serviceAccountName: app-sa
```

Then verify again with `kubectl auth can-i`.

---

# 5. Problem: ServiceAccount Exists in Another Namespace

### Symptom

`app-sa` exists, but access still fails.

### Root cause

ServiceAccounts are namespace-scoped. These are different identities:

```text
system:serviceaccount:dev:app-sa
system:serviceaccount:test:app-sa
```

### Check

```bash
kubectl get sa app-sa -A
```

### Fix

Make sure the Pod, ServiceAccount and RoleBinding subject namespace all match.

---

# 6. Problem: Role Exists but Access Is Denied

### Root cause

A Role only defines permissions. It does not assign them to an identity.

### Check

```bash
kubectl get rolebinding -n <namespace>
```

Correct flow:

```text
ServiceAccount
      |
      v
RoleBinding
      |
      v
Role
```

### Fix

Create or correct the RoleBinding.

---

# 7. Problem: RoleBinding Points to Wrong Role

### Check

```bash
kubectl describe rolebinding <binding> -n <namespace>
```

Look at:

```yaml
roleRef:
  kind: Role
  name: pod-reader
```

Then:

```bash
kubectl describe role pod-reader -n <namespace>
```

### Root cause

The binding may reference a different Role than expected.

### Fix

Correct the `roleRef` to the intended Role.

---

# 8. Problem: Wrong API Group

### Symptom

Deployment access gets 403 even though a Role exists.

### Root cause

Deployment belongs to the `apps` API group, not the core API group.

Correct:

```yaml
apiGroups:
- apps
resources:
- deployments
verbs:
- get
- list
- watch
```

Common mapping:

| Resource | API group |
|---|---|
| Pods | `""` |
| Services | `""` |
| ConfigMaps | `""` |
| Secrets | `""` |
| Deployments | `apps` |
| StatefulSets | `apps` |
| Jobs | `batch` |
| CronJobs | `batch` |
| Ingress | `networking.k8s.io` |
| NetworkPolicy | `networking.k8s.io` |

---

# 9. Problem: Missing Verb

### Example

```text
get  = yes
list = yes
delete = no
```

### Root cause

The Role intentionally allows reading but not deletion.

### Check

```bash
kubectl auth can-i get pods \
  --as=system:serviceaccount:<ns>:<sa> -n <ns>

kubectl auth can-i delete pods \
  --as=system:serviceaccount:<ns>:<sa> -n <ns>
```

### Fix

Add the minimum required verb, not `*`.

---

# 10. Problem: Pod Access Works but Logs Fail

### Symptom

The application can access Pods but cannot read their logs.

### Root cause

`pods` and `pods/log` are separate RBAC resources.

### Fix

```yaml
resources:
- pods
- pods/log
```

with the required verbs.

---

# 11. Problem: ClusterRole Exists but Cluster Access Fails

### Symptom

```bash
kubectl get clusterrole
```

shows the expected ClusterRole, but access still returns `no`.

### Root cause

The ClusterRole defines permissions but must be connected to the identity.

For cluster-wide access:

```text
ClusterRole + ClusterRoleBinding
```

### Check

```bash
kubectl get clusterrolebinding
kubectl describe clusterrolebinding <binding>
```

---

# 12. Problem: ClusterRole Works Only in One Namespace

### Scenario

A ClusterRole reads Pods and is referenced by a RoleBinding in `dev`.

The ServiceAccount can read Pods in `dev` but not `prod`.

### Is it a problem?

No. This is expected.

A RoleBinding referencing a ClusterRole grants those permissions within the RoleBinding's namespace.

For cluster-wide access, use a ClusterRoleBinding.

---

# 13. Problem: ClusterRoleBinding Uses Wrong ServiceAccount

### Check

```bash
kubectl describe clusterrolebinding <binding>
```

Verify:

```yaml
subjects:
- kind: ServiceAccount
  name: monitoring-sa
  namespace: rbac-lab
```

The Pod must actually use that exact identity.

---

# 14. Problem: Pod Runs as Root

### Check

```bash
kubectl exec -it <pod> -- id
```

If you see:

```text
uid=0(root)
```

the process is running as root.

### Why it matters

A compromised root process has more privileges inside the container and potentially a larger security impact.

### Fix

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
```

First confirm the image supports the selected non-root UID.

---

# 15. Problem: runAsNonRoot Prevents Startup

### Symptom

The Pod fails to start because the image would run as root while:

```yaml
runAsNonRoot: true
```

is enabled.

### Root cause

The image expects UID 0.

### Fix

Prefer an image designed to run as a non-root user. For custom images, use a non-root `USER` and align Kubernetes settings with the image.

Example Dockerfile pattern:

```dockerfile
RUN useradd -u 1000 appuser
USER appuser
```

---

# 16. Problem: Permission Denied on Mounted Volume

### Symptom

Application starts but cannot write to `/data` or another mounted directory.

### Troubleshooting

```bash
kubectl exec -it <pod> -- id
kubectl exec -it <pod> -- ls -ld /data
kubectl describe pod <pod>
```

### Possible root cause

Application:

```text
UID 1000
```

Volume directory:

```text
root:root
```

with permissions that do not allow the application to write.

### Possible fix

Use an appropriate `fsGroup` where supported:

```yaml
securityContext:
  fsGroup: 2000
```

Do not blindly use `chmod 777` in production.

---

# 17. Problem: Read-only Filesystem

### Symptom

```text
Read-only file system
```

### Root cause

The application tries to write to the container root filesystem while:

```yaml
readOnlyRootFilesystem: true
```

is enabled.

### Troubleshooting

Identify the exact path being written, for example:

```text
/tmp
/var/cache
/app/logs
```

### Fix

Mount only the required path as writable:

```yaml
volumeMounts:
- name: tmp
  mountPath: /tmp
volumes:
- name: tmp
  emptyDir: {}
```

---

# 18. Problem: Application Needs a Linux Capability

### Symptom

An application operation fails after:

```yaml
capabilities:
  drop:
  - ALL
```

### Root cause

The application genuinely requires a specific Linux capability.

### Correct approach

Identify the exact required capability and add only that capability. Do not revert to full root privileges just because one operation fails.

---

# 19. Problem: Privilege Escalation Error

### Symptom

An operation fails while:

```yaml
allowPrivilegeEscalation: false
```

is enabled.

### Troubleshooting

Determine whether the application really needs privilege escalation. Check Pod events and application requirements.

### Production approach

Keep privilege escalation disabled where possible. If a workload genuinely requires elevated behavior, isolate and document that exception.

---

# 20. Problem: Pod Rejected by Pod Security

### Symptoms

Pod creation is rejected or warnings appear due to configurations such as:

```text
privileged container
root execution
host namespaces
unsafe capabilities
hostPath
```

### Check namespace policy

```bash
kubectl get namespace <namespace> --show-labels
```

Look for:

```text
pod-security.kubernetes.io/enforce
pod-security.kubernetes.io/warn
pod-security.kubernetes.io/audit
```

### Fix

Bring the workload into compliance. Common hardening changes include:

```yaml
runAsNonRoot: true
allowPrivilegeEscalation: false
capabilities:
  drop:
  - ALL
```

The exact change depends on the policy violation.

---

# 21. Problem: Restricted Policy Breaks Legacy Application

### Symptom

Existing applications stop deploying after namespace enforcement.

### Root cause

The workloads may rely on settings that Restricted does not allow.

### Safer production rollout

```text
Audit
  ↓
Warn
  ↓
Fix workloads
  ↓
Test
  ↓
Enforce
```

Do not blindly enforce Restricted across legacy workloads.

---

# 22. Problem: One RBAC Command Works, Another Fails

Example:

```bash
kubectl get pods     # works
kubectl delete pods  # fails
```

This can be completely expected.

Test directly:

```bash
kubectl auth can-i get pods \
  --as=system:serviceaccount:<ns>:<sa> -n <ns>

kubectl auth can-i delete pods \
  --as=system:serviceaccount:<ns>:<sa> -n <ns>
```

Possible result:

```text
yes
no
```

That means RBAC is doing exactly what the Role says.

---

# 23. Problem: RBAC Changed but Application Still Fails

### Troubleshooting

First test the live authorization decision:

```bash
kubectl auth can-i ...
```

Then inspect the actual cluster objects:

```bash
kubectl get role <role> -o yaml
kubectl get rolebinding <binding> -o yaml
```

Confirm the namespace and subject. Do not assume the YAML file on your machine matches the object currently stored in the cluster.

Then retry the application operation.

---

# 24. Problem: Application Has Too Much Permission

### Symptom

```bash
kubectl auth can-i --list \
  --as=system:serviceaccount:<ns>:<sa>
```

shows access the application does not need.

### Possible causes

```text
wildcard permissions
multiple RoleBindings
broad ClusterRoleBinding
overly broad ClusterRole
```

### Fix

Find all bindings and reduce access to the actual requirement.

Useful checks:

```bash
kubectl get rolebinding -A
kubectl get clusterrolebinding
```

---

# 25. Problem: Pod Cannot Access Kubernetes API

Do not immediately assume RBAC.

Check in this order:

```text
1. Is the correct ServiceAccount assigned?
2. Is the token expected to be mounted?
3. Is automountServiceAccountToken disabled?
4. Can the Pod reach the API endpoint?
5. Is authentication successful?
6. Does RBAC allow the operation?
```

Check the live Pod:

```bash
kubectl get pod <pod> -o yaml
```

Look for:

```yaml
serviceAccountName:
automountServiceAccountToken:
```

If:

```yaml
automountServiceAccountToken: false
```

the normal ServiceAccount token is not automatically mounted.

---

# 26. Security Incident: Application Suspected Compromised

Think about blast radius.

Review:

```text
ServiceAccount permissions
ClusterRoleBindings
Secrets access
Network access
Cloud IAM permissions
Writable filesystem
Linux capabilities
```

The practical question is:

> If this Pod is compromised, what else can it reach or change?

Least privilege reduces that blast radius.

---

# 27. Interview Troubleshooting Answer

If asked:

**"How do you troubleshoot a Kubernetes RBAC issue?"**

Answer:

> "First I identify the exact API operation that is failing and the identity making the request. Then I verify the Pod's ServiceAccount and namespace. I inspect the Role or ClusterRole and the corresponding binding. I check the API group, resource, verb and subresource. I use `kubectl auth can-i` to reproduce the authorization decision directly. If the API permission is correct, I move to the container layer and check SecurityContext, UID/GID, fsGroup, filesystem permissions and Pod Security restrictions."

---

# 28. Security Troubleshooting Checklist

## ServiceAccount

```text
[ ] Correct ServiceAccount?
[ ] Correct namespace?
[ ] Pod actually uses it?
[ ] Token mounting expected?
```

## RBAC

```text
[ ] Correct Role/ClusterRole?
[ ] Correct Binding?
[ ] Correct subject?
[ ] Correct namespace?
[ ] Correct API group?
[ ] Correct resource?
[ ] Correct verb?
[ ] Correct subresource?
```

## Container security

```text
[ ] UID correct?
[ ] GID correct?
[ ] runAsNonRoot?
[ ] fsGroup?
[ ] Volume ownership?
[ ] Read-only filesystem?
[ ] Capabilities?
[ ] Privilege escalation?
```

## Pod Security

```text
[ ] Namespace security labels?
[ ] Audit/warn/enforce mode?
[ ] Workload compliant?
```

---

# 29. Troubleshooting Cheat Sheet

| Symptom | First thing to check |
|---|---|
| 403 Forbidden | RBAC / `kubectl auth can-i` |
| Wrong identity | `serviceAccountName` |
| Role exists but access denied | RoleBinding |
| Cluster resource denied | ClusterRole + appropriate binding |
| Deployment denied | `apiGroups: ["apps"]` |
| Logs denied | `pods/log` permission |
| Delete denied | `delete` verb |
| Permission denied on volume | UID/GID + fsGroup |
| Container starts as root | `runAsNonRoot` / image USER |
| Container fails with runAsNonRoot | Image expects root |
| Read-only filesystem | `readOnlyRootFilesystem` |
| App needs privilege | Capabilities / privilege escalation |
| Pod rejected | Pod Security Admission |
| Too much access | Wildcards / broad bindings |
| API unavailable from Pod | SA token, networking, authentication, RBAC |

---

# 30. Final Security Troubleshooting Mental Model

```text
                    SECURITY ISSUE
                          |
             +------------+------------+
             |                         |
        API ACCESS                 CONTAINER
             |                         |
             v                         v
      Authentication             SecurityContext
             |                         |
       ServiceAccount             UID / GID
             |                         |
       Authorization               fsGroup
             |                         |
            RBAC                Filesystem permissions
             |                         |
      Role / ClusterRole          Capabilities
             |                         |
   RoleBinding / CRB        Privilege escalation
             |                         |
 API group / resource / verb   Read-only filesystem
             |                         |
        subresource             Pod Security
```

## Golden rule

> **Do not fix Kubernetes security problems by blindly adding permissions. First identify the identity, requested operation, required privilege, and exact security control that is blocking it. Then make the smallest safe change and verify it.**
