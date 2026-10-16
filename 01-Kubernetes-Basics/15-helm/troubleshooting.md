# Helm – Troubleshooting

## 1. Troubleshooting Model

Separate problems into:

```text
Helm layer
- Chart
- Templates
- Values
- Release

Kubernetes/application layer
- Scheduling
- Images
- Pods
- Probes
- Services
- Application runtime
```

A successful Helm command does not always mean the application is healthy.

---

## 2. First Commands

```bash
helm status <release> -n <namespace>
helm history <release> -n <namespace>
helm get values <release> -n <namespace>
helm get manifest <release> -n <namespace>

kubectl get all -n <namespace>
kubectl get pods -n <namespace>
kubectl describe pod <pod> -n <namespace>
kubectl logs <pod> -n <namespace>
```

---

## 3. helm lint Fails

```bash
helm lint ./nginx-demo
```

Check:
1. Exact error.
2. Referenced template.
3. YAML indentation.
4. Values names.
5. Template syntax.

Rerun lint after fixing.

---

## 4. helm template Fails

```bash
helm template nginx-demo ./nginx-demo --debug
```

Possible causes:
- Invalid Go template syntax.
- Missing/wrong values.
- Bad indentation.
- Incorrect `if`, `range`, `with`, `define`.
- Wrong helper name.

Fix rendering before troubleshooting the cluster.

---

## 5. Values File Not Taking Effect

Problem:

```yaml
replicaCount: 1
```

but output is:

```yaml
replicas: 3
```

Check:

```bash
cat values-dev.yaml

helm template nginx-demo ./nginx-demo   -f values-dev.yaml | grep "replicas:"
```

Common causes:
- Forgot `-f`.
- Wrong path.
- Wrong key.
- Another values file overrides it.
- `--set` overrides it.
- Template references a different value.

Precedence:

```text
values.yaml
   <
-f first.yaml
   <
-f second.yaml
   <
--set
```

---

## 6. Wrong Environment Configuration

Example:

```text
Expected DEV:
1 replica + ClusterIP

Actual:
3 replicas + LoadBalancer
```

Render the exact environment values before deployment:

```bash
helm template nginx-dev ./nginx-demo   -f values-dev.yaml
```

Then inspect:

```bash
helm template nginx-dev ./nginx-demo   -f values-dev.yaml | grep -E "replicas:|type:"
```

---

## 7. Release Not Found

```bash
helm status nginx-demo -n helm-lab
```

If not found:

```bash
helm list -A
helm list -n helm-lab
```

Common cause: release exists in another namespace.

---

## 8. Upgrade Fails

```bash
helm status nginx-demo -n helm-lab
helm history nginx-demo -n helm-lab

kubectl get pods -n helm-lab
kubectl describe pod <pod> -n helm-lab
kubectl get events -n helm-lab --sort-by=.lastTimestamp
```

Also render:

```bash
helm template nginx-demo ./nginx-demo
```

Ask:

```text
Did Helm fail to render?
OR
Did Kubernetes fail to run the rendered resources?
```

---

## 9. ErrImagePull / ImagePullBackOff

Check:

```bash
kubectl get pods -n helm-lab
kubectl describe pod <pod> -n helm-lab
```

Common causes:
- Wrong repository.
- Wrong tag.
- Private registry authentication missing.
- Image does not exist.
- Registry problem.

Example bad value:

```yaml
image:
  repository: nginx
  tag: "does-not-exist"
```

Helm may render successfully:

```yaml
image: "nginx:does-not-exist"
```

Kubernetes then fails to pull it.

Fix the tag and upgrade:

```bash
helm upgrade nginx-demo ./nginx-demo -n helm-lab
kubectl get pods -n helm-lab
```

---

## 10. CrashLoopBackOff

Check:

```bash
kubectl get pods -n <namespace>
kubectl describe pod <pod> -n <namespace>
kubectl logs <pod> -n <namespace>
kubectl logs <pod> -n <namespace> --previous
```

Possible causes:
- Application startup failure.
- Incorrect environment variable.
- Missing ConfigMap/Secret.
- Wrong command/arguments.
- Dependency failure.

---

## 11. ConfigMap Problem

Check:

```bash
kubectl get configmap -n <namespace>
kubectl describe configmap <name> -n <namespace>
kubectl get deployment <name> -n <namespace> -o yaml
```

Look for:

```yaml
envFrom:
  - configMapRef:
      name: app-config
```

or:

```yaml
env:
  - name: APP_MODE
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: APP_MODE
```

Then check application logs.

---

## 12. Secret Problem

Check:

```bash
kubectl get secret -n <namespace>
kubectl describe secret <name> -n <namespace>
```

Remember:

```text
Base64 is encoding, not encryption.
```

Do not expose production credentials in Git or terminal output.

---

## 13. Service Has No Endpoints

Check:

```bash
kubectl get svc -n <namespace>
kubectl describe svc <service> -n <namespace>
kubectl get endpoints -n <namespace>
kubectl get endpointslice -n <namespace>
kubectl get pods --show-labels -n <namespace>
```

Common root cause:

```text
Service selector != Pod labels
```

---

## 14. Bad Release → Rollback

Example:

```text
1 → Install
2 → Upgrade
3 → Bad Upgrade
```

Check:

```bash
helm history nginx-demo -n helm-lab
```

Rollback:

