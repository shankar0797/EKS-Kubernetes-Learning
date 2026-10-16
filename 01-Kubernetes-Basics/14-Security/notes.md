# Kubernetes Security – Notes

> **Style:** Interview-ready, practical explanations. No textbook definitions. Explain what we actually do, why we do it, what problem it solves, and how we troubleshoot it.

## 07. Kubernetes Security

### Topics covered
- ServiceAccounts
- Authentication vs Authorization
- RBAC
- Roles
- RoleBindings
- ClusterRoles
- ClusterRoleBindings
- SecurityContext
- runAsUser / runAsGroup
- fsGroup / runAsNonRoot
- Privilege escalation and Linux capabilities
- Read-only root filesystem
- Pod Security / Pod Security Admission
- Security troubleshooting
- Production practices
- Interview Q&A
- Cheat sheet

---

## 1. ServiceAccounts

### How I explain it in an interview

A ServiceAccount is the **identity given to a Pod when the application inside it needs to interact with the Kubernetes API**. Instead of allowing every application to act anonymously or with broad access, we give the workload its own identity and then control that identity using RBAC.

### Why do we need it?

Example: a monitoring application needs to read Pods.

```text
Application Pod
      |
      | API request
      v
Kubernetes API Server
      |
      | Who are you?
      v
ServiceAccount identity
      |
      | What can you do?
      v
RBAC
```

Easy memory:

```text
ServiceAccount = Who are you?
RBAC           = What can you do?
```

Example:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: monitoring-sa
```

Pod:

```yaml
spec:
  serviceAccountName: monitoring-sa
```

Useful commands:

```bash
kubectl get serviceaccounts
kubectl describe serviceaccount monitoring-sa
kubectl get pod <pod-name> -o yaml
```

Modern Kubernetes generally uses **short-lived projected ServiceAccount tokens** rather than automatically creating a long-lived token Secret for every ServiceAccount. A mounted token is normally available under:

```text
/var/run/secrets/kubernetes.io/serviceaccount/
```

**Interview point:** Do not say every ServiceAccount automatically creates a Secret token; that is an outdated explanation for modern Kubernetes.

---

## 2. Authentication vs Authorization

The easiest interview explanation is:

```text
Authentication = Who are you?
Authorization  = What are you allowed to do?
```

Example:

```text
Developer / workload
        |
        | Authentication
        v
Kubernetes knows the identity
        |
        | Authorization / RBAC
        v
Can this identity delete Pods?
```

A request can be successfully authenticated and still receive:

```text
403 Forbidden
```

because RBAC does not allow the operation.

---

## 3. RBAC

### How I explain it

RBAC is how we control **which Kubernetes API operations an identity is allowed to perform**. In production, the main goal is least privilege: give an application only the resources and actions it actually needs.

Flow:

```text
Identity + Permissions + Binding

ServiceAccount
      |
      v
Role / ClusterRole
      |
      v
RoleBinding / ClusterRoleBinding
```

Example: an app only needs to read Pods.

```yaml
verbs:
- get
- list
- watch
resources:
- pods
```

It can read Pods but cannot delete Pods, create Deployments, or read Secrets unless separate permissions grant those actions.

### Important

RBAC is additive. Normal RBAC rules grant allowed permissions; they are not an explicit deny system.

---

## 4. Role

### Interview explanation

A Role is a **namespace-level permission document**. It says what an identity is allowed to do on resources inside a particular namespace.

Example:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: rbac-lab
rules:
- apiGroups: [""]
  resources:
  - pods
  verbs:
  - get
  - list
  - watch
```

Important fields:

```text
apiGroups
resources
verbs
```

Common API groups:

| Resource | API group |
|---|---|
| Pods | `""` |
| Services | `""` |
| ConfigMaps | `""` |
| Secrets | `""` |
| Deployments | `apps` |
| ReplicaSets | `apps` |
| StatefulSets | `apps` |
| Jobs | `batch` |
| CronJobs | `batch` |
| Ingress | `networking.k8s.io` |
| NetworkPolicy | `networking.k8s.io` |

