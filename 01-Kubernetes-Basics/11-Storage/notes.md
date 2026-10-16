# Kubernetes Storage — Notes & Interview Q&A

## 1. Why Kubernetes Storage?

Container writable filesystems are temporary. Important application data should use persistent storage.

```text
Pod/Container
    ↓
Container filesystem
    ↓
Pod/container recreated
    ↓
Data may be lost
```

Kubernetes storage options provide different lifetimes and persistence.

---

## 2. Container Filesystem

**Definition:** Writable filesystem available inside a container.

Example:

```bash
echo "hello" > /tmp/data.txt
```

**Use:** Temporary files, scratch data, cache.

**Key point:** Container filesystem = temporary.

---

## 3. emptyDir

**Definition:** Temporary volume created for a Pod.

```yaml
volumes:
  - name: temporary-storage
    emptyDir: {}
```

Lifecycle:

```text
Pod created → emptyDir created
Container restart → emptyDir remains
Pod deleted → emptyDir deleted
```

**Use cases:** Temporary processing, cache, scratch space, sharing temporary files between containers in one Pod.

**Key point:** `emptyDir` survives container restarts but not Pod deletion.

---

## 4. hostPath

**Definition:** Mounts a directory from the Kubernetes node into a Pod.

```yaml
volumes:
  - name: host-storage
    hostPath:
      path: /data/k8s-hostpath
      type: DirectoryOrCreate
```

```text
Node
└── /data/k8s-hostpath
          ↑
       mounted
          ↓
Pod
└── /data
```

**Advantages:** Simple; data can survive Pod recreation if it returns to the same node.

**Problems:** Node-dependent, not portable, and generally not preferred for normal production application persistence.

**Key point:** `hostPath` = node filesystem.

---

## 5. PersistentVolume (PV)

**Definition:** A Kubernetes storage resource representing persistent storage available to workloads.

Important fields:

- `capacity`
- `accessModes`
- `persistentVolumeReclaimPolicy`
- `storageClassName`
- storage backend/source

**Mental model:**

> PV = storage resource available to Kubernetes.

---

## 6. PersistentVolumeClaim (PVC)

**Definition:** An application's request for persistent storage.

Example:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: demo-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
  storageClassName: manual
```

**Mental model:**

```text
PV  = storage available
PVC = storage requested
```

---

## 7. Pod → PVC → PV

A Pod normally uses a PVC:

```yaml
volumes:
  - name: persistent-storage
    persistentVolumeClaim:
      claimName: demo-pvc
```

Flow:

```text
Pod
 ↓
PVC
 ↓
PV
 ↓
Storage backend
```

The application requests storage through the PVC.

---

## 8. PV/PVC Binding

A PVC becomes `Bound` when Kubernetes successfully associates it with suitable storage.

Example:

```text
demo-pvc → Bound → demo-pv
```

Matching can involve:

- Storage size
- Access mode
- StorageClass
- Other volume requirements

---

## 9. Access Modes

### RWO — ReadWriteOnce

Read/write mount from a single node.

Common with block storage such as EBS.

### ROX — ReadOnlyMany

Read-only mounting from multiple nodes.

### RWX — ReadWriteMany

Read/write mounting from multiple nodes.

**Important:** Exact behavior depends on the storage implementation.

---

## 10. Reclaim Policies

### Retain

```text
PVC deleted
    ↓
PV → Released
    ↓
Underlying data remains
```

Useful when protecting data or requiring manual cleanup/recovery.

### Delete

```text
PVC deleted
    ↓
PV deleted
    ↓
