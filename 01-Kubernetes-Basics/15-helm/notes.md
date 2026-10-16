# Helm – Notes

## 1. What is Helm?

Helm is a package manager and templating/release-management tool for Kubernetes.

It helps us:
- Package Kubernetes manifests into reusable Charts.
- Parameterize YAML using values.
- Deploy the same application differently across DEV/TEST/PROD.
- Manage releases, upgrades, and rollbacks.

### Core model

```text
Chart       = Package
values.yaml = Configuration
Template    = Kubernetes YAML with variables
Release     = Installed instance
Revision    = Release history
```

---

## 2. Helm Chart Structure

Created with:

```bash
helm create nginx-demo
```

Typical structure:

```text
nginx-demo/
├── Chart.yaml
├── values.yaml
├── charts/
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── serviceaccount.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── tests/
│   └── _helpers.tpl
└── .helmignore
```

### Chart.yaml

```yaml
apiVersion: v2
name: nginx-demo
type: application
version: 0.1.0
appVersion: "1.16.0"
```

- `version` = Helm chart version.
- `appVersion` = application version.

Important:

```text
Chart version != Application version != Release revision
```

---

## 3. values.yaml

`values.yaml` contains default configuration.

```yaml
replicaCount: 3

image:
  repository: nginx
  tag: "1.16.0"

service:
  type: ClusterIP
  port: 80
```

Template:

```yaml
replicas: {{ .Values.replicaCount }}
```

Rendered result:

```yaml
replicas: 3
```

Flow:

```text
values.yaml → .Values → template → Kubernetes manifest
```

---

## 4. Helm Templates

Example:

```yaml
image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

With:

```yaml
repository: nginx
tag: "1.16.0"
```

Helm renders:

```yaml
image: "nginx:1.16.0"
```

---

## 5. helm template

Render a chart without installing:

```bash
helm template nginx-demo ./nginx-demo
```

- `helm` = CLI
- `template` = render/preview
- `nginx-demo` = release name used for rendering
- `./nginx-demo` = chart directory

Use it to inspect the exact Kubernetes YAML Helm will generate.

```text
helm template = render only
helm install   = render + install
```

---

## 6. helm lint

Validate a chart:

```bash
helm lint ./nginx-demo
```

Typical success:

```text
1 chart(s) linted, 0 chart(s) failed
```

Use before deployment or committing chart changes.

---

## 7. Helm Install

```bash
helm install nginx-demo ./nginx-demo -n helm-lab
```

Check:

```bash
helm list -n helm-lab
kubectl get all -n helm-lab
helm status nginx-demo -n helm-lab
```

---

## 8. Helm Upgrade

```bash
helm upgrade nginx-demo ./nginx-demo -n helm-lab
```

An upgrade creates a new release revision.

Example:

```text
Revision 1 → Install
Revision 2 → Upgrade
```

---

## 9. Release Revision and Rollback

Check history:

```bash
helm history nginx-demo -n helm-lab
```

Rollback:

```bash
helm rollback nginx-demo 2 -n helm-lab
```

Important: rollback creates a NEW revision.

```text
1 → Install
2 → Upgrade
3 → Bad Upgrade
4 → Rollback to 2
```

Revision 4 is deployed.

---

## 10. Environment Values Files

### values-dev.yaml

```yaml
replicaCount: 1

image:
  repository: nginx
  tag: "1.16.0"

service:
  type: ClusterIP
  port: 80
```

### values-test.yaml

```yaml
replicaCount: 2

image:
  repository: nginx
  tag: "1.16.0"

service:
  type: ClusterIP
  port: 80
```

### values-prod.yaml

```yaml
replicaCount: 3

image:
  repository: nginx
  tag: "1.16.0"

service:
  type: LoadBalancer
  port: 80
```

Render:

```bash
helm template nginx-demo ./nginx-demo -f nginx-demo/values-dev.yaml
helm template nginx-demo ./nginx-demo -f nginx-demo/values-test.yaml
helm template nginx-demo ./nginx-demo -f nginx-demo/values-prod.yaml
```

Concept:

```text
Same chart
   ↓
Different values
   ↓