### Subresources

Some operations use subresources:

```text
pods
pods/log
pods/exec
```

Reading logs can therefore require:

```yaml
resources:
- pods/log
```

### resourceNames

You can restrict access to specific named objects:

```yaml
resources:
- configmaps
resourceNames:
- application-config
```

This is more restrictive than allowing every ConfigMap.

---

## 5. RoleBinding

### Interview explanation

A Role defines permissions, but it does not give those permissions to an identity by itself. A RoleBinding connects **who** to **which permissions**.

```text
app-sa
  |
  | RoleBinding
  v
pod-reader Role
  |
  v
get/list/watch Pods
```

Example:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-sa-pod-reader
  namespace: rbac-lab
subjects:
- kind: ServiceAccount
  name: app-sa
  namespace: rbac-lab
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### Important

A RoleBinding is namespace-scoped. It can reference a ClusterRole, but the permissions granted through that RoleBinding are limited to the RoleBinding's namespace.

This is a useful production pattern:

```text
Reusable ClusterRole
       |
       +-- RoleBinding -> team-a
       +-- RoleBinding -> team-b
```

---

## 6. ClusterRole

### Interview explanation

A ClusterRole is used when permissions need to cover cluster-scoped resources or when we want a reusable permission set that can be bound in multiple namespaces.

Examples of cluster-scoped resources:

```text
Nodes
PersistentVolumes
Namespaces
StorageClasses
```

Example:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
- apiGroups: [""]
  resources:
  - nodes
  verbs:
  - get
  - list
  - watch
```

### Important interview point

A ClusterRole does **not** automatically mean cluster-wide access. The binding determines the scope.

A ClusterRole can also define namespaced permissions:

```text
ClusterRole: read Pods
       |
       +-- RoleBinding in team-a -> Pods in team-a
       +-- RoleBinding in team-b -> Pods in team-b
```

---

## 7. ClusterRoleBinding

### Interview explanation

A ClusterRoleBinding connects an identity to a ClusterRole at cluster scope.

```text
ServiceAccount
      |
      | ClusterRoleBinding
      v
ClusterRole
      |
      v
Cluster-level permissions
```

Example:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: monitoring-sa-global-pod-reader
subjects:
- kind: ServiceAccount
  name: monitoring-sa
  namespace: rbac-lab
roleRef:
  kind: ClusterRole
  name: global-pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### RoleBinding vs ClusterRoleBinding

| Item | RoleBinding | ClusterRoleBinding |
|---|---|---|
| Binding scope | Namespace | Cluster |
| Can reference Role | Yes | No |
| Can reference ClusterRole | Yes | Yes |
| Typical use | App access in one namespace | Cluster-wide monitoring/admin access |

---

## 8. Complete RBAC mental model

```text
IDENTITY
   |
ServiceAccount / User
   |
   v
BINDING
 /       \
RoleBinding  ClusterRoleBinding
 |              |
 v              v
Role         ClusterRole
  \            /
   +----------+
        |
        v
API permissions
get/list/watch/create/update/delete
```

When troubleshooting, always ask:

```text
1. Who is the identity?
2. Which namespace?
3. Which Role/ClusterRole?
4. Which Binding?
5. Which resource?
6. Which API group?
7. Which verb?
8. Is it a subresource?
```

---

## 9. SecurityContext

### Interview explanation

SecurityContext controls **how the Pod/container runs from a Linux security perspective**.

Typical controls:

```text
Run as non-root
UID/GID
Filesystem group
Disable privilege escalation
Drop capabilities
Read-only root filesystem
```

Pod-level example:

```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 1000
  runAsNonRoot: true
  fsGroup: 2000