Provisioned storage cleaned up
```

Memory trick:

```text
Retain = Keep
Delete  = Clean
```

---

## 11. PVC Protection

Kubernetes protects a PVC that is actively being used.

If a Pod is still using a PVC and you run:

```bash
kubectl delete pvc dynamic-pvc
```

the PVC can remain:

```text
Terminating
```

Typical finalizer:

```text
kubernetes.io/pvc-protection
```

After the consuming Pod is removed, deletion can complete.

**Key point:** PVC protection helps prevent unsafe deletion while a Pod is using the claim.

---

## 12. StorageClass

**Definition:** A StorageClass defines a class/blueprint for dynamically provisioning storage.

Important concepts:

- Provisioner
- Reclaim policy
- Volume binding mode
- Parameters
- Volume expansion

Example in our Minikube lab:

```text
standard
Provisioner: k8s.io/minikube-hostpath
```

---

## 13. Dynamic Provisioning

Without dynamic provisioning:

```text
Admin → creates PV
Application → creates PVC
PVC → binds to PV
```

With dynamic provisioning:

```text
Application
 ↓
PVC
 ↓
StorageClass
 ↓
Provisioner
 ↓
PV automatically created
 ↓
PVC becomes Bound
```

In our lab, we created only `dynamic-pvc`; Minikube automatically created its PV.

---

## 14. StorageClass + Dynamic Provisioning

```text
PVC
"I need 1Gi"
    ↓
StorageClass
    ↓
Provisioner
    ↓
Dynamic PV
    ↓
Storage Backend
```

### EKS mapping

EBS:

```text
PVC
 ↓
StorageClass
 ↓
EBS CSI Driver
 ↓
Amazon EBS
```

EFS:

```text
PVC
 ↓
StorageClass
 ↓
EFS CSI Driver
 ↓
Amazon EFS
```

---

## 15. Volume Binding Mode

### Immediate

Provisioning/binding can happen as soon as the PVC is created.

### WaitForFirstConsumer

Provisioning waits until a Pod using the PVC is scheduled. This helps topology-aware storage decisions.

Useful for topology-sensitive storage such as zonal block storage.

```text
Immediate
PVC → provision now

WaitForFirstConsumer
PVC → Pod scheduled → choose suitable topology → provision
```

---

# 16. StatefulSet

**Definition:** StatefulSet manages stateful applications that need stable Pod identity and persistent storage association.

Typical examples:

- PostgreSQL
- MySQL
- MongoDB
- Kafka
- ZooKeeper
- Elasticsearch

### Deployment vs StatefulSet

```text
Deployment
→ Pods are generally interchangeable
→ generated names

StatefulSet
→ stable identity
→ app-0
→ app-1
→ app-2
```

---

## 17. StatefulSet Stable Identity

For:

```yaml
replicas: 3
```

a StatefulSet named `stateful-demo` creates:

```text
stateful-demo-0
stateful-demo-1
stateful-demo-2
```

If `stateful-demo-1` is deleted, Kubernetes recreates:

```text
stateful-demo-1
```

not a random identity.

---

## 18. StatefulSet volumeClaimTemplates

One of the most important storage concepts.

```yaml
volumeClaimTemplates:
  - metadata:
      name: app-data
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 1Gi
      storageClassName: standard
```

With 3 replicas:

```text
stateful-demo-0 → app-data-stateful-demo-0
stateful-demo-1 → app-data-stateful-demo-1
stateful-demo-2 → app-data-stateful-demo-2
```

Each Pod gets its own PVC.

**Important:** StatefulSet does NOT mean all Pods share one PVC.

---

## 19. StatefulSet Storage Architecture

```text
                 StatefulSet
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Pod-0        Pod-1        Pod-2
          │           │           │
          ▼           ▼           ▼
       PVC-0        PVC-1        PVC-2
          │           │           │
          ▼           ▼           ▼
        PV-0         PV-1         PV-2
          │           │           │
          └───────────┼───────────┘
                      ▼
              Storage Backend
```

---

## 20. StatefulSet Pod Deletion

We deleted:

```text
stateful-demo-1
```

Kubernetes recreated the same identity.

The existing PVC remained and the data:

```text
DATA FROM POD 1
```

was available again.

Flow:

```text
Pod deleted
    ↓
PVC remains
    ↓
PV remains
    ↓
Data remains
    ↓
Same Pod identity recreated
    ↓
