# Kubernetes Storage — Troubleshooting

## 1. PVC stuck in Pending

### Symptom

```bash
kubectl get pvc
```

shows:

```text
STATUS   Pending
```

### Check

```bash
kubectl describe pvc <pvc-name>
kubectl get pv
kubectl get storageclass
kubectl get events --sort-by=.lastTimestamp
```

### Common causes

- No matching PV.
- Wrong/missing StorageClass.
- Dynamic provisioner unavailable.
- Unsupported access mode.
- Insufficient capacity.
- Storage topology issue.
- CSI driver problem.

---

## 2. PVC stuck in Terminating

### Symptom

```text
dynamic-pvc   Terminating
```

### Common cause

A Pod is still using the PVC.

### Check

```bash
kubectl describe pvc <pvc-name>
kubectl get pods
```

Look for `Used By`.

### Why?

PVC protection can prevent unsafe deletion.

Typical finalizer:

```text
kubernetes.io/pvc-protection
```

### Resolution

If appropriate, remove the consuming Pod:

```bash
kubectl delete pod <pod-name>
```

Then:

```bash
kubectl get pvc
```

### Lab example

`dynamic-pvc` stayed `Terminating` while `dynamic-pvc-demo` was using it. After deleting the Pod, the PVC disappeared automatically.

---

## 3. PVC is Bound but Pod cannot start

Check:

```bash
kubectl describe pod <pod-name>
kubectl describe pvc <pvc-name>
kubectl describe pv <pv-name>
kubectl get events --sort-by=.lastTimestamp
```

Possible causes:

- Volume mount failure.
- CSI driver issue.
- Access mode conflict.
- Node/topology problem.
- Backend storage problem.
- Permissions/mount issue.

---

## 4. Pod cannot mount PVC

Use:

```bash
kubectl describe pod <pod-name>
kubectl describe pvc <pvc-name>
kubectl describe pv <pv-name>
kubectl get events --sort-by=.lastTimestamp
```

In EKS also investigate the relevant CSI driver:

```text
EBS CSI Driver
EFS CSI Driver
```

---

## 5. Data disappeared after Pod deletion

Identify the storage type:

```text
Container filesystem → temporary
emptyDir → deleted with Pod
hostPath → may survive if same node/path
PVC → normally survives Pod deletion
```

Verify the Pod's actual volume configuration:

```bash
kubectl describe pod <pod-name>
```

Check `Volumes` and `Mounts`.

---

## 6. Data disappeared after container restart

If using `emptyDir`, data should normally survive a container restart within the same Pod.

Check:

```bash
kubectl describe pod <pod-name>
```

Make sure the application writes to the mounted path.

Example:

```text
Mounted path: /data
Application writes: /tmp/file.txt
```

The `/tmp` file is not stored in the persistent volume.

---

## 7. hostPath data missing after Pod moves

### Root cause

`hostPath` is node-local.

```text
Node-1 → /data/application → data exists

Pod moves to Node-2
                  ↓
          different filesystem
```

### Resolution

Use an appropriate persistent storage backend instead of relying on node-local paths for portable application data.

---

## 8. StatefulSet Pod recreated but data is missing

For:

```text
stateful-demo-1
```

verify:

```bash
kubectl get pvc
kubectl describe pvc app-data-stateful-demo-1
kubectl describe pod stateful-demo-1
kubectl get pv
```

Expected relationship:

```text
stateful-demo-1
       ↓
app-data-stateful-demo-1
       ↓
PV
       ↓
Persistent storage
```

---

## 9. StatefulSet scaled down but PVCs remain

This is normally expected.

Example:

```text
5 replicas → 2 replicas
```

Pods `2`, `3`, `4` are removed, but their PVCs can remain.

Check:

```bash
kubectl get pvc
```

The PVCs are retained to protect state.

---

## 10. StatefulSet scaled back up

For:

```text
5 → 2 → 5
```

the higher ordinal Pods are recreated and their existing PVCs can be reused.

Check:

```bash
kubectl get pods
kubectl get pvc
```