```

Container-level example:

```yaml
containers:
- name: app
  securityContext:
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true
    capabilities:
      drop:
      - ALL
```

### Pod vs container level

Use Pod-level settings for common identity/filesystem behavior and container-level settings when one container needs a specific behavior.

---

## 10. runAsUser / runAsGroup

`runAsUser` controls the Linux UID.

```yaml
securityContext:
  runAsUser: 1000
```

Instead of UID 0/root, the process runs as UID 1000.

`runAsGroup` controls the primary Linux group:

```yaml
securityContext:
  runAsUser: 1000
  runAsGroup: 1000
```

### Why?

If an application is compromised, running as a non-root user reduces the privileges and potential blast radius.

---

## 11. runAsNonRoot

```yaml
securityContext:
  runAsNonRoot: true
```

This tells Kubernetes that the container must not run as root. If the image expects UID 0, the container can fail instead of silently running as root.

**Interview line:**

> I use runAsNonRoot as an explicit guard so a workload does not accidentally start with root privileges.

---

## 12. fsGroup

`fsGroup` is mainly used for group-based access to supported mounted volumes.

```yaml
securityContext:
  fsGroup: 2000
```

Typical situation:

```text
App runs as UID 1000
       |
       v
Volume mounted
       |
       v
Permission denied
```

An appropriate `fsGroup` can help when the storage system supports the relevant ownership behavior.

Do not blindly solve storage permissions with `chmod 777`.

---

## 13. Privilege Escalation

```yaml
securityContext:
  allowPrivilegeEscalation: false
```

This prevents a process from gaining more privilege than its parent through mechanisms such as setuid/setgid behavior.

For hardened applications, it is commonly combined with:

```text
runAsNonRoot
+ drop capabilities
+ readOnlyRootFilesystem
```

---

## 14. Linux Capabilities

Linux capabilities split some traditionally root-level privileges into smaller permissions.

A common hardening step is:

```yaml
securityContext:
  capabilities:
    drop:
    - ALL
```

If the application genuinely needs one capability, add only that capability rather than restoring broad privileges.

---

## 15. Read-only root filesystem

```yaml
securityContext:
  readOnlyRootFilesystem: true
```

This prevents writes to the container's root filesystem.

If the app needs temporary writable storage:

```yaml
volumeMounts:
- name: tmp
  mountPath: /tmp
volumes:
- name: tmp
  emptyDir: {}
```

Result:

```text
Container root filesystem = read-only
/tmp                       = writable
```

This reduces the ability of a compromised application to write arbitrary files into the container filesystem.

---

## 16. Practical hardened workload

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    runAsNonRoot: true
    fsGroup: 2000
  containers:
  - name: app
    image: nginx:stable
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

Always test security settings against the application's actual runtime requirements.

---

## 17. Pod Security / Pod Security Admission

### Interview explanation

Pod Security controls what security configurations are allowed in a namespace. The common Pod Security Standards levels are:

```text
Privileged
Baseline
Restricted
```

Think of them as increasing levels of restriction.

- **Privileged:** few restrictions; used only where elevated behavior is genuinely required.
- **Baseline:** blocks many common risky configurations while allowing normal workloads.
- **Restricted:** strongest hardening expectations for workloads that can comply.

Namespace example:

```bash
kubectl label namespace secure-ns \
  pod-security.kubernetes.io/enforce=restricted
```

You can also use `warn` and `audit`.

### Production rollout

```text
Audit existing workloads
        ↓
Warn developers
        ↓
Fix incompatible workloads
        ↓
Test
        ↓
Enforce
```

Do not blindly enforce Restricted on legacy applications before testing.

---

## 18. Security troubleshooting methodology

When something fails:

```text
1. Identify the exact failing operation
2. Identify the identity
3. Identify namespace
4. Check RBAC
5. Check SecurityContext
6. Check filesystem permissions
7. Check Pod Security
8. Check events/logs
9. Reproduce with a controlled test
10. Apply minimum required permission
11. Verify
```

For API authorization problems, start with:

```bash
kubectl auth can-i ...
```

For container security problems, inspect:

```bash
kubectl get pod <pod> -o yaml
kubectl describe pod <pod>
kubectl exec -it <pod> -- id
```

---

## 19. Production security approach

```text
Workload identity
      ↓