Existing PVC mounted
```

---

## 21. StatefulSet Scaling

We tested:

```text
3 → 5
```

New Pods:

```text
stateful-demo-3
stateful-demo-4
```

New PVCs:

```text
app-data-stateful-demo-3
app-data-stateful-demo-4
```

Then:

```text
5 → 2
```

Higher ordinal Pods were removed:

```text
stateful-demo-4
stateful-demo-3
stateful-demo-2
```

But their PVCs remained.

Then:

```text
2 → 5
```

The higher ordinal Pods were recreated and their existing PVCs were reused.

**Key point:** Scaling down a StatefulSet removes Pods but, by default, does not automatically delete their PVCs.

---

## 22. StatefulSet vs Deployment

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod identity | Interchangeable | Stable |
| Pod names | Generated | Ordered/stable |
| Stable network identity | Not inherent | Supported |
| Per-Pod PVC | Not automatic | `volumeClaimTemplates` |
| Typical use | Stateless APIs/web | Databases/stateful systems |
| Storage association | Application-specific | Strong Pod/PVC association |

---

## 23. Complete Storage Lifecycle

```text
PVC created
    ↓
StorageClass selected
    ↓
Provisioner provisions storage
    ↓
PV created
    ↓
PVC ↔ PV Bound
    ↓
Pod mounts PVC
    ↓
Application writes data
    ↓
Pod deleted/recreated
    ↓
PVC/PV can remain
    ↓
Data remains
```

PVC deletion:

```text
Retain → PV Released → data remains

Delete → PV/storage cleaned up
```

---

# 24. Container FS vs emptyDir vs hostPath vs PV/PVC

| Storage | Survives container restart | Survives Pod deletion | Persistent application storage |
|---|---:|---:|---:|
| Container filesystem | Usually no | No | No |
| emptyDir | Yes | No | No |
| hostPath | Yes | Yes, if same node | Not generally recommended |
| PV/PVC | Yes | Yes | Yes |

---

# 25. EKS Storage Mental Model

### EBS

```text
Pod
 ↓
PVC
 ↓
StorageClass
 ↓
EBS CSI Driver
 ↓
EBS Volume
```

### EFS

```text
Pod
 ↓
PVC
 ↓
StorageClass
 ↓
EFS CSI Driver
 ↓