Then verify data if test data was stored:

```bash
kubectl exec stateful-demo-2 -- cat /data/identity.txt
```

---

## 11. StorageClass not found

Check:

```bash
kubectl get storageclass
```

If a PVC contains:

```yaml
storageClassName: my-storage
```

but `my-storage` does not exist, dynamic provisioning cannot work through that class.

---

## 12. Dynamic provisioning not working

Check:

```bash
kubectl get pvc
kubectl describe pvc <pvc>
kubectl get storageclass
kubectl describe storageclass <storageclass>
kubectl get pv
kubectl get events --sort-by=.lastTimestamp
```

Common causes:

- Incorrect StorageClass.
- Provisioner unavailable.
- CSI driver missing/broken.
- Invalid storage parameters.
- Topology constraints.
- Cloud IAM/permissions.
- Capacity or availability problem.

---

## 13. Wrong access mode

If a PVC requests an access mode unsupported by the storage backend, provisioning or mounting can fail.

Check:

```bash
kubectl describe pvc <pvc>
kubectl get storageclass
```

Conceptually:

```text
EBS → commonly RWO
EFS → supports shared filesystem patterns such as RWX
```

Always verify the actual CSI/storage implementation.

---

## 14. PV is Released

### Symptom

```bash
kubectl get pv
```

shows:

```text
Released
```

### Meaning

The PV was previously bound to a PVC, but that claim was deleted.

If the reclaim policy is:

```text
Retain
```

the underlying data remains.

A `Released` PV is not automatically the same as a fresh `Available` PV. Manual cleanup/reclaim may be required before reuse.

---

## 15. PV disappeared after PVC deletion

Check:

```bash
kubectl describe pv <pv-name>
```

If:

```text
Reclaim Policy: Delete
```

the PV and dynamically provisioned storage may be cleaned up after the PVC is deleted.

This is expected.

---

## 16. Storage remains after PVC deletion

Check:

```bash
kubectl describe pv <pv-name>
```

If:

```text
Reclaim Policy: Retain
```

storage/data is intentionally retained for manual recovery or cleanup.

---

## 17. RWO mounting problem

RWO is a node-level access constraint. If a workload requires shared mounting across nodes, verify whether the storage backend supports the required access pattern.

Check:

```bash
kubectl describe pod <pod-name>
kubectl describe pvc <pvc-name>
kubectl describe pv <pv-name>
kubectl get events --sort-by=.lastTimestamp
```

In EKS understand:

```text
EBS
Availability Zone
Node
Pod
EBS CSI Driver
```

---

# 18. General Storage Troubleshooting Sequence

Use this order:

```bash
kubectl get pvc
kubectl describe pvc <pvc>
kubectl get pv
kubectl describe pv <pv>
kubectl get storageclass
kubectl describe storageclass <storageclass>
kubectl describe pod <pod>
kubectl get events --sort-by=.lastTimestamp
```

Then classify the problem:

```text
PVC problem?
   ↓
PV problem?
   ↓
StorageClass/provisioner problem?
   ↓
Pod mount problem?
   ↓
CSI/backend/cloud problem?
```

---

# 19. StatefulSet Troubleshooting Sequence

```bash
kubectl get statefulset
kubectl describe statefulset <name>

kubectl get pods
kubectl get pvc

kubectl describe pod <pod>
kubectl describe pvc <pvc>

kubectl get pv
kubectl get events --sort-by=.lastTimestamp
```

Verify:

```text
Pod identity
    ↓
PVC identity
    ↓
PV identity
    ↓
Storage backend
```

---

# 20. Production Warnings

### Don't use hostPath for normal application persistence

It is node-dependent.

### Don't delete PVCs casually

PVC deletion can cause permanent data loss depending on reclaim policy and backend.

### Understand reclaim policy

```text
Retain → preserve storage/data
Delete  → provisioned storage may be removed
```

### StatefulSet is not database replication

StatefulSet provides identity/storage association. Database replication and failover remain application/database responsibilities.