Different Kubernetes manifests
```

---

## 11. -f / --values and --set

`-f` supplies an override values file:

```bash
helm template nginx-demo ./nginx-demo   -f nginx-demo/values-dev.yaml
```

`--set` overrides directly:

```bash
helm upgrade nginx-demo ./nginx-demo   -n helm-lab   --set replicaCount=5
```

Simplified precedence:

```text
values.yaml
    <
-f first-values.yaml
    <
-f second-values.yaml
    <
--set
```

For repeatable environment configuration, values files are usually easier to maintain.

---

## 12. if / else

Conditional rendering:

```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
...
{{- end }}
```

If enabled is true, the resource is rendered. If false, it is not rendered.

Use case:

```text
DEV  → ingress disabled
PROD → ingress enabled
```

---

## 13. range

Loops through a list.

Values:

```yaml
allowedHosts:
  - app.example.com
  - api.example.com
```

Template:

```yaml
hosts:
{{- range .Values.allowedHosts }}
  - {{ . }}
{{- end }}
```

Inside `range`, `.` represents the current item.

---

## 14. with

Works with a nested object.

```yaml
{{- with .Values.image }}
image: "{{ .repository }}:{{ .tag }}"
{{- end }}
```

Inside `with`:

```text
. = .Values.image
```

---

## 15. default

Provides a fallback:

```yaml
image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
```

If the tag is empty and:

```yaml
appVersion: "1.16.0"
```

the rendered image becomes:

```yaml
image: "nginx:1.16.0"
```

---

## 16. _helpers.tpl, define, include, nindent

Reusable helper:

```yaml
{{- define "nginx-demo.fullname" -}}
{{ .Release.Name }}-{{ .Chart.Name }}
{{- end }}
```

Use it:

```yaml
metadata:
  name: {{ include "nginx-demo.fullname" . }}
```

- `define` creates a named template.
- `include` renders it.
- `.` passes the current Helm context.
- `_helpers.tpl` is for reusable template logic and is not itself a Kubernetes resource.
- `nindent` is commonly used to preserve YAML indentation:

```yaml
labels:
  {{- include "nginx-demo.labels" . | nindent 2 }}
```

---

## 17. ConfigMaps with Helm

ConfigMap is for non-sensitive configuration.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_MODE: {{ .Values.appMode | quote }}
```

Pod consumption:

```yaml
envFrom:
  - configMapRef:
      name: app-config
```

Use cases:
- Application mode
- URLs
- Feature flags
- Non-sensitive settings

Do not store passwords in ConfigMaps.

---

## 18. Secrets with Helm

Example:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  DB_PASSWORD: {{ .Values.dbPassword | b64enc | quote }}
```

Important:

```text
Base64 = encoding
Base64 != encryption
```

Do not put real production credentials into Git-managed values files.

Production pattern can be:

```text
AWS Secrets Manager
        ↓
External Secrets / secret integration
        ↓
Kubernetes Secret
        ↓
Application
```

---

## 19. Same Chart, Multiple Releases

A chart can have multiple installed instances:

```bash
helm install nginx-dev ./nginx-demo   -n helm-lab   -f nginx-demo/values-dev.yaml
```

Another:

```bash
helm install nginx-test ./nginx-demo   -n helm-lab   -f nginx-demo/values-test.yaml
```

Concept:

```text
              nginx-demo Chart
                /                         /                    nginx-dev        nginx-test
        1 replica         2 replicas
```

Chart = package; Release = installed instance.

---

## 20. Deliberate Failure: Invalid Image

Set:

```yaml
image:
  tag: "does-not-exist"
```

Render:

```bash
helm template nginx-demo ./nginx-demo | grep -n "image:"
```

Helm can render it because the template is valid.

Kubernetes can then fail with:

```text
ErrImagePull
ImagePullBackOff
```

Key lesson:

```text
Helm rendering success ≠ application deployment success
```

---

## 21. Practical Helm Workflow

```text
Modify chart
    ↓
helm lint
    ↓
helm template
    ↓
Review rendered YAML
    ↓
helm install / helm upgrade
    ↓
kubectl verify
    ↓
helm status
    ↓