EFS
```

---

# 26. Interview Q&A

### Q1. Why do we need persistent storage in Kubernetes?

Because container filesystems are temporary and application data may be lost when containers/Pods are recreated. Persistent storage keeps important data outside the ephemeral container filesystem.

### Q2. What is emptyDir?

A temporary volume created for a Pod. It survives container restarts but is deleted when the Pod is deleted.

### Q3. What is hostPath?

A volume that mounts a directory from the Kubernetes node into a Pod. It is node-dependent.

### Q4. What is a PersistentVolume?

A Kubernetes resource representing persistent storage available to workloads.

### Q5. What is a PVC?

An application's request for persistent storage.

### Q6. PV vs PVC?

PV represents the storage resource; PVC represents the application's request.

```text
PV  = supply
PVC = demand
```

### Q7. Does a Pod directly create a PV?

Normally the application creates a PVC. The PVC either binds to an existing PV or triggers dynamic provisioning through a StorageClass.

### Q8. What is StorageClass?

A definition of a class of storage and the provisioning mechanism used to create storage dynamically.

### Q9. What is dynamic provisioning?

Automatic creation of suitable storage/PV when a PVC requests storage through a StorageClass.

### Q10. What does Bound mean?

The PVC has successfully been associated with a PV.

### Q11. What does Pending mean for a PVC?

Kubernetes has not yet found or provisioned suitable storage.

### Q12. What is RWO?

ReadWriteOnce. The volume can be mounted read/write by a single node.

### Q13. What is RWX?

ReadWriteMany. The storage implementation supports read/write mounting from multiple nodes.

### Q14. Retain vs Delete?

`Retain` preserves the PV/data for manual handling. `Delete` allows dynamically provisioned storage to be cleaned up when the claim is deleted, according to the provisioner's behavior.

### Q15. Why can a PVC be stuck in Terminating?

A Pod may still be using it. PVC protection can prevent unsafe deletion.

### Q16. What is StatefulSet?

A workload controller for stateful applications needing stable identity and persistent storage association.

### Q17. Deployment vs StatefulSet?

Deployment is generally for interchangeable stateless Pods. StatefulSet provides stable identities and storage association for stateful workloads.

### Q18. What happens when a StatefulSet Pod is deleted?

The controller recreates the same ordinal identity.

### Q19. Does deleting a StatefulSet Pod delete its PVC?

Normally no. The PVC remains and can be mounted by the replacement Pod.

### Q20. What is volumeClaimTemplates?

A StatefulSet mechanism that automatically creates a separate PVC for each StatefulSet Pod.

### Q21. Does StatefulSet mean all Pods share one volume?

No. With `volumeClaimTemplates`, each Pod gets its own PVC.

### Q22. What happens when StatefulSet scales 3 → 5?

New higher-ordinal Pods are created and corresponding PVCs are created when using `volumeClaimTemplates`.

### Q23. What happens when it scales 5 → 2?

Higher ordinal Pods are removed first. Their PVCs are normally retained.

### Q24. What happens when it scales 2 → 5 again?

The higher ordinal Pods are recreated and their existing PVCs can be reused.

### Q25. Does StatefulSet automatically replicate database data?

No. StatefulSet provides stable identity and storage association. Database replication and failover are application/database responsibilities.

### Q26. Why is StatefulSet useful for PostgreSQL?

It can provide predictable Pod identity and stable PVC association. It does not configure PostgreSQL replication by itself.

### Q27. What is PVC protection?

A mechanism that helps prevent deletion of a PVC while it is still being used by a Pod.

### Q28. What is WaitForFirstConsumer?

It delays storage provisioning/binding until a Pod using the PVC is scheduled, helping topology-aware storage decisions.

### Q29. What is the EKS storage flow with EBS?

```text
PVC → StorageClass → EBS CSI Driver → EBS
```

### Q30. What is the EKS storage flow with EFS?

```text
PVC → StorageClass → EFS CSI Driver → EFS
```

### Q31. How would you troubleshoot a PVC Pending issue?

Check:

```bash
kubectl get pvc
kubectl describe pvc <pvc>
kubectl get pv
kubectl get storageclass
kubectl describe storageclass <storageclass>
kubectl get events --sort-by=.lastTimestamp
```

Look for missing storage, wrong StorageClass, provisioner/CSI issues, access mode mismatch, capacity, or topology problems.

### Q32. How would you troubleshoot a Pod unable to mount a volume?

Start with:

```bash
kubectl describe pod <pod>
kubectl describe pvc <pvc>
kubectl describe pv <pv>
kubectl get events --sort-by=.lastTimestamp
```

Then inspect the CSI driver/backend in EKS.

### Q33. How would you troubleshoot data disappearing?

Identify the storage type first:

```text
Container filesystem → temporary
emptyDir → Pod lifetime
hostPath → node-dependent
PVC/PV → persistent
```

Then verify the actual volume mount and PVC/PV relationship.

---

# 27. One-Minute Interview Explanation

> Kubernetes provides different storage options depending on the required persistence. Container filesystems are temporary, while emptyDir survives container restarts for the lifetime of the Pod. hostPath uses node-local storage but is node-dependent. For persistent application data, Kubernetes uses PersistentVolumes and PersistentVolumeClaims. A PVC represents the application's storage request, while a PV represents the storage resource. StorageClasses enable dynamic provisioning so a PVC can automatically trigger storage creation. Reclaim policies such as Retain and Delete control what happens after PVC deletion. For stateful workloads such as databases, StatefulSet provides stable Pod identity and, using volumeClaimTemplates, a dedicated PVC per Pod.

---

# 28. Final Storage Memory Map

```text
Container FS → temporary

emptyDir → Pod lifetime

hostPath → node filesystem

PV → storage resource

PVC → storage request

StorageClass → provisioning definition

Dynamic Provisioning → PVC automatically gets storage

Retain → keep storage

Delete → clean provisioned storage

StatefulSet → stable identity + persistent storage association

volumeClaimTemplates → one PVC per StatefulSet Pod
```