ServiceAccount
      ↓
Least-privilege RBAC
      ↓
SecurityContext
      ├─ Non-root
      ├─ No privilege escalation
      ├─ Drop capabilities
      └─ Read-only filesystem where practical
      ↓
Pod Security controls
      ↓
Network controls
      ↓
Secret protection
      ↓
Monitoring / auditing
```

### Production principles

1. Use dedicated ServiceAccounts when workload identity is required.
2. Prefer namespace-level Roles over cluster-wide access when possible.
3. Avoid wildcard RBAC.
4. Run applications as non-root.
5. Disable privilege escalation where possible.
6. Drop unnecessary capabilities.
7. Use read-only root filesystems where practical.
8. Apply Pod Security controls with a staged rollout.
9. Protect Secrets and avoid unnecessary Secret access.
10. Review the blast radius: if the Pod is compromised, what can it reach?

### EKS connection

Later, EKS workload identity will connect Kubernetes identities with AWS permissions. The same principle applies:

```text
Pod identity -> minimum AWS permissions
```

---

# Interview Q&A

### Q1. What is a ServiceAccount?

> A ServiceAccount gives a workload its Kubernetes identity. If a Pod needs to interact with the Kubernetes API, I assign a ServiceAccount and then control its permissions through RBAC.

### Q2. Authentication vs Authorization?

> Authentication identifies who is making the request. Authorization decides whether that identity is allowed to perform the requested action.

### Q3. What is RBAC?

> RBAC controls Kubernetes API access based on identities, resources and actions. In production I use it mainly for least privilege so applications only get what they actually need.

### Q4. Role vs ClusterRole?

> A Role is namespace-scoped. A ClusterRole is used for cluster-scoped resources and can also be reused for namespaced permissions.

### Q5. RoleBinding vs ClusterRoleBinding?

> RoleBinding grants permissions within a namespace. ClusterRoleBinding grants a ClusterRole at cluster scope.

### Q6. Can a RoleBinding reference a ClusterRole?

> Yes. The permissions granted through that RoleBinding are limited to the RoleBinding's namespace.

### Q7. Why avoid wildcard permissions?

> They can give much more access than the workload needs. If the workload is compromised, the blast radius becomes larger.

### Q8. Why use SecurityContext?

> It controls how the container runs from a Linux security perspective, such as UID/GID, non-root execution, privilege escalation, capabilities and filesystem access.

### Q9. What does runAsNonRoot do?

> It prevents the workload from running as root. If the image requires root, the container can fail instead of running with UID 0.

### Q10. What is fsGroup?

> It is mainly used to provide group-based access to supported mounted volumes, which is useful when a non-root application needs group permissions on a volume.

### Q11. Why use readOnlyRootFilesystem?

> It prevents the application from modifying the root filesystem. If a writable path is required, I mount only that path using a volume such as emptyDir.

### Q12. How do you troubleshoot a 403 from Kubernetes API?

> I identify the identity and namespace, verify the ServiceAccount, inspect the Role or ClusterRole and binding, then check API group, resource, verb and subresource. I use kubectl auth can-i to verify the permission directly.

### Q13. ServiceAccount exists but application gets 403. What do you check?

> First I verify the Pod actually uses that ServiceAccount. Then I verify the binding and subject namespace/name. Finally I check the exact API resource, group and verb required.

### Q14. Pod can read Pods but cannot read logs. Why?

> Pods and pods/log are separate RBAC resources. The Role may allow Pods but not the pods/log subresource.

### Q15. What is Pod Security Admission?

> It is Kubernetes' built-in mechanism for applying Pod Security Standards to namespaces. We can use Privileged, Baseline or Restricted levels and roll them out with audit, warn and enforce modes.

### Q16. How would you secure a production application?

> I would use a dedicated ServiceAccount, least-privilege RBAC, non-root execution, disabled privilege escalation, dropped capabilities, read-only root filesystem where practical, controlled writable volumes, Pod Security controls, NetworkPolicies, secure secret handling and monitoring/auditing.

---

# One-minute Security explanation

> "I look at Kubernetes security in layers. First I identify the workload using a ServiceAccount. Then I use RBAC to control what that identity can do against the Kubernetes API. For namespace-level access I generally use Roles and RoleBindings, and for cluster-wide or reusable permissions I use ClusterRoles with the appropriate binding. At the container level I use SecurityContext to run workloads as non-root, disable privilege escalation, drop unnecessary Linux capabilities, and use a read-only root filesystem where possible. I also use Pod Security controls to prevent unsafe Pod configurations. When troubleshooting, I start with the identity and namespace, then verify the binding, API group, resource, verb, subresource, and finally the container UID/GID and filesystem permissions."

---

# Security Cheat Sheet

| Concept | Remember it as |
|---|---|
| ServiceAccount | Pod identity |
| Authentication | Who are you? |
| Authorization | What can you do? |
| RBAC | Kubernetes API permission control |
| Role | Namespace-level permissions |
| RoleBinding | Connect identity to Role |
| ClusterRole | Cluster/reusable permissions |
| ClusterRoleBinding | Cluster-wide binding |
| runAsUser | Linux UID |
| runAsGroup | Linux primary GID |
| runAsNonRoot | Prevent root execution |
| fsGroup | Group-based volume/filesystem access |
| allowPrivilegeEscalation | Prevent gaining extra privilege |
| Capabilities | Fine-grained Linux privileges |
| readOnlyRootFilesystem | Root filesystem cannot be written |
| Pod Security | Control unsafe Pod configurations |
| Least privilege | Give only what is required |
| `kubectl auth can-i` | Fast RBAC verification |
| 403 Forbidden | Usually authorization/RBAC issue |
| Permission denied | Often UID/GID/filesystem issue |

## Most important commands

```bash
# ServiceAccounts
kubectl get sa
kubectl describe sa <sa> -n <ns>