If bad → helm history
    ↓
helm rollback
```

---

## 22. Real-World Use Cases

### DEV/TEST/PROD
Same chart, different replica counts, image tags, service types, ingress settings, and resource settings.

### Standard application deployment
Package an application once and deploy it consistently.

### Safe upgrades
Revision history enables recovery after bad releases.

### Reusable platform components
Package NGINX, monitoring agents, applications, or internal services.

### CI/CD
Typical pipeline:

```text
Git
 ↓
helm lint
 ↓
helm template
 ↓
helm upgrade --install
 ↓
kubectl verification
```

---

# Interview Q&A

### Q1. What is Helm?
Helm is a Kubernetes package manager and templating/release-management tool.

### Q2. What is a Chart?
A reusable package containing Kubernetes templates, values, metadata, and optionally dependencies.

### Q3. Chart vs Release?
Chart = package. Release = installed instance of the chart.

### Q4. What is values.yaml?
Default configurable values used by chart templates.

### Q5. What does helm template do?
Renders manifests locally without installing resources.

### Q6. Why use helm template?
To inspect the exact manifests before changing the cluster.

### Q7. What does -f do?
Supplies an additional values file that overrides defaults.

### Q8. What is --set?
A command-line value override.

### Q9. Which has higher precedence: values.yaml or --set?
`--set`.

### Q10. What happens during helm upgrade?
The existing release is updated and a new revision is created.

### Q11. What is helm history?
Release revision history.

### Q12. Does rollback reactivate the old revision number?
No. Rollback creates a new revision using the selected revision's configuration.

### Q13. What is _helpers.tpl?
A file for reusable named templates such as common names and labels.

### Q14. ConfigMap vs Secret?
ConfigMap is for non-sensitive configuration; Secret is intended for sensitive data.

### Q15. Is Base64 encryption?
No. Base64 is encoding.

### Q16. Can one chart have multiple releases?
Yes.

### Q17. What if Helm renders successfully but the image does not exist?
Kubernetes can show `ErrImagePull` or `ImagePullBackOff`.

### Q18. Helm vs kubectl?
Helm manages packaged applications and releases; kubectl directly interacts with Kubernetes resources and is heavily used for inspection/troubleshooting.

### Q19. Chart version vs appVersion?
`version` identifies the Helm chart; `appVersion` identifies the application.

### Q20. How would you troubleshoot a failed Helm deployment?
Check `helm status`, `helm history`, `helm get values`, `helm get manifest`, then `kubectl get pods`, `describe`, events, and logs. Determine whether the issue is Helm configuration/rendering or Kubernetes/application runtime.

---

# Cheat Sheet

```text
CREATE
helm create mychart

VALIDATE
helm lint ./mychart

RENDER
helm template myrelease ./mychart

RENDER WITH VALUES
helm template myrelease ./mychart -f values-dev.yaml

INSTALL
helm install myrelease ./mychart -n mynamespace

INSTALL/UPGRADE
helm upgrade --install myrelease ./mychart -n mynamespace

LIST
helm list -n mynamespace

STATUS
helm status myrelease -n mynamespace

HISTORY
helm history myrelease -n mynamespace

UPGRADE
helm upgrade myrelease ./mychart -n mynamespace

ROLLBACK
helm rollback myrelease <revision> -n mynamespace

MANIFEST
helm get manifest myrelease -n mynamespace

VALUES
helm get values myrelease -n mynamespace

UNINSTALL
helm uninstall myrelease -n mynamespace

OVERRIDE
--set replicaCount=5

VALUES FILE
-f values-prod.yaml
```

## One-Minute Interview Summary

> Helm is a package manager and release-management tool for Kubernetes. I use Charts to package reusable Kubernetes templates and values.yaml to parameterize them. Environment-specific values files allow the same chart to be deployed differently in DEV, TEST, and PROD. I use `helm lint` and `helm template` before deployment, `helm install` for initial deployment, `helm upgrade` for changes, `helm history` for revisions, and `helm rollback` for recovery. Helm manages application packaging and release lifecycle, while kubectl is commonly used for Kubernetes inspection and troubleshooting.