### Persistent storage is not backup

A persistent volume protects against some Pod/container lifecycle events, but it is not a replacement for backups, snapshots, replication, or disaster recovery.

---

# 21. Quick Troubleshooting Cheat Sheet

| Symptom | First checks |
|---|---|
| PVC Pending | `describe pvc`, StorageClass, PV, events |
| PVC Terminating | Pod using PVC, PVC protection |
| Pod mount failure | `describe pod`, PVC, PV, events |
| Data disappeared | Storage type + mount path + PVC |
| hostPath data missing | Node placement |
| StatefulSet data missing | Pod → PVC → PV relationship |
| PV Released | Reclaim policy and previous claim |
| Dynamic provisioning failed | StorageClass + provisioner/CSI |
| Wrong access mode | PVC + backend capabilities |
| StatefulSet scale-down | Pods removed, PVCs normally retained |

---

# 22. Strong Interview Troubleshooting Answer

> "For a Kubernetes storage issue, I first check the PVC status using `kubectl get pvc` and `kubectl describe pvc`. Then I verify the associated PV and reclaim policy. Next I check the StorageClass and provisioner, followed by the Pod's volume mounts and Events. If I'm on EKS, I also verify the relevant CSI driver and the underlying AWS storage resource. I troubleshoot from PVC → PV → StorageClass/CSI → Pod mount → cloud backend rather than changing resources blindly."

---

# 23. Final Checklist

- Container filesystem
- emptyDir
- hostPath
- PersistentVolume
- PersistentVolumeClaim
- PV/PVC binding
- RWO / ROX / RWX
- Retain / Delete
- PVC protection
- StorageClass
- Dynamic provisioning
- Immediate
- WaitForFirstConsumer
- StatefulSet
- Stable Pod identity
- volumeClaimTemplates
- Per-Pod PVCs
- StatefulSet Pod deletion/recreation
- StatefulSet scaling
- PVC retention during scale-down
- EKS EBS/EFS conceptual mapping
- Storage troubleshooting
# Kubernetes Storage — Troubleshooting

## 1. PVC stuck in Pending

### Symptom

```bash
kubectl get pvc
```

shows:

```text
STATUS   Pending
```

### Check

```bash
kubectl describe pvc <pvc-name>
kubectl get pv
kubectl get storageclass
kubectl get events --sort-by=.lastTimestamp
```

### Common causes

- No matching PV.
- Wrong/missing StorageClass.
- Dynamic provisioner unavailable.
- Unsupported access mode.
- Insufficient capacity.
- Storage topology issue.
- CSI driver problem.

---

## 2. PVC stuck in Terminating

### Symptom

```text
dynamic-pvc   Terminating
```

### Common cause

A Pod is still using the PVC.

### Check

```bash
kubectl describe pvc <pvc-name>
kubectl get pods
```

Look for `Used By`.

### Why?

PVC protection can prevent unsafe deletion.

Typical finalizer:

```text
kubernetes.io/pvc-protection
```

### Resolution

If appropriate, remove the consuming Pod:

```bash
kubectl delete pod <pod-name>
```

Then:

```bash
kubectl get pvc
```

### Lab example

`dynamic-pvc` stayed `Terminating` while `dynamic-pvc-demo` was using it. After deleting the Pod, the PVC disappeared automatically.

---

## 3. PVC is Bound but Pod cannot start

Check:

```bash
kubectl describe pod <pod-name>
kubectl describe pvc <pvc-name>
kubectl describe pv <pv-name>
kubectl get events --sort-by=.lastTimestamp
```

Possible causes:

- Volume mount failure.
- CSI driver issue.
- Access mode conflict.
- Node/topology problem.
- Backend storage problem.
- Permissions/mount issue.

---

## 4. Pod cannot mount PVC

Use:

```bash
kubectl describe pod <pod-name>
kubectl describe pvc <pvc-name>
kubectl describe pv <pv-name>
kubectl get events --sort-by=.lastTimestamp
```

In EKS also investigate the relevant CSI driver:

```text
EBS CSI Driver
EFS CSI Driver
```

---

## 5. Data disappeared after Pod deletion

Identify the storage type:

```text
Container filesystem → temporary
emptyDir → deleted with Pod
hostPath → may survive if same node/path
PVC → normally survives Pod deletion
```

Verify the Pod's actual volume configuration:

```bash
kubectl describe pod <pod-name>
```

Check `Volumes` and `Mounts`.

---

## 6. Data disappeared after container restart

If using `emptyDir`, data should normally survive a container restart within the same Pod.

Check:

```bash
kubectl describe pod <pod-name>
```

Make sure the application writes to the mounted path.

Example:

```text
Mounted path: /data
Application writes: /tmp/file.txt
```

The `/tmp` file is not stored in the persistent volume.

---

## 7. hostPath data missing after Pod moves

### Root cause

`hostPath` is node-local.

```text
Node-1 → /data/application → data exists

Pod moves to Node-2
                  ↓
          different filesystem
```

### Resolution

Use an appropriate persistent storage backend instead of relying on node-local paths for portable application data.

---

## 8. StatefulSet Pod recreated but data is missing

For:

```text
stateful-demo-1
```

verify:

```bash
kubectl get pvc
kubectl describe pvc app-data-stateful-demo-1
kubectl describe pod stateful-demo-1
kubectl get pv
```

Expected relationship:

```text
stateful-demo-1
       ↓
app-data-stateful-demo-1
       ↓
PV
       ↓
Persistent storage
```

---

## 9. StatefulSet scaled down but PVCs remain

This is normally expected.

Example:

```text
5 replicas → 2 replicas
```

Pods `2`, `3`, `4` are removed, but their PVCs can remain.

Check:

```bash
kubectl get pvc
```

The PVCs are retained to protect state.

---

## 10. StatefulSet scaled back up

For:

```text
5 → 2 → 5
```

the higher ordinal Pods are recreated and their existing PVCs can be reused.

Check:

```bash
kubectl get pods
kubectl get pvc
```

Then verify data if test data was stored:

```bash
kubectl exec stateful-demo-2 -- cat /data/identity.txt
```

---

## 11. StorageClass not found

Check:

```bash
kubectl get storageclass
```

If a PVC contains:

```yaml
storageClassName: my-storage
```

but `my-storage` does not exist, dynamic provisioning cannot work through that class.

---

## 12. Dynamic provisioning not working

Check:

```bash
kubectl get pvc
kubectl describe pvc <pvc>
kubectl get storageclass
kubectl describe storageclass <storageclass>
kubectl get pv
kubectl get events --sort-by=.lastTimestamp
```

Common causes:

- Incorrect StorageClass.
- Provisioner unavailable.
- CSI driver missing/broken.
- Invalid storage parameters.
- Topology constraints.
- Cloud IAM/permissions.
- Capacity or availability problem.

---

## 13. Wrong access mode

If a PVC requests an access mode unsupported by the storage backend, provisioning or mounting can fail.

Check:

```bash
kubectl describe pvc <pvc>
kubectl get storageclass
```

Conceptually:

```text
EBS → commonly RWO
EFS → supports shared filesystem patterns such as RWX
```

Always verify the actual CSI/storage implementation.

---

## 14. PV is Released

### Symptom

```bash
kubectl get pv
```

shows:

```text
Released
```

### Meaning

The PV was previously bound to a PVC, but that claim was deleted.

If the reclaim policy is:

```text
Retain
```

the underlying data remains.

A `Released` PV is not automatically the same as a fresh `Available` PV. Manual cleanup/reclaim may be required before reuse.

---

## 15. PV disappeared after PVC deletion

Check:

```bash
kubectl describe pv <pv-name>
```

If:

```text
Reclaim Policy: Delete
```

the PV and dynamically provisioned storage may be cleaned up after the PVC is deleted.

This is expected.

---

## 16. Storage remains after PVC deletion

Check:

```bash
kubectl describe pv <pv-name>
```

If:

```text
Reclaim Policy: Retain
```

storage/data is intentionally retained for manual recovery or cleanup.

---

## 17. RWO mounting problem

RWO is a node-level access constraint. If a workload requires shared mounting across nodes, verify whether the storage backend supports the required access pattern.

Check:

```bash
kubectl describe pod <pod-name>
kubectl describe pvc <pvc-name>
kubectl describe pv <pv-name>
kubectl get events --sort-by=.lastTimestamp
```

In EKS understand:

```text
EBS
Availability Zone
Node
Pod
EBS CSI Driver
```

---

# 18. General Storage Troubleshooting Sequence

Use this order:

```bash
kubectl get pvc
kubectl describe pvc <pvc>
kubectl get pv
kubectl describe pv <pv>
kubectl get storageclass
kubectl describe storageclass <storageclass>
kubectl describe pod <pod>
kubectl get events --sort-by=.lastTimestamp
```

Then classify the problem:

```text
PVC problem?
   ↓
PV problem?
   ↓
StorageClass/provisioner problem?
   ↓
Pod mount problem?
   ↓
CSI/backend/cloud problem?
```

---

# 19. StatefulSet Troubleshooting Sequence

```bash
kubectl get statefulset
kubectl describe statefulset <name>

kubectl get pods
kubectl get pvc

kubectl describe pod <pod>
kubectl describe pvc <pvc>

kubectl get pv
kubectl get events --sort-by=.lastTimestamp
```

Verify:

```text
Pod identity
    ↓
PVC identity
    ↓
PV identity
    ↓
Storage backend
```

---

# 20. Production Warnings

### Don't use hostPath for normal application persistence

It is node-dependent.

### Don't delete PVCs casually

PVC deletion can cause permanent data loss depending on reclaim policy and backend.

### Understand reclaim policy

```text
Retain → preserve storage/data
Delete  → provisioned storage may be removed
```

### StatefulSet is not database replication

StatefulSet provides identity/storage association. Database replication and failover remain application/database responsibilities.

### Persistent storage is not backup

A persistent volume protects against some Pod/container lifecycle events, but it is not a replacement for backups, snapshots, replication, or disaster recovery.

---

# 21. Quick Troubleshooting Cheat Sheet

| Symptom | First checks |
|---|---|
| PVC Pending | `describe pvc`, StorageClass, PV, events |
| PVC Terminating | Pod using PVC, PVC protection |
| Pod mount failure | `describe pod`, PVC, PV, events |
| Data disappeared | Storage type + mount path + PVC |
| hostPath data missing | Node placement |
| StatefulSet data missing | Pod → PVC → PV relationship |
| PV Released | Reclaim policy and previous claim |
| Dynamic provisioning failed | StorageClass + provisioner/CSI |
| Wrong access mode | PVC + backend capabilities |
| StatefulSet scale-down | Pods removed, PVCs normally retained |

---

# 22. Strong Interview Troubleshooting Answer

> "For a Kubernetes storage issue, I first check the PVC status using `kubectl get pvc` and `kubectl describe pvc`. Then I verify the associated PV and reclaim policy. Next I check the StorageClass and provisioner, followed by the Pod's volume mounts and Events. If I'm on EKS, I also verify the relevant CSI driver and the underlying AWS storage resource. I troubleshoot from PVC → PV → StorageClass/CSI → Pod mount → cloud backend rather than changing resources blindly."

---

# 23. Final Checklist

- Container filesystem
- emptyDir
- hostPath
- PersistentVolume
- PersistentVolumeClaim
- PV/PVC binding
- RWO / ROX / RWX
- Retain / Delete
- PVC protection
- StorageClass
- Dynamic provisioning
- Immediate
- WaitForFirstConsumer
- StatefulSet
- Stable Pod identity
- volumeClaimTemplates
- Per-Pod PVCs
- StatefulSet Pod deletion/recreation
- StatefulSet scaling
- PVC retention during scale-down
- EKS EBS/EFS conceptual mapping
- Storage troubleshooting