# RBAC objects
kubectl get role -A
kubectl get rolebinding -A
kubectl get clusterrole
kubectl get clusterrolebinding

# Permission check
kubectl auth can-i get pods -n <ns>
kubectl auth can-i delete pods -n <ns>

# Check as ServiceAccount
kubectl auth can-i get pods \
  --as=system:serviceaccount:<ns>:<sa> \
  -n <ns>

# List permissions
kubectl auth can-i --list \
  --as=system:serviceaccount:<ns>:<sa> \
  -n <ns>

# Pod security details
kubectl get pod <pod> -o yaml
kubectl describe pod <pod>

# Container identity
kubectl exec -it <pod> -- id

# Filesystem permissions
kubectl exec -it <pod> -- ls -ld /path

# Events
kubectl get events --sort-by=.lastTimestamp
```

## Final mental model

```text
WHO?
  -> ServiceAccount

WHAT CAN THEY DO?
  -> RBAC
     -> Role + RoleBinding
     -> ClusterRole + ClusterRoleBinding

HOW DOES THE CONTAINER RUN?
  -> SecurityContext
     -> non-root
     -> UID/GID
     -> fsGroup
     -> no privilege escalation
     -> drop capabilities
     -> read-only filesystem

WHAT POD CONFIGURATION IS ALLOWED?
  -> Pod Security Admission

PRODUCTION
  -> Least privilege
  -> NetworkPolicy
  -> Secret protection
  -> Monitoring/auditing
  -> Cloud workload identity
```