```bash
helm rollback nginx-demo 2 -n helm-lab
```

Verify:

```bash
helm history nginx-demo -n helm-lab
kubectl get pods -n helm-lab
kubectl get deployment -n helm-lab
```

Remember: rollback creates revision 4; revision 2 is not renamed/reused.

---

## 15. kubectl history Confusion

Wrong:

```bash
kubectl history
```

Correct:

```bash
helm history nginx-demo -n helm-lab
```

Use:

```text
helm history → Helm release history
kubectl       → Kubernetes resource inspection
```

---

## 16. Resource Not Rendered

If a resource is missing:

```bash
helm get manifest <release> -n <namespace>
```

Then render directly:

```bash
helm template <release> ./chart -f values.yaml
```

Possible cause:

```yaml
{{- if .Values.ingress.enabled }}
...
{{- end }}
```

If:

```yaml
ingress:
  enabled: false
```

the resource is intentionally not rendered.

---

## 17. Helper Template Error

Check:

```text
templates/_helpers.tpl
```

Make sure:

```yaml
{{- define "nginx-demo.name" -}}
...
{{- end }}
```

matches:

```yaml
{{ include "nginx-demo.name" . }}
```

Helper names must match exactly.

---

## 18. YAML Indentation Problem

Render with:

```bash
helm template nginx-demo ./nginx-demo --debug
```

Inspect rendered YAML.

With helpers, `nindent` is often useful:

```yaml
labels:
  {{- include "nginx-demo.labels" . | nindent 2 }}
```

Golden rule:

```text
Troubleshoot the rendered YAML, not only the template source.
```

---

## 19. Upgrade Succeeds but Pods Are Not Ready

Check:

```bash
kubectl rollout status deployment/<deployment> -n <namespace>
kubectl get pods -n <namespace>
kubectl describe pod <pod> -n <namespace>
kubectl logs <pod> -n <namespace>
```

Possible causes:
- Readiness probe failure.
- Liveness/startup probe failure.
- Application startup issue.
- Image issue.
- Resource constraints.
- Missing configuration.
- Dependency failure.

---

## 20. Recommended Debugging Order

```text
1. helm status
       ↓
2. helm history
       ↓
3. helm get values
       ↓
4. helm get manifest
       ↓
5. kubectl get pods
       ↓
6. kubectl describe pod
       ↓
7. kubectl get events
       ↓
8. kubectl logs
       ↓
9. Service / ConfigMap / Secret checks
       ↓
10. Root cause
       ↓
11. Fix
       ↓
12. Verify
```

---

## 21. Production Incident Example

Scenario:

A production Helm upgrade changes an image tag.

Symptoms:

```text
helm upgrade → completed
Pods → ImagePullBackOff
```

### Step 1

```bash
helm status ecommerce -n production
```

### Step 2

```bash
helm history ecommerce -n production
```

### Step 3

```bash
kubectl get pods -n production
```

### Step 4

```bash
kubectl describe pod <pod> -n production
```

### Step 5

Find event such as:

```text
Failed to pull image
```

### Root cause

The configured image tag does not exist in the registry.

### Resolution

Correct the tag and upgrade, or for immediate recovery:

```bash
helm rollback ecommerce <known-good-revision> -n production
```

### Verify

```bash
kubectl rollout status deployment/<deployment> -n production
kubectl get pods -n production
helm status ecommerce -n production
```

---

# Troubleshooting Interview Q&A

### Q1. Helm deployment succeeded but application is down. What do you do?

Check `helm status` and `helm history`, inspect the released manifest, then inspect Pods, events, descriptions, and logs. Determine whether the problem is image, configuration, scheduling, probe, networking, or application runtime. Roll back to a known-good revision if immediate recovery is required.

### Q2. Helm template works but Pod is ImagePullBackOff. Why?

The rendered Kubernetes YAML can be valid while the referenced image/tag is unavailable or inaccessible.

### Q3. DEV values are not being applied. What do you check?

Check the `-f` path, key names, multiple values-file order, `--set`, and the template reference. Confirm using `helm template`.

### Q4. A resource is missing after installation. What do you check?

Check `helm get manifest`, then render with `helm template` and inspect conditional blocks such as `if`.

### Q5. Service exists but traffic does not reach Pods. What do you check?

Check Service selectors, Pod labels, endpoints/EndpointSlices, Pod readiness, and application listening port.

---

# Root-Cause Matrix

| Symptom | Likely area |
|---|---|
| `helm lint` fails | Chart/template |
| `helm template` fails | Template/values |
| Wrong replicas | Values/override |
| Resource not rendered | Conditional values |
| `ErrImagePull` | Image/registry |
| `CrashLoopBackOff` | Application/config |
| Pod Pending | Scheduling/resources |
| Readiness failure | Application/probe |
| Service has no endpoints | Labels/selectors |
| Secret missing | Configuration |
| Bad upgrade | Release/config |
| Immediate recovery required | Rollback |

---

# Golden Rules

1. Run `helm lint`.
2. Run `helm template` before deployment.
3. Never assume Helm success means application health.
4. Check Pods and rollout after deployment.
5. Use `helm history` for release history.
6. Rollback creates a new revision.
7. Use values files for repeatable environments.
8. Never commit real production secrets to Git.
9. Base64 is not encryption.
10. Troubleshoot rendered YAML plus Kubernetes runtime state.
