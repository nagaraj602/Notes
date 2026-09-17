# Complete Kubernetes Reference & Hands-On Engineering Guide

---

## Table of Contents
1. [Introduction to Container Orchestration & Docker Swarm vs. Kubernetes](#1-introduction-to-container-orchestration--docker-swarm-vs-kubernetes)
2. [Cluster Hardware Sizing, Prerequisites & System Preparation](#2-cluster-hardware-sizing-prerequisites--system-preparation)
3. [Cluster Initialization & Pod Networking (CNI)](#3-cluster-initialization--pod-networking-cni)
4. [Kubernetes Architecture Deep Dive](#4-kubernetes-architecture-deep-dive)
5. [etcd Key-Value Store: Quorum Math, High Availability & Disaster Recovery](#5-etcd-key-value-store-quorum-math-high-availability--disaster-recovery)
6. [Kubernetes Pods: Lifecycle, Restart Policies & Troubleshooting](#6-kubernetes-pods-lifecycle-restart-policies--troubleshooting)
7. [API Versioning, Resource Groups, Labels & Selectors](#7-api-versioning-resource-groups-labels--selectors)
8. [ReplicaSet Controller: Desired State, Self-Healing & Pod Adoption](#8-replicaset-controller-desired-state-self-healing--pod-adoption)
9. [Deployment Controller & Zero-Downtime Rolling Updates](#9-deployment-controller--zero-downtime-rolling-updates)
10. [DaemonSet Controller & Node Daemon Architecture](#10-daemonset-controller--node-daemon-architecture)
11. [Kubernetes Services & Networking Abstractions](#11-kubernetes-services--networking-abstractions)
12. [StatefulSet Controller & Headless Services](#12-statefulset-controller--headless-services)
13. [Headless Service DNS Discovery Deep Dive](#13-headless-service-dns-discovery-deep-dive)
14. [Storage Management: Volumes, HostPath, EmptyDir, PV, PVC & StorageClasses](#14-storage-management-volumes-hostpath-emptydir-pv-pvc--storageclasses)
15. [Namespaces, ResourceQuotas & Compute Resource Management](#15-namespaces-resourcequotas--compute-resource-management)
16. [Configuration Management: Environment Variables, ConfigMaps & Secrets](#16-configuration-management-environment-variables-configmaps--secrets)
17. [Cluster Security & Role-Based Access Control (RBAC)](#17-cluster-security--role-based-access-control-rbac)
18. [Advanced Pod Scheduling: Affinities, Anti-Affinities, Taints & Tolerations](#18-advanced-pod-scheduling-affinities-anti-affinities-taints--tolerations)
19. [Application Health Checks: Startup, Liveness & Readiness Probes](#19-application-health-checks-startup-liveness--readiness-probes)
20. [Helm: Kubernetes Package Management & Release Lifecycle](#20-helm-kubernetes-package-management--release-lifecycle)
21. [Kubernetes Monitoring & Observability: Prometheus, Grafana & Exporters](#21-kubernetes-monitoring--observability-prometheus-grafana--exporters)
22. [Production Monitoring Infrastructure: 2-VM Architecture](#22-production-monitoring-infrastructure-2-vm-architecture)
23. [AWS EKS Architecture: Provisioning, Access Patterns, Ingress & Add-ons](#23-aws-eks-architecture-provisioning-access-patterns-ingress--add-ons)
24. [Advanced Kubernetes Engineering Modules](#24-advanced-kubernetes-engineering-modules)
    - [24.1 Horizontal Pod Autoscaler (HPA)](#241-horizontal-pod-autoscaler-hpa)
    - [24.2 Ingress & AWS Load Balancer Controller](#242-ingress--aws-load-balancer-controller)
    - [24.3 Kubernetes Gateway API](#243-kubernetes-gateway-api)
    - [24.4 Advanced Helm Templating & Best Practices](#244-advanced-helm-templating--best-practices)
    - [24.5 Batch Processing: Jobs and CronJobs](#245-batch-processing-jobs-and-cronjobs)
    - [24.6 Network Policies & Micro-segmentation](#246-network-policies--micro-segmentation)
    - [24.7 Admission Controllers & Kyverno Policy Engine](#247-admission-controllers--kyverno-policy-engine)
    - [24.8 Pod Security Standards (PSS) & Pod Security Admission (PSA)](#248-pod-security-standards-pss--pod-security-admission-psa)
    - [24.9 Declarative Configuration with Kustomize](#249-declarative-configuration-with-kustomize)
    - [24.10 Container Storage Interface (CSI) Architecture](#2410-container-storage-interface-csi-architecture)
    - [24.11 Secrets Store CSI Driver (Vault / AWS Secrets Manager)](#2411-secrets-store-csi-driver-vault--aws-secrets-manager)
25. [Assignments](#25-assignments)

---

## 1. Introduction to Container Orchestration & Docker Swarm vs. Kubernetes

### 1.1 The Need for Container Orchestration
In a traditional computing environment, applications were deployed directly onto physical hardware or virtual machines (VMs). With the rise of microservices, applications are broken down into hundreds of independently deployable containerized components. While Docker solves the problem of packaging applications and their dependencies uniformly, managing containers at scale across multiple physical or cloud virtual servers introduces substantial operational challenges:

1. **Host-Level Failures**: If a physical server hosting 50 Docker containers crashes, how are those containers immediately resurrected on healthy machines?
2. **Dynamic Scaling**: How do we seamlessly scale application replicas up during peak traffic spikes and scale them down during off-peak hours without manual intervention?
3. **Service Discovery & Load Balancing**: How do microservices discover each other's dynamically assigned IP addresses, and how is network traffic evenly distributed across all running replicas?
4. **Zero-Downtime Deployments**: How do we roll out updates and roll back failed releases without dropping active user connections?
5. **Storage Orchestration**: How do stateful services retain and re-attach their persistent data volumes when containers are rescheduled across different host machines?

Container orchestration automates the provisioning, deployment, networking, scaling, health monitoring, and lifecycle management of containerized workloads across a distributed cluster of nodes.

### 1.2 What is Kubernetes?
**Kubernetes** (often abbreviated as **K8s**, representing the 8 letters between 'K' and 's') is an open-source, enterprise-grade container orchestration engine originally designed by Google based on over a decade and a half of production experience with its internal cluster management system, Borg. Today, Kubernetes is maintained by the Cloud Native Computing Foundation (CNCF).

Kubernetes automates:
- **Service discovery and load balancing**: Exposes containers via a stable IP and DNS name, distributing traffic evenly.
- **Storage orchestration**: Automatically mounts local storage, public cloud storage (AWS EBS, GCP Persistent Disk, Azure Disk), or network storage (NFS, Ceph, AWS EFS).
- **Automated rollouts and rollbacks**: Declaratively updates application versions, monitors health, and rolls back if failures occur.
- **Automatic bin packing**: Allocates CPU and memory resources to maximize node efficiency without sacrificing application performance.
- **Self-healing**: Kills containers that fail health checks, reschedules pods when nodes die, and replaces unresponsive instances.
- **Secret and configuration management**: Stores sensitive credentials, API keys, and environment configs securely outside container images.

### 1.3 Docker Swarm vs. Kubernetes Detailed Comparison

| Evaluation Metric | Docker Swarm | Kubernetes (K8s) |
| :--- | :--- | :--- |
| **Origin & Backing** | Docker Inc. | Google / CNCF (Cloud Native Computing Foundation) |
| **Setup & Learning Curve** | Extremely simple, native to Docker CLI (`docker swarm init`). Minimal learning curve. | Steep learning curve, requires understanding distributed systems, CNI, CSI, and complex manifests. |
| **Architecture Scale** | Best suited for small-to-medium clusters (up to ~1,000 nodes / 30,000 containers). | Built for hyperscale production environments (5,000+ nodes, 300,000+ containers per cluster). |
| **Auto-scaling** | Limited native capability. Requires external scripting or third-party add-ons. | Built-in Horizontal Pod Autoscaler (HPA), Vertical Pod Autoscaler (VPA), and Cluster Autoscaler. |
| **Load Balancing** | Built-in ingress routing mesh (Layer 4 load balancing). | Highly flexible via kube-proxy, Ingress Controllers (Layer 7 routing), and Gateway API. |
| **High Availability & Healing**| Basic service re-balancing on node outage. | Sophisticated reconciliation loops, self-healing, pod disruption budgets, and multi-zone spreading. |
| **Extensibility & Ecosystem**| Rigid, limited plugin ecosystem. | Limitless extensibility via Custom Resource Definitions (CRDs), Operators, Admission Webhooks, and Helm. |
| **Industry Adoption** | Declining, mostly used in legacy setups or simple internal developer tools. | Global industry standard for cloud-native infrastructure across all public and private clouds. |

---

## 2. Cluster Hardware Sizing, Prerequisites & System Preparation

### 2.1 Node Hardware Sizing Guidelines
A Kubernetes cluster consists of two types of servers:
1. **Control Plane (Master) Nodes**: Manage and orchestrate the cluster.
2. **Worker Nodes**: Run user applications and background daemons.

#### Sizing Recommendations
- **Lab & Learning Environment**:
  - **Master Node**: 1 VM instance with at least **2 vCPUs** and **4 GB RAM** (e.g., AWS EC2 `t2.medium` / `t3.medium`). *Kubernetes pre-flight checks strictly enforce a minimum of 2 vCPUs on the control plane.*
  - **Worker Nodes**: 2 or more VM instances with **1–2 vCPUs** and **1–2 GB RAM** (e.g., AWS EC2 `t2.micro` or `t3.small`).
- **Production Environment**:
  - **Master Nodes**: Minimum of 3 Control Plane nodes for High Availability (HA) quorum, each with **4–8 vCPUs**, **16–32 GB RAM**, and fast SSD storage for `etcd` disk I/O.
  - **Worker Nodes**: Sized according to workload footprint (e.g., compute-optimized `c5.2xlarge` or memory-optimized `r5.2xlarge`).

### 2.2 System Prerequisites & OS Configuration
All nodes (Master and Workers) must run a modern Linux kernel (e.g., Ubuntu 22.04 LTS or 24.04 LTS). Before installing Kubernetes packages, several critical OS-level configurations must be applied.

#### 1. Disabling Swap Memory
Kubernetes requires swap memory to be completely disabled. The Kubernetes memory model assumes full control over memory allocation; allowing memory to page to swap disk breaks the kubelet's resource accounting, degrades performance, and causes unpredictability in container eviction thresholds.

Execute on **all nodes**:
```bash
# Disable swap immediately for current session
sudo swapoff -a

# Permanently disable swap across system reboots
sudo sed -i '/swap/d' /etc/fstab
```

#### 2. Enabling Required Kernel Modules
Kubernetes container networking relies on bridge netfilter and overlay filesystems:
```bash
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter
```

#### 3. Configuring Sysctl Parameters for Packet Forwarding
Linux bridges must pass IPv4 traffic to iptables chains so that `kube-proxy` and Container Network Interface (CNI) plugins can correctly route packet filters:
```bash
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

# Apply sysctl parameters without rebooting
sudo sysctl --system
```

### 2.3 Container Runtime Interface (CRI) Setup: containerd
Kubernetes interacts with container runtimes via the Container Runtime Interface (CRI). As of Kubernetes version 1.24, the legacy `dockershim` was deprecated and removed. Modern Kubernetes clusters use native CRI runtimes, primarily **containerd**.

Execute on **all nodes**:
```bash
# Install containerd from official package repositories
sudo apt update
sudo apt install -y containerd

# Generate default configuration file
sudo mkdir -p /etc/containerd
sudo containerd config default | sudo tee /etc/containerd/config.toml

# Configure containerd to use systemd as the cgroup driver
# This ensures cgroup management is unified between systemd and the kubelet
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml

# Restart and enable containerd service
sudo systemctl restart containerd
sudo systemctl enable containerd
```

### 2.4 Installing Kubernetes Toolchain (`kubelet`, `kubeadm`, `kubectl`)
The core Kubernetes administration packages must be installed across all machines:
- **`kubelet`**: The node agent running on every machine in the cluster. It ensures containers described in PodSpecs are running and healthy.
- **`kubeadm`**: The official bootstrap tool used to initialize the cluster control plane and join worker nodes.
- **`kubectl`**: The command-line utility used by administrators and CI/CD pipelines to communicate with the cluster's API server.

Execute on **all nodes**:
```bash
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gpg

# Download Kubernetes official package signing key
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.36/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# Add Kubernetes official repository
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.36/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install packages
sudo apt update
sudo apt install -y kubelet kubeadm kubectl

# Pin package versions to prevent unintended auto-upgrades
sudo apt-mark hold kubelet kubeadm kubectl
```

#### Multi-Node Provisioning via AWS AMI
After configuring the base instance with containerd, kubelet, kubeadm, and kubectl, create an Amazon Machine Image (AMI) from the master instance:
1. In the AWS EC2 Console, select the configured master instance.
2. Click **Actions** -> **Image and templates** -> **Create image**.
3. Once the AMI status transitions to **Available** (typically 2–8 minutes), launch 2 additional EC2 instances (`t2.medium` or `t2.micro` worker nodes) using this AMI. This eliminates repetitive package installation across all worker nodes.

![][image1]

---

## 3. Cluster Initialization & Pod Networking (CNI)

### 3.1 Initializing the Control Plane with `kubeadm init`
The master node control plane components are initialized using `kubeadm init`. When specifying a CNI like Calico, the Pod Network CIDR must be explicitly defined.

Execute strictly on the **Master Node**:
```bash
sudo kubeadm init --pod-network-cidr=192.168.0.0/16
```

![][image2]

Upon successful initialization, the output provides critical operational commands:
1. **Setting up regular user access (`kubeconfig`)**:
```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```
2. **Worker Node Join Command**:
```bash
sudo kubeadm join <MASTER_IP>:6443 --token <TOKEN> \
    --discovery-token-ca-cert-hash sha256:<HASH>
```

> [!NOTE]
> The bootstrap token generated by `kubeadm init` is valid for **24 hours**. If adding new worker nodes after token expiration, generate a fresh join command on the master node:
> ```bash
> kubeadm token create --print-join-command
> ```

### 3.2 Installing the Calico Container Network Interface (CNI)
Initially, running `kubectl get nodes` shows the master node in a `NotReady` state:
```bash
kubectl get nodes
# NAME          STATUS     ROLES           AGE   VERSION
# k8s-master    NotReady   control-plane   2m    v1.36.0
```

![][image4]
This is expected because Kubernetes does not bundle a default network plugin. Pod-to-pod networking across nodes requires a CNI plugin. **Calico** is an enterprise CNI providing Layer 3 routing and network policy enforcement.

Install Calico on the **Master Node**:
```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml
```

![][image3]

Wait 60–90 seconds and verify the node status changes to `Ready`:
```bash
kubectl get nodes
# NAME          STATUS   ROLES           AGE   VERSION
# k8s-master    Ready    control-plane   4m    v1.36.0
```

### 3.3 Joining Worker Nodes to the Cluster
On each **Worker Node**, execute the `kubeadm join` command generated during master initialization:
```bash
sudo kubeadm join 172.31.21.247:6443 --token 46m78l.ehm773uh1vmihbub \
    --discovery-token-ca-cert-hash sha256:653a2b38ec519ea5272ff45846c55cd5b1b6de56788c1654a105baf4469f3be6
```

Back on the **Master Node**, verify all nodes are registered and healthy:
```bash
kubectl get nodes -o wide
```

---

## 4. Kubernetes Architecture Deep Dive

A Kubernetes cluster is divided into two distinct architectural planes:
1. **Control Plane (Master)**: Manages cluster state, takes scheduling decisions, and detects/responds to cluster events.
2. **Data Plane (Worker Nodes)**: Executes user container workloads.

![][image5]

### 4.1 Control Plane Components

#### 1. `kube-apiserver` (The Cluster Brain)
The API server is the front-end gatekeeper of the control plane. It exposes the Kubernetes REST API over HTTPS on port 6443.
- **Functions**:
  - Authenticates and authorizes all incoming requests (from users, external systems, and worker nodes).
  - Validates and configures data for API objects (Pods, Services, Deployments, etc.).
  - Executes Mutating and Validating Admission Webhooks.
  - Acts as the **exclusive intermediary** to `etcd`; no other component is allowed to read or write to `etcd` directly.

#### 2. `etcd` (The Source of Truth)
`etcd` is a strongly consistent, highly-available, distributed key-value store.
- Stores the complete, authoritative state and configuration of the entire cluster.
- Uses the **Raft consensus algorithm** to maintain data integrity across distributed replicas.
- Never runs workloads or applications; strictly holds cluster metadata.

#### 3. `kube-scheduler` (The Placement Engine)
The scheduler is responsible for watching for newly created Pods that have no node assigned and assigning them to an optimal node.
- **Two-Step Decision Process**:
  1. **Filtering (Predicates)**: Discards nodes that cannot meet the pod's requirements (insufficient CPU/memory, missing volume mounts, taints that the pod cannot tolerate, node selector mismatches).
  2. **Scoring (Priorities)**: Ranks remaining candidate nodes based on resource balance, image locality (node already has the container image pulled), and affinity/anti-affinity rules to pick the best host.

#### 4. `kube-controller-manager` (The Reconciliation Loop)
The controller manager bundles multiple core control loops into a single binary. Each controller continuously compares the **current state** of the cluster with the **desired state** specified in manifests and drives changes toward reconciliation:
- **Node Controller**: Detects when nodes go offline and initiates pod evictions.
- **ReplicaSet Controller**: Ensures the exact desired count of pod instances is maintained.
- **EndpointSlice / Endpoints Controller**: Populates endpoints linking Services to healthy Pod IPs.
- **ServiceAccount Controller**: Creates default accounts and API access tokens for new namespaces.

#### 5. `cloud-controller-manager` (Cloud Provider Bridge)
Runs controllers that interact directly with the underlying cloud platform (AWS, Azure, GCP):
- Provisions cloud load balancers (AWS NLB/ALB) when a Service of type `LoadBalancer` is created.
- Initializes cloud storage volumes (AWS EBS) when PersistentVolumeClaims are requested.
- Checks cloud provider APIs to verify if a stopped node has been terminated in the cloud.

---

### 4.2 Worker Node Components

#### 1. `kubelet` (The Primary Node Agent)
An agent running on every node in the cluster.
- Registers the worker node with the `kube-apiserver`.
- Receives PodSpecs from the API server and instructs the container runtime (via CRI) to start, stop, and monitor containers.
- Executes container health checks (Startup, Liveness, and Readiness Probes).
- Collects node resource telemetry and sends periodic heartbeats (Node Leases) back to the control plane.

#### 2. `kube-proxy` (The Network Router)
Maintains network rules on each worker node to implement the Kubernetes `Service` abstraction.
- Runs in `iptables` or `IPVS` mode.
- Translates virtual ClusterIP addresses and NodePorts into backend Pod IP addresses, providing Layer 4 round-robin load balancing.

#### 3. Container Runtime
The underlying software responsible for pulling container images, configuring namespaces/cgroups, and running container processes (e.g., `containerd`, `CRI-O`).

#### 4. Cluster Add-ons
- **CoreDNS**: In-cluster DNS server that provides service name resolution (e.g., `my-service.my-namespace.svc.cluster.local`).
- **Metrics Server**: Collects container CPU/memory usage metrics required by `kubectl top` and HPA.
- **Network Plugin (Calico/Flannel)**: Manages pod overlay networks and inter-node routing.

---

## 5. etcd Key-Value Store: Quorum Math, High Availability & Disaster Recovery

### 5.1 The Raft Consensus Algorithm & Quorum Math
Because `etcd` stores the entire state of the cluster, control plane high availability depends on running multiple `etcd` members across separate machines. In distributed systems, maintaining consensus across independent nodes requires a **Quorum**.

The Quorum is the minimum number of nodes that must be online, communicating, and agreeing before any read or write transaction can be committed.

$$\text{Quorum} = \left\lfloor \frac{N}{2} \right\rfloor + 1$$

Where $N$ is the total number of members in the `etcd` cluster.

The maximum number of simultaneous node failures the cluster can tolerate without going offline is:

$$\text{Fault Tolerance } (F) = \frac{N - 1}{2}$$

#### Quorum and Fault Tolerance Table
| Total Nodes ($N$) | Quorum Required | Failure Tolerance ($F$) | Recommendation / Risk Analysis |
| :---: | :---: | :---: | :--- |
| **1** | 1 | 0 | Single point of failure. Common in labs, unsuitable for production. |
| **2** | 2 | 0 | **High Risk**: If 1 node fails, remaining node (1) cannot form quorum of 2. Cluster freezes. |
| **3** | 2 | **1** | **Standard Production Baseline**: Tolerates 1 node failure while retaining quorum (2). |
| **4** | 3 | **1** | **Anti-Pattern**: Tolerates only 1 failure (same as 3 nodes), but increases network overhead and split-brain risk. |
| **5** | 3 | **2** | **Enterprise Standard**: Tolerates 2 simultaneous node outages. Highly resilient. |
| **6** | 4 | **2** | **Anti-Pattern**: Tolerates 2 failures (same as 5 nodes), adding unnecessary complexity. |
| **7** | 4 | **3** | Maximum practical scale. High latency overhead across write consensus. |

### 5.2 Split-Brain Scenario Explained
Why must `etcd` clusters always be configured with an **odd number of nodes** (3, 5, 7)?

Imagine a 4-node cluster ($N=4, \text{Quorum}=3$). If a network partition splits the cluster into two equal halves (2 nodes on Rack A and 2 nodes on Rack B):
- Rack A has 2 nodes. Needed quorum = 3. Consensus **fails**.
- Rack B has 2 nodes. Needed quorum = 3. Consensus **fails**.
- The entire cluster freezes and refuses writes, even though 4 nodes are fully functional.

Now contrast this with a 5-node cluster ($N=5, \text{Quorum}=3$). A network partition divides the cluster into 3 nodes on Rack A and 2 nodes on Rack B:
- Rack A has 3 nodes. Quorum ($3$) is satisfied. Cluster continues processing writes.
- Rack B has 2 nodes. Cannot form quorum ($2 < 3$). It gracefully pauses until the network heals.
- Split-brain is prevented and the cluster remains online.

### 5.3 Backup and Disaster Recovery (`etcdctl`)
Production disaster recovery plans require automated daily snapshots of the `etcd` database.

#### Installing `etcdctl` CLI
```bash
sudo apt install -y etcd-client
```

#### Taking an `etcd` Snapshot Backup
`etcd` runs as a static pod on the master node and communicates using TLS certificates located in `/etc/kubernetes/pki/etcd/`.
```bash
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /tmp/etcd-backup.db
```

Verify snapshot health and integrity:
```bash
ETCDCTL_API=3 etcdctl --write-out=table snapshot status /tmp/etcd-backup.db
```

#### Restoring `etcd` from Snapshot
When disaster strikes, restore the snapshot into a new data directory:
```bash
ETCDCTL_API=3 etcdctl \
  --data-dir=/var/lib/etcd-restored \
  snapshot restore /tmp/etcd-backup.db
```

Update the static pod manifest for `etcd` located at `/etc/kubernetes/manifests/etcd.yaml`:
1. Modify `volumes.hostPath.path` from `/var/lib/etcd` to `/var/lib/etcd-restored`.
2. Save the file. The `kubelet` automatically detects the change and restarts the `etcd` container pointing to the restored state.

---

## 6. Kubernetes Pods: Lifecycle, Restart Policies & Troubleshooting

### 6.1 What is a Pod?
A **Pod** is the smallest, most fundamental deployable compute unit in Kubernetes. Rather than running containers directly on a virtual machine or physical host, Kubernetes wraps one or more closely coupled containers into a Pod.

#### Key Architectural Characteristics of a Pod
1. **Shared Network Namespace**: All containers inside a single Pod share the exact same network IP address and port space.
   - Containers within the same Pod can communicate with one another using `localhost` over high-speed loopback.
   - Two containers in the same Pod cannot bind to the same port (e.g., both cannot bind to port 8080).
2. **Shared IPC Namespace**: Containers in a Pod share Inter-Process Communication (POSIX shared memory, semaphores).
3. **Shared Storage Volumes**: Any Kubernetes volume defined at the Pod level can be mounted into any or all containers within that Pod, allowing containers to share files (e.g., a primary web server container and a log-shipping sidecar container).

#### Single-Container vs. Multi-Container Pods
- **Single-Container Pods**: The most common pattern in Kubernetes (90%+ of workloads). A single pod wraps a single container.
- **Multi-Container Pods (Sidecar Pattern)**: A main application container runs alongside helper containers. Common helper patterns include:
  - **Sidecar**: Shippers collecting logs or forwarding telemetry metrics.
  - **Adapter**: Standardizing output formats from legacy applications.
  - **Ambassador**: Proxying outgoing connections to databases or cache clusters.

### 6.2 Declarative YAML vs. Imperative Creation
Kubernetes objects can be created imperatively via CLI commands or declaratively via YAML manifests.

#### Imperative Pod Creation (`kubectl run`)
```bash
kubectl run nginx-pod --image=nginx:latest --port=80
kubectl get pods
```

![][image6]

#### Declarative Pod Creation (Production YAML)
Declarative configuration ensures infrastructure-as-code (IaC) versioning in Git repositories:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: web
    env: production
spec:
  containers:
  - name: nginx-container
    image: nginx:1.26
    ports:
    - containerPort: 80
```
Apply the manifest to the cluster:
```bash
kubectl apply -f nginx-pod.yaml
```

### 6.3 DNS-1123 Naming Conventions
All Kubernetes resource names (including Pods, Services, and Namespaces) must conform to the **DNS-1123 Subdomain Standard** (RFC 1123):
- Must contain no more than **253 characters** (some resources limit subdomains to 63 characters).
- Must contain only lowercase alphanumeric characters (`a-z`, `0-9`) or hyphens (`-`).
- Must begin and end with an alphanumeric character (cannot start or end with a hyphen).
- Uppercase letters and underscores (`_`) are strictly disallowed.

### 6.4 Understanding Pod Status and the `READY` Column
When listing pods using `kubectl get pods`, the output displays:
```
NAME        READY   STATUS    RESTARTS   AGE
nginx-pod   1/1     Running   0          45s
```
- **`STATUS: Running`**: The pod has been bound to a node and all containers have been created.
- **`READY: 1/1`**: The fraction represents $\frac{\text{Containers Passing Readiness Checks}}{\text{Total Containers in Pod}}$.
  - If a pod has 2 containers and only 1 is passing readiness checks, the status is `READY 1/2`. Traffic from Services will NOT route to the pod until it reaches `2/2`.

### 6.5 Pod Lifecycle Phases
Every pod passes through a defined lifecycle:

#### Phase Breakdown
1. **`Pending`**: The Pod has been accepted by the Kubernetes API server, but one or more containers are not yet running. This includes time spent waiting to be scheduled, downloading images over the network, or waiting for PersistentVolumes to attach.
2. **`Running`**: The Pod has been bound to a node, and all containers have been created. At least one container is currently running or is in the process of starting or restarting.
3. **`Succeeded`**: All containers in the Pod have terminated successfully and will not be restarted (exit code 0). Common for batch Jobs.
4. **`Failed`**: All containers in the Pod have terminated, and at least one container has terminated in failure (exit code non-zero).
5. **`Unknown`**: The state of the Pod cannot be obtained, typically due to network disruption between the master control plane and the worker node's `kubelet`.

#### Common Troubleshooting Error States
- **`ImagePullBackOff` / `ErrImagePull`**: The container image could not be retrieved (typo in image name/tag, image does not exist, or missing Docker registry credentials).
- **`CrashLoopBackOff`**: The container started, immediately crashed or exited with an error, and the kubelet is waiting in an exponential backoff delay before restarting it.
- **`OOMKilled`**: The container exceeded its configured memory limit (`resources.limits.memory`) and was terminated by the Linux kernel Out-Of-Memory killer (Exit Code 137).

### 6.6 Restart Policies & Exponential Backoff Delay
The `spec.restartPolicy` controls how the `kubelet` handles terminated containers:
- **`Always`** (Default): Restart the container whenever it terminates. Suitable for web servers, APIs, and persistent daemons.
- **`OnFailure`**: Restart the container only if it exits with a non-zero exit code. Suitable for batch jobs that must run to completion.
- **`Never`**: Never restart the container, regardless of exit status.

#### Exponential Backoff Math
When a container in a Pod fails, the `kubelet` restarts it immediately on the first failure. If the container continues to crash, the `kubelet` enforces an exponential backoff delay to prevent overwhelming node CPU, disk I/O, and container runtime resources:

$$\text{Delay}_n = \min(10 \times 2^{n-1}, 300) \text{ seconds}$$

- **1st crash**: Restarted after **10 seconds**
- **2nd crash**: Restarted after **20 seconds**
- **3rd crash**: Restarted after **40 seconds**
- **4th crash**: Restarted after **80 seconds**
- **5th crash**: Restarted after **160 seconds**
- **6th crash onwards**: Capped at **300 seconds (5 minutes)**

If the container runs successfully for **10 minutes**, the kubelet automatically resets the crash backoff timer back to 10 seconds.

### 6.7 Essential Pod Inspection & Troubleshooting Commands
```bash
# 1. Inspect complete object configuration and runtime events
kubectl describe pod nginx-pod

# 2. View real-time container application logs
kubectl logs nginx-pod

# 3. Follow / stream live logs
kubectl logs -f nginx-pod

# 4. View logs of a crashed container before its last restart
kubectl logs --previous nginx-pod

# 5. Execute an interactive shell inside a running container
kubectl exec -it nginx-pod -- /bin/bash

# 6. Execute shell in a specific container within a multi-container pod
kubectl exec -it multi-pod -c log-shipper -- /bin/sh
```

---

## 7. API Versioning, Resource Groups, Labels & Selectors

### 7.1 Kubernetes API Architecture & Versioning
The Kubernetes API is organized hierarchically into **API Groups** to allow modular feature development and backward compatibility.

```
/apis/<group>/<version>/namespaces/<namespace>/<resource-type>
```

#### Core vs. Named API Groups
- **Core (Legacy) Group**: Exposed at `/api/v1`. Contains foundational resources created in Kubernetes' earliest releases (e.g., `Pod`, `Service`, `Namespace`, `ConfigMap`, `Secret`, `PersistentVolume`, `Node`). These do not require an API group prefix in `apiVersion` (simply `apiVersion: v1`).
- **Named API Groups**: Exposed at `/apis/<group>/<version>`. Examples:
  - `apps/v1`: Deployments, ReplicaSets, StatefulSets, DaemonSets.
  - `batch/v1`: Jobs, CronJobs.
  - `networking.k8s.io/v1`: Ingress, NetworkPolicy.
  - `storage.k8s.io/v1`: StorageClass, CSIDriver.
  - `rbac.authorization.k8s.io/v1`: Role, ClusterRole, RoleBinding, ClusterRoleBinding.

#### API Maturity Levels
- **Alpha** (e.g., `v1alpha1`): Experimental features disabled by default. Schema may change incompatibly.
- **Beta** (e.g., `v1beta1`): Well-tested features enabled by default. Schema will be preserved until GA.
- **Stable / GA** (e.g., `v1`): Production-ready features guaranteed for backward compatibility across releases.

---

### 7.2 Labels and Selectors

#### Labels
Labels are key-value pairs attached to Kubernetes objects (Pods, Nodes, Services). They do not provide direct semantic meaning to the core engine; instead, they serve as organizational metadata used for querying, grouping, and controlling routing.
```yaml
metadata:
  labels:
    app: order-service
    tier: backend
    environment: staging
    release: "v2.4.1"
```

#### Selectors
Selectors allow controllers and services to query and target subsets of objects based on their labels.

##### 1. Equality-Based Selectors
Filter resources using operators `=`, `==`, and `!=`.
- Used in `Service` specifications and basic CLI queries:
```bash
# Query all pods with label tier=backend
kubectl get pods -l tier=backend

# Query all pods not in production
kubectl get pods -l environment!=production
```

##### 2. Set-Based Selectors
Filter resources based on a set of values using operators: `In`, `NotIn`, `Exists` (key exists), and `DoesNotExist`.
- Used in `ReplicaSet`, `Deployment`, `NetworkPolicy`, and `PodAffinity` manifests under `matchExpressions`:
```yaml
spec:
  selector:
    matchLabels:
      tier: backend
    matchExpressions:
    - key: environment
      operator: In
      values: [staging, production]
    - key: release
      operator: NotIn
      values: [deprecated, canary]
```

### 7.3 Multi-Resource Declarative Manifests
Multiple Kubernetes resources can be declared inside a single YAML file using three hyphens (`---`) as document separators:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-one
spec:
  containers:
  - name: c1
    image: nginx
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-two
spec:
  containers:
  - name: c2
    image: redis
```

---

## 8. ReplicaSet (RS) Controller: Desired State, Self-Healing & Pod Adoption

### 8.1 Purpose of the ReplicaSet Controller
Running standalone Pods in production is an anti-pattern. If a standalone Pod crashes or the underlying worker node experiences a hardware failure, the pod is lost forever. 

A **ReplicaSet** guarantees the availability and scale of a specified number of identical Pod replicas at any given time.
- **Desired State Reconciliation**: A continuous control loop compares the number of actual running pods matching the label selector against `spec.replicas`.
- If there are too few pods (due to node failure or container crash), it creates new ones.
- If there are too many pods (e.g., an operator manually launched extra pods with identical labels), it terminates the excess instances.

### 8.2 ReplicaSet Manifest Example
```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: frontend-rs
  labels:
    app: guestbook
    tier: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      tier: frontend
  template:
    metadata:
      labels:
        tier: frontend
    spec:
      containers:
      - name: php-redis
        image: gcr.io/google_samples/gb-frontend:v3
```

### 8.3 Scaling Workloads
- **Imperative CLI Scaling**:
```bash
kubectl scale rs frontend-rs --replicas=5
```
- **Declarative Scaling**: Update `spec.replicas: 5` in `frontend-rs.yaml` and execute `kubectl apply -f frontend-rs.yaml`.

### 8.4 The Pod Adoption Phenomenon
One of the most critical concepts in Kubernetes controller design is **Label-Based Decoupling**. A ReplicaSet does **not** own a private internal list of pod IDs; it simply watches for any pod in the namespace matching its `spec.selector.matchLabels`.

#### Hands-on Experiment: Pod Adoption
1. **Step 1: Create an unmanaged standalone pod with label `tier: frontend`**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: orphaned-pod
  labels:
    tier: frontend
spec:
  containers:
  - name: nginx
    image: nginx
```
```bash
kubectl apply -f orphan.yaml
kubectl get pods
# orphaned-pod   1/1     Running   0          10s
```

2. **Step 2: Create a ReplicaSet with `replicas: 3` targeting `tier: frontend`**:
When `frontend-rs` is created, it queries the API server for pods matching `tier: frontend`. It discovers `orphaned-pod` already exists and is healthy!
- Instead of creating 3 new pods, it **adopts** `orphaned-pod` and creates only **2 additional pods** to satisfy the desired count of 3.
- If you inspect `orphaned-pod` via `kubectl describe pod orphaned-pod`, you will see its `Controlled By:` field has been updated to point to `ReplicaSet/frontend-rs`.

3. **Step 3: What happens if you delete `orphaned-pod`?**:
The ReplicaSet controller detects the running count dropped from 3 to 2, and immediately spins up a new pod with an auto-generated name (e.g., `frontend-rs-x8k2j`) to maintain desired state.

---

## 9. Deployment Controller & Zero-Downtime Rolling Updates

### 9.1 The Hierarchical Architecture of Deployments
While ReplicaSets ensure pods stay alive, they cannot gracefully manage application updates or version transitions. If you change the container image in a ReplicaSet manifest and run `kubectl apply`, existing running pods will **not** update because the ReplicaSet's only job is to maintain the replica count, not refresh existing containers.

The **Deployment Controller** sits one level above ReplicaSets, providing declarative updates for Pods and ReplicaSets.

$$\text{Deployment} \longrightarrow \text{Manages ReplicaSets} \longrightarrow \text{Manages Pods}$$

### 9.2 Zero-Downtime Rolling Update Strategy
When an image version is updated, the Deployment controller provisions a **new ReplicaSet (v2)** while gradually scaling down the **old ReplicaSet (v1)**. User traffic continues to be served throughout the transition without dropping connections.

Two parameters inside `spec.strategy.rollingUpdate` govern this behavior:
1. **`maxSurge`**: The maximum number of Pods that can be created **above** the desired replica count during an update. Can be an absolute number (e.g., `2`) or a percentage (default: `25%`).
2. **`maxUnavailable`**: The maximum number of Pods that can be unavailable during the update process. Can be an absolute number or a percentage (default: `25%`).

#### Formula & Example Calculation
For a Deployment with `replicas: 8`, `maxSurge: 25%`, and `maxUnavailable: 25%`:
- $\text{Max Surge} = 8 \times 0.25 = 2 \text{ pods}$ $\implies \text{Total pods can surge up to } 8 + 2 = 10 \text{ pods}$.
- $\text{Max Unavailable} = 8 \times 0.25 = 2 \text{ pods}$ $\implies \text{At least } 8 - 2 = 6 \text{ pods must be operational}$.

During the update, Kubernetes will create 2 new pods (v2). Once they pass readiness probes, it terminates 2 old pods (v1), ensuring seamless traffic switching.

### 9.3 Deployment Manifest Example
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app-deploy
  labels:
    app: web-app
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: nginx
        image: nginx:1.24
        ports:
        - containerPort: 80
```

### 9.4 Rollout Management & Instant Rollbacks
Kubernetes maintains a complete revision history for Deployments, enabling instant rollbacks if a newly deployed version introduces runtime bugs.

```bash
# Apply initial deployment with change-cause annotation
kubectl apply -f web-app.yaml --record

# Update container image to a newer release
kubectl set image deployment/web-app-deploy nginx=nginx:1.26 --record

# Check live rollout progression
kubectl rollout status deployment/web-app-deploy

# View deployment rollout history and revisions
kubectl rollout history deployment/web-app-deploy

# Output:
# REVISION  CHANGE-CAUSE
# 1         kubectl apply -f web-app.yaml --record
# 2         kubectl set image deployment/web-app-deploy nginx=nginx:1.26 --record

# Undo rollout and revert to previous revision
kubectl rollout undo deployment/web-app-deploy

# Roll back to a specific revision (e.g., revision 1)
kubectl rollout undo deployment/web-app-deploy --to-revision=1
```

### 9.5 Container Log Retention & Centralized Logging Architecture
By default, the `kubelet` stores container logs in `/var/log/pods/` on the local worker node. However, Kubernetes applies a strict local log rotation policy:
- Maximum container log file size before rotation is typically **10MB** (configurable via `containerLogMaxSize`).
- Maximum number of rotated log files per container is **5** (configurable via `containerLogMaxFiles`).

Because pods are ephemeral and local logs are rotated quickly under heavy traffic, **container logs must never be relied upon for audit trails or production debugging**. In production, a centralized log-shipping daemon (such as Fluentd, Fluent Bit, or Logstash) is deployed as a **DaemonSet** on every node to continuously stream logs to centralized repositories (Elasticsearch, AWS OpenSearch, CloudWatch, or Grafana Loki).

---

## 10. DaemonSet Controller & Node Daemon Architecture

### 10.1 Purpose of a DaemonSet
A **DaemonSet** ensures that **all (or a selected subset of) worker nodes run exactly one copy of a Pod**. As new nodes are added to the cluster, the DaemonSet automatically adds the pod to them. As nodes are removed from the cluster, those pods are garbage collected.

#### DaemonSet vs. Deployment Key Differences
- A Deployment has a `spec.replicas` field. You choose *how many* total instances to run across the cluster.
- A DaemonSet has **no replicas field**. The number of running pods is strictly determined by the number of active, matching worker nodes in the cluster.

### 10.2 Node Failure Behavior: DaemonSet vs. Deployment
Understanding how controllers respond to node failure is essential for systems design:

1. **Deployment / ReplicaSet Node Outage**:
   - If Worker Node 2 crashes or its `kubelet` is stopped (`sudo systemctl stop kubelet`), the node controller marks the node `NotReady`.
   - After the eviction timeout (default 5 minutes), Kubernetes declares the pods on that node lost and **reschedules replacement pods onto remaining healthy nodes** (Worker Node 1 or 3).
2. **DaemonSet Node Outage**:
   - If Worker Node 2 crashes, its DaemonSet pod is lost.
   - Kubernetes **NEVER** reschedules that DaemonSet pod to Worker Node 1 or 3! Scheduling a second DaemonSet pod on an existing healthy node would violate the core invariant of running *exactly one pod per node*.
   - When Worker Node 2 is repaired and rejoins the cluster, the `kubelet` immediately spawns the DaemonSet pod locally.

### 10.3 Primary Production Use Cases
1. **Cluster Storage Daemons**: Running storage daemons like Ceph (`ceph-csi`), GlusterFS, or AWS EBS node agents on every storage node.
2. **Cluster Logging Daemons**: Running log collectors like `fluentd`, `fluent-bit`, or Filebeat on every worker node to tail `/var/log/pods/`.
3. **Node Monitoring Daemons**: Running hardware and OS exporters like Prometheus `node-exporter` (listening on port 9100) or Datadog agent on every node.
4. **Network Plugins & CNI**: Core networking components like `kube-proxy` and `calico-node` run as DaemonSets across the entire cluster.

Verify active system DaemonSets running across all nodes:
```bash
kubectl get ds -n kube-system
```

![][image25]

### 10.4 DaemonSet Manifest Example
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentbit-logging
  namespace: kube-system
  labels:
    k8s-app: fluentbit-logging
spec:
  selector:
    matchLabels:
      name: fluentbit
  template:
    metadata:
      labels:
        name: fluentbit
    spec:
      tolerations:
      # Allow daemon to run on master nodes as well
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
      containers:
      - name: fluentbit
        image: fluent/fluent-bit:3.0
        volumeMounts:
        - name: varlog
          mountPath: /var/log
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
```

---

## 11. Kubernetes Services & Networking Abstractions

### 11.1 The Ephemeral Pod IP Problem
In Kubernetes, every Pod receives its own unique IP address from the CNI network CIDR (e.g., `192.168.1.15`). However:
1. **Pods are ephemeral**: When a pod crashes, scales down, or is replaced during a rolling update, it is terminated and its IP address is released.
2. **Replacement pods receive completely new IPs**: The newly created pod will have an entirely different IP address (e.g., `192.168.2.42`).
3. If an upstream frontend microservice attempted to connect directly to backend pod IPs, it would constantly fail as backend IPs change.

A **Service** provides a stable, permanent abstraction (a static Virtual IP and static DNS name) that sits in front of a dynamic group of backend Pods, automatically load balancing incoming traffic across all healthy replicas.

### 11.2 The Four Core Service Types

| Service Type | Scope & Routing Mechanism | Typical Use Case |
| :--- | :--- | :--- |
| **`ClusterIP`** (Default) | Assigns an internal Virtual IP accessible **only within the cluster**. | Inter-service communication (e.g., Frontend talking to Backend, Backend talking to internal Database). |
| **`NodePort`** | Exposes the service on each worker node’s physical IP at a static port allocated from the range **30000–32767**. | Direct external access for development/debugging, or routing traffic through on-premise hardware load balancers. |
| **`LoadBalancer`** | Integrates with cloud provider APIs (AWS, GCP, Azure) to automatically provision an external cloud load balancer (e.g., AWS NLB). The cloud LB forwards to NodePorts, which route to ClusterIP. | Production-grade public-facing web traffic. |
| **`Headless`** | Configured with `clusterIP: None`. No virtual IP is allocated. DNS queries directly return the individual IP addresses of all backing pods. | Stateful applications, database replication topologies (Master/Replica), and peer discovery (Kafka, ZooKeeper). |

### 11.3 End-to-End Enterprise Traffic Flow
Understanding how client requests route from the public internet into a container:

---

### 11.4 Hands-On Service Implementation & Load Balancing Verification

#### Step 1: Deploy a Sample Application (`k8s-helloworld`)
Create a deployment running 3 replicas of a hello-world container listening on port 8080:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-deploy
  labels:
    app: hello
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      labels:
        app: hello
    spec:
      containers:
      - name: hello-container
        image: karthequian/helloworld:latest
        ports:
        - containerPort: 8080
```
Deploy and verify pods:
```bash
kubectl apply -f hello-deploy.yaml
kubectl get pods -l app=hello -o wide
```

#### Step 2: Create a `ClusterIP` Service (`cip.yaml`)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: hello-cip
spec:
  type: ClusterIP
  selector:
    app: hello
  ports:
  - protocol: TCP
    port: 80          # Service port (incoming traffic)
    targetPort: 8080  # Container port (where application listens)
```
Apply and inspect the Service and its associated `Endpoints`:
```bash
kubectl apply -f cip.yaml
kubectl get svc hello-cip
# NAME        TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
# hello-cip   ClusterIP   10.105.42.18   <none>        80/TCP    15s
```

![][image7]

Inspect detailed service configuration and endpoints:
```bash
kubectl describe svc hello-cip
```

![][image8]

```bash
kubectl get endpoints hello-cip
# NAME        ENDPOINTS                                                  AGE
# hello-cip   192.168.1.25:8080,192.168.1.26:8080,192.168.2.14:8080   30s
```

#### Step 3: Verifying Internal Round-Robin Load Balancing
Launch a temporary debug container to test internal connectivity to the Service ClusterIP:
```bash
kubectl run test-curl --rm -it --image=curlimages/curl -- sh

# Inside the curl shell, issue multiple requests to the Service name:
/ $ curl http://hello-cip
# Hello World from hello-deploy-7448df749-j28kx!

/ $ curl http://hello-cip
# Hello World from hello-deploy-7448df749-v9fms!

/ $ curl http://hello-cip
# Hello World from hello-deploy-7448df749-x6lqr!
```
Notice how each curl request resolves through the Service VIP and is distributed evenly across the three distinct pod hostnames.

#### Step 4: Exposing Externally via `NodePort` Service (`node.yaml`)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: hello-nodeport
spec:
  type: NodePort
  selector:
    app: hello
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
    nodePort: 30080    # Must be between 30000 and 32767
```
```bash
kubectl apply -f node.yaml
kubectl get svc hello-nodeport
```
Now, external clients can access the application by navigating in a web browser to:
`http://<ANY_WORKER_NODE_PUBLIC_IP>:30080`

---

## 12. StatefulSet Controller & Headless Services

### 12.1 Why Deployments Cannot Run Databases
Deployments and ReplicaSets are designed exclusively for **stateless** workloads (web servers, microservices, stateless APIs) where:
- All pods are 100% interchangeable clones.
- Pods have random generated names (`frontend-849dfb-9q2kx`).
- Pods can be created or terminated in arbitrary parallel order.
- Pods share an identical backing storage bucket or do not persist state locally.

However, distributed stateful applications (such as MySQL Primary/Replica, PostgreSQL, MongoDB replica sets, Apache Cassandra, Apache Kafka, and ZooKeeper) have strict operational requirements:
1. **Predictable Identity**: Each node must have a dedicated, stable role (e.g., `mysql-0` is Primary, `mysql-1` is Replica).
2. **Dedicated Storage**: If `mysql-1` fails, its replacement must re-attach to the exact same physical disk volume to avoid data corruption or re-syncing terabytes of data.
3. **Sequential Scaling**: Data clustering protocols require node 0 to initialize first, form a quorum, and then node 1 and node 2 can sequentially join.

The **StatefulSet Controller** is purpose-built to satisfy these requirements.

---

### 12.2 The Four Core Features of StatefulSets

#### 1. Stable, Unique Network Identifiers
Pods managed by a StatefulSet receive a predictable, sticky ordinal index starting at 0:
$$\text{Name Format}: <\text{statefulset-name}>-<\text{ordinal}>$$
For a StatefulSet named `web` with 3 replicas: `web-0`, `web-1`, `web-2`.
Even if `web-1` crashes and is rescheduled to a completely different physical machine, it retains the exact hostname `web-1`.

#### 2. Stable, Dedicated Persistent Storage
StatefulSets do not define a shared volume. Instead, they use `volumeClaimTemplates`.
- For each replica, Kubernetes dynamically creates a distinct PersistentVolumeClaim:
$$\text{PVC Format}: <\text{volume-claim-name}>-<\text{pod-name}>$$
- `data-web-0` is bound strictly to `web-0`.
- `data-web-1` is bound strictly to `web-1`.
- If `web-1` terminates, its replacement pod automatically mounts `data-web-1`.

#### 3. Ordered, Graceful Deployment and Scaling
- **Scaling Up**: Pods are launched strictly sequentially from ordinal $0$ to $N-1$. Pod $1$ is never started until Pod $0$ is in a `Running` and `Ready` state.
- **Scaling Down**: Pods are terminated in reverse ordinal order, from $N-1$ down to $0$. Pod $1$ is not terminated until Pod $2$ has completely shut down.

#### 4. Ordered, Automated Rolling Updates
When an update is rolled out, the StatefulSet controller updates pods in reverse ordinal order (e.g., `web-2` first, then `web-1`, then `web-0`), ensuring quorum is preserved throughout database updates.

---

### 12.3 Headless Services: The Networking Glue for StatefulSets
Standard Kubernetes Services assign a virtual ClusterIP that round-robins traffic indiscriminately. This breaks database architectures because a write request must be routed specifically to `mysql-0` (the primary), while read traffic can route to `mysql-1` or `mysql-2`.

A **Headless Service** is a Service created with:
```yaml
spec:
  clusterIP: None
```

When `clusterIP: None` is set:
1. The Service does **not** allocate a Virtual IP.
2. CoreDNS creates direct A-records for each individual pod in the StatefulSet:
$$\text{FQDN}: <\text{pod-name}>.<\text{service-name}>.<\text{namespace}>.svc.cluster.local$$
- `mysql-0.mysql-service.default.svc.cluster.local` resolves directly to Pod 0's IP.
- `mysql-1.mysql-service.default.svc.cluster.local` resolves directly to Pod 1's IP.

This allows stateful applications to discover peers and replicate state directly without intermediaries.

### 12.4 Production StatefulSet Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-headless
  labels:
    app: stateful-nginx
spec:
  ports:
  - port: 80
    name: web
  clusterIP: None        # Headless Service definition
  selector:
    app: stateful-nginx
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: "nginx-headless"   # Links to headless service
  replicas: 3
  selector:
    matchLabels:
      app: stateful-nginx
  template:
    metadata:
      labels:
        app: stateful-nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.26
        ports:
        - containerPort: 80
          name: web
        volumeMounts:
        - name: www
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:          # Dynamically provisions 1 PVC per pod
  - metadata:
      name: www
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: "standard"
      resources:
        requests:
          storage: 5Gi
```

---

## 13. Headless Service DNS Discovery Deep Dive

### 13.1 Headless Service Implementation Walkthrough
In Section 12, we explored why stateful distributed applications require stable network identities. Here, we demonstrate the exact mechanics of Headless Service DNS resolution compared to standard ClusterIP Services.

#### Manifest: `hello-hl.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: hello-hl
spec:
  type: ClusterIP
  clusterIP: None        # Explicitly disables virtual IP allocation
  selector:
    app: hello
  ports:
  - targetPort: 8080
    port: 80
```

Deploy the Headless Service:
```bash
kubectl apply -f hello-hl.yaml
```

Inspect the Services in the namespace:
```bash
kubectl get svc
```
![][image9]

Notice that for `hello-cip`, Kubernetes assigned a cluster virtual IP (e.g., `10.105.42.18`). For `hello-hl`, the `CLUSTER-IP` column explicitly displays `None`.

Inspect the endpoints associated with `hello-hl`:
```bash
kubectl describe svc hello-hl
```
![][image10]

Even though `hello-hl` lacks a virtual IP, its `Endpoints` slice maintains active tracking of all three backend pod IP addresses.

---

### 13.2 Comparing DNS Lookups: ClusterIP vs. Headless Service
To observe how CoreDNS handles these two service types, launch a shell inside a running debug pod (such as an `nginx` pod) and install `dnsutils`:
```bash
kubectl exec -it nginx -- bash

# Install DNS lookup utilities inside the container
apt update && apt install -y dnsutils
```

#### 1. DNS Resolution for Standard ClusterIP Service (`hello-cip`)
```bash
nslookup hello-cip
```
![][image11]

The DNS server returns **a single virtual IP address** (`10.105.42.18`). When client traffic connects to this virtual IP, `kube-proxy` iptables/IPVS rules intercept the connection and forward it to one of the backend pods via round-robin load balancing.

#### 2. DNS Resolution for Headless Service (`hello-hl`)
```bash
nslookup hello-hl
```
![][image12]

Instead of returning a virtual IP, the DNS query directly returns **three distinct A-records**, corresponding to the individual, physical IP addresses of each pod currently running behind the selector (`192.168.1.25`, `192.168.1.26`, `192.168.2.14`).

This allows database drivers, stateful clustering frameworks, and service discovery libraries to connect directly to specific nodes, perform master/replica discovery, and maintain point-to-point replication streams.

---

## 14. Storage Management: Volumes, HostPath, EmptyDir, PV, PVC & StorageClasses

### 14.1 Ephemeral vs. Persistent Storage
By default, the root filesystem inside a container is ephemeral. When a container crashes or is restarted by the `kubelet`, all files written to the container layer are permanently lost.

Kubernetes provides storage abstractions to solve two distinct challenges:
1. **Preserving data across container restarts** within the same pod.
2. **Preserving data across pod terminations, rescheduling, and cluster reboots**.

---

### 14.2 Basic Volume Types

#### 1. `emptyDir` (Ephemeral Pod Storage)
An `emptyDir` volume is created when a Pod is assigned to a Node, and exists as long as that Pod is running on that node.
- Initially empty.
- All containers in the Pod can read and write the same files in the `emptyDir`.
- When a Pod is removed from a node for any reason, the data in the `emptyDir` is deleted permanently.
- **Primary Use Cases**: Scratch space (sorting large files), disk-based cache, checkpointing long computations.

#### 2. `hostPath` (Node Bind Mount)
A `hostPath` volume mounts a file or directory from the host node’s filesystem directly into your Pod.
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-hostpath
spec:
  volumes:
  - name: host-data
    hostPath:
      path: /tmp/data
      type: DirectoryOrCreate
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: host-data
      mountPath: /data
```

#### Architectural Limitations of `hostPath`
> [!WARNING]
> `hostPath` volumes pose serious risks in multi-node clusters:
> 1. **Node Affinity Lock**: If a pod writes data to `/tmp/data` on Worker Node 1, and the pod is later rescheduled to Worker Node 2, the pod will look at `/tmp/data` on Worker Node 2, where the data does not exist!
> 2. **Security Vulnerability**: Containers gaining access to host directories can read or overwrite host system files.
> 3. **Permission Mismatches**: The user running inside the container (e.g., UID 1000) may lack write permissions on the host directory owned by root.

---

### 14.3 The Persistent Volume (PV) Subsystem
To decouple physical storage infrastructure from application developers, Kubernetes introduces a clean separation of concerns:
- **Cluster Administrator**: Configures physical/cloud storage pools (NFS, SAN, AWS EBS, Ceph) and registers them as **PersistentVolumes (PV)**.
- **Application Developer**: Requests storage capacity and access modes by writing a **PersistentVolumeClaim (PVC)**, without needing to know the underlying storage technology.

#### Storage Access Modes
- **`ReadWriteOnce` (RWO)**: The volume can be mounted as read-write by a single node. (Standard for block storage like AWS EBS, GCP Persistent Disk, Azure Disk).
- **`ReadOnlyMany` (ROX)**: The volume can be mounted as read-only by many nodes simultaneously.
- **`ReadWriteMany` (RWX)**: The volume can be mounted as read-write by many nodes simultaneously. (Requires network-attached file systems like NFS, AWS EFS, GlusterFS, or CephFS).

#### Volume Reclaim Policies
Controls what happens to the underlying storage when a developer deletes their `PersistentVolumeClaim`:
- **`Retain`**: The PersistentVolume still exists, but its status changes to `Released`. Data remains intact on disk. An administrator must manually reclaim or backup the volume before it can be reused.
- **`Delete`** (Default for dynamic cloud storage): Automatically deletes both the Kubernetes `PersistentVolume` object and the physical cloud storage volume (e.g., deletes the AWS EBS volume).
- **`Recycle`** (Deprecated): Performs a basic scrub (`rm -rf /thevolume/*`) and makes the volume available again.

---

### 14.4 Static Provisioning Walkthrough

#### Step 1: Cluster Admin Creates the Persistent Volume (`pv.yaml`)
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: static-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
  - ReadWriteOnce
  storageClassName: host
  hostPath:
    path: /tmp/data
```
```bash
kubectl apply -f pv.yaml
kubectl get pv
```
![][image13]

Notice that the `STATUS` is `Available` and `CLAIM` is empty. The storage is registered with the cluster, waiting to be claimed.

#### Step 2: Developer Submits a Claim (`pvc.yaml`)
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: static-pvc
spec:
  storageClassName: host
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```
```bash
kubectl apply -f pvc.yaml
kubectl get pvc
```
![][image14]

The PVC matches the criteria of `static-pv` (1Gi capacity, `ReadWriteOnce` access mode, and matching `storageClassName: host`). Its status immediately changes to `Bound`.

Verify the PV status updates to `Bound`:
```bash
kubectl get pv
```
![][image15]

#### Understanding `storageClassName` Matching Pools
The `storageClassName` acts as a grouping tag. Administrators can create pools of storage with varying performance characteristics:
- `storageClassName: fast-ssd` (Provisioned IOPS SSDs for Databases)
- `storageClassName: standard-hdd` (High-capacity magnetic storage for log archives)

Developers specify the corresponding class in their PVC to claim volumes from the intended pool:
![][image16]

#### Step 3: Mounting the Claim in an Application Pod (`pod-pvc.yaml`)
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-storage-app
spec:
  volumes:
  - name: app-data
    persistentVolumeClaim:
      claimName: static-pvc
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 80
    volumeMounts:
    - name: app-data
      mountPath: /usr/share/nginx/html
```

Apply the pod manifest and verify pod scheduling on the worker node:
```bash
kubectl apply -f pod-pvc.yaml
kubectl get pods -o wide
```

![][image17]

Verify persistent volume mounting inside the running container:
```bash
kubectl exec -it nginx-storage-app -- bash
cd /data
ls -la
```

![][image18]

#### Hands-On Reclaim Policy Verification & Volume Recovery

##### 1. `Retain` Policy Recovery Walkthrough
When the PVC is deleted under the `Retain` policy, the PV status transitions to `Released`. The volume is preserved, but cannot be claimed by other pods because the previous claimant's `claimRef` remains bound.
To make the PV available for reuse:
```bash
kubectl edit pv static-pv
# Remove the entire 'claimRef' block from the manifest and save
```

![][image19]

If a new PVC is submitted before clearing `claimRef`, the claim remains stuck in `Pending` state:
```bash
kubectl get pvc
```

![][image20]

##### 2. `Delete` Reclaim Policy Walkthrough
To enable automatic storage cleanup, update the PV reclaim policy to `Delete`:
```bash
kubectl edit pv static-pv
# Set persistentVolumeReclaimPolicy: Delete
```

![][image21]

Deleting the PVC now triggers automatic deletion of the bound PV:
```bash
kubectl delete pvc test
kubectl get pv
```

![][image22]

##### 3. `Recycle` Policy & Dynamic Provisioning Transition
The deprecated `Recycle` policy performs a basic data scrub (`rm -rf /thevolume/*`) to reuse storage:

![][image23]

While static provisioning works well for small environments, managing individual PV pools manually becomes impractical at scale, requiring **Dynamic Provisioning**.

---

### 14.5 Dynamic Provisioning with StorageClasses
Static provisioning requires manual ticket creation and pre-allocation by administrators. In modern cloud environments, **Dynamic Provisioning** eliminates this bottleneck.

A **StorageClass** defines:
1. **Provisioner**: The CSI plugin responsible for creating volumes (e.g., `ebs.csi.aws.com`).
2. **Parameters**: Storage tier attributes (e.g., `type: gp3`, `iops: "3000"`).
3. **Volume Binding Mode**:
   - `Immediate`: Volume is provisioned as soon as the PVC is submitted.
   - `WaitForFirstConsumer`: Delays volume creation until a Pod using the PVC is scheduled. This guarantees the volume is provisioned in the exact AWS Availability Zone (AZ) where the pod is scheduled!

#### Dynamic StorageClass Manifest
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ebs-sc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
```
When a developer submits a PVC referencing `fast-ebs-sc`, the AWS EBS CSI driver communicates directly with the AWS EC2 API, provisions a new EBS gp3 volume, formats it, creates the PV, and mounts it to the worker node automatically.

---

## 15. Namespaces, ResourceQuotas & Compute Resource Management

### 15.1 Namespaces: Virtual Cluster Partitioning
A **Namespace** provides a mechanism for isolating groups of resources within a single physical Kubernetes cluster.

#### Built-in Default Namespaces
- **`default`**: The fallback namespace for objects created without an explicit `--namespace` flag.
- **`kube-system`**: Reserved for internal control plane components, CNI pods (Calico), CoreDNS, and cluster-wide add-ons.
- **`kube-public`**: Completely readable by all users (authenticated or unauthenticated); holds public cluster discovery information.
- **`kube-node-lease`**: Holds `Lease` objects associated with each node, allowing the control plane to detect node heartbeats with minimal overhead.

#### Working with Namespaces
When clearing workloads in the default namespace:
```bash
kubectl delete pods --all
kubectl get pods
# No resources found in default namespace.
```

![][image24]

```bash
# Create a dedicated namespace for staging
kubectl create namespace staging

# List pods in a specific namespace
kubectl get pods -n staging

# Permanently switch active namespace in current context
kubectl config set-context --current --namespace=staging
```

---

### 15.2 Compute Resource Management: Requests vs. Limits
To ensure fair resource sharing and prevent "noisy neighbor" problems, every container specification should declare CPU and memory **Requests** and **Limits**.

```yaml
resources:
  requests:
    cpu: "250m"       # 250 milliCPUs (0.25 vCPU)
    memory: "512Mi"   # 512 Mebibytes
  limits:
    cpu: "1000m"      # 1 vCPU
    memory: "1Gi"     # 1 Gibibyte
```

#### Deep Dive: Requests vs. Limits Behavior
| Metric | CPU (Compressible Resource) | Memory (Non-Compressible Resource) |
| :--- | :--- | :--- |
| **`requests`** | Minimum guaranteed CPU reserved by `kube-scheduler` when placing pods on nodes. | Minimum guaranteed RAM reserved on the node. |
| **`limits`** | Hard ceiling enforced via Linux Completely Fair Scheduler (CFS) quotas. | Hard ceiling enforced via Linux memory cgroups. |
| **Exceeding Limit** | **Throttling**: The container’s CPU usage is throttled. The application slows down, but is **never terminated**. | **OOMKilled**: The Linux kernel Out-of-Memory killer terminates the container immediately (**Exit Code 137**). |

---

### 15.3 ResourceQuotas: Multi-Tenant Budget Enforcement
In shared clusters, a single team could accidentally deploy workloads that consume 100% of the cluster's compute capacity. A **ResourceQuota** enforces hard resource consumption caps across an entire namespace.

#### ResourceQuota Manifest (`quota.yaml`)
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-quota
  namespace: demo
spec:
  hard:
    requests.cpu: "4"             # Max 4 vCPUs total requested across namespace
    requests.memory: 8Gi          # Max 8Gi total RAM requested
    limits.cpu: "8"               # Max 8 vCPUs total limit
    limits.memory: 16Gi           # Max 16Gi total RAM limit
    pods: "10"                    # Max 10 pods total in namespace
    services: "5"                 # Max 5 services
    services.nodeports: "2"       # Max 2 NodePort services
```

> [!IMPORTANT]
> Once a ResourceQuota is applied to a namespace, **Kubernetes strictly rejects any pod creation request in that namespace that does not explicitly define CPU and memory requests and limits**! To streamline developer experience, administrators pair ResourceQuotas with **LimitRanges**, which inject default requests/limits automatically.

#### Inspecting ResourceQuotas
```bash
# View resource quotas in default namespace
kubectl get resourcequotas
```

![][image26]

```bash
# View resource quotas in dev namespace
kubectl get resourcequotas -n dev
```

![][image27]

```bash
# View detailed quota consumption and limits
kubectl describe resourcequota -n dev
```

![][image28]

---

## 16. Configuration Management: Environment Variables, ConfigMaps & Secrets

### 16.1 Decoupling Configuration from Application Code
Following the **Twelve-Factor App methodology**, application source code must remain completely immutable across environments (Dev, UAT, Staging, Production). Any environment-specific parameters (database connection strings, feature flags, third-party API URLs, credentials) must be injected at runtime via Kubernetes configuration objects.

---

### 16.2 Environment Variables in Pods
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: env-demo
spec:
  containers:
  - name: app
    image: my-app:v1
    env:
    - name: ENVIRONMENT
      value: "production"
    - name: LOG_LEVEL
      value: "warn"
```

---

### 16.3 ConfigMaps: Non-Confidential Data
**ConfigMaps** store non-sensitive configuration data as key-value pairs or complete configuration files.

#### Creating ConfigMaps
1. **From CLI Literals**:
```bash
kubectl create configmap app-config \
  --from-literal=DB_PORT=3306 \
  --from-literal=DB_HOST=mysql.production.svc
```
2. **From Configuration Files**:
```bash
kubectl create configmap nginx-config --from-file=nginx.conf
```
3. **Declarative YAML**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-settings
  namespace: default
data:
  APP_ENV: "production"
  MAX_CONNECTIONS: "100"
  config.json: |
    {
      "cacheTimeout": 3600,
      "enableMetrics": true
    }
```

#### Consuming ConfigMaps in Pods
1. **Inject Specific Keys as Environment Variables**:
```yaml
env:
- name: APPLICATION_ENVIRONMENT
  valueFrom:
    configMapKeyRef:
      name: app-settings
      key: APP_ENV
```
2. **Inject All Keys as Environment Variables (`envFrom`)**:
```yaml
envFrom:
- configMapRef:
    name: app-settings
```
3. **Mount ConfigMap as a Directory of Files**:
```yaml
volumes:
- name: config-volume
  configMap:
    name: app-settings
containers:
- name: app
  image: app:v1
  volumeMounts:
  - name: config-volume
    mountPath: /etc/config
```
Inside the container, `/etc/config/APP_ENV` and `/etc/config/config.json` appear as standard files. When the ConfigMap is updated, mounted files are updated automatically without restarting the pod!

---

### 16.4 Secrets: Sensitive Data Management
**Secrets** store confidential data such as database passwords, API tokens, SSH keys, and TLS certificates.

#### Secret Types
- **`Opaque`**: Arbitrary user-defined key-value data (passwords, tokens).
- **`kubernetes.io/tls`**: Holds `tls.crt` and `tls.key` for SSL/TLS termination.
- **`kubernetes.io/dockerconfigjson`**: Stores authentication credentials for private container registries (Docker Hub, AWS ECR, GitHub Container Registry).
- **`kubernetes.io/service-account-token`**: Stores tokens used to authenticate pod identities against the API server.

#### Base64 Encoding & Creation
Values in a Secret YAML manifest must be base64 encoded:
```bash
echo -n "SuperSecretPass123!" | base64
# Output: U3VwZXJTZWNyZXRQYXNzMTIzIQ==
```

#### Secret Manifest (`db-secret.yaml`)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  DB_USERNAME: YWRtaW4=                     # "admin"
  DB_PASSWORD: U3VwZXJTZWNyZXRQYXNzMTIzIQ== # "SuperSecretPass123!"
```

#### Consuming Secrets in a Pod
```yaml
env:
- name: DATABASE_PASSWORD
  valueFrom:
    secretKeyRef:
      name: db-credentials
      key: DB_PASSWORD
```

> [!CAUTION]
> **Base64 encoding is NOT encryption**. It is trivial to decode base64 strings (`echo "..." | base64 -d`).
> In enterprise production environments:
> 1. Enable **Encryption-at-Rest for `etcd`** using an `EncryptionConfiguration` provider (AES-GCM or AWS KMS).
> 2. Restrict access using strict RBAC policies.
> 3. Use external secrets stores (AWS Secrets Manager, HashiCorp Vault) integrated via the **Secrets Store CSI Driver** (covered in Section 24).

---

## 17. Cluster Security & Role-Based Access Control (RBAC)

### 17.1 The Authentication & Authorization Flow
Every request sent to the `kube-apiserver` passes through three distinct gates:
1. **Authentication**: *Who is making the request?* (Validates X.509 client certificates, bearer tokens, or external OIDC tokens).
2. **Authorization (RBAC)**: *Does this subject have permission to perform this action on this resource?*
3. **Admission Control**: *Does the request adhere to cluster policies, resource quotas, and security standards?*

---

### 17.2 Users vs. ServiceAccounts

#### 1. User Accounts
Represent human operators, DevOps engineers, and external CI/CD systems.
- Kubernetes does **not** have an internal database of users.
- Users are managed externally via TLS client certificates (Common Name represents the username, e.g., `CN=john`) or external Identity Providers (Okta, Keycloak, AWS IAM).

#### 2. ServiceAccounts
Represent internal identities for processes running inside Pods.
- Stored as native Kubernetes API resources (`ServiceAccount`).
- Used by applications that need to talk to the API server (e.g., Prometheus scraping cluster metrics, Helm, or Jenkins agent pods).

---

### 17.3 Kubeconfig Anatomy & Context Management
Client authentication settings are stored in `~/.kube/config`. A kubeconfig file consists of three components:
1. **`clusters`**: API server endpoints and CA certificates.
2. **`users`**: Client certificates or authentication tokens.
3. **`contexts`**: A tuple binding `(cluster, user, default-namespace)`.

#### Managing Contexts via CLI
```bash
# List all configured contexts
kubectl config get-contexts

# View current active context
kubectl config current-context

# Switch to another context
kubectl config use-context production-cluster

# Set credentials for a user
kubectl config set-credentials developer --token="<BEARER_TOKEN>"

# Bind user and cluster into a new context
kubectl config set-context dev-context --user=developer --cluster=kubernetes --namespace=dev
```

#### Kubeconfig File Dependency & Remote Cluster Access
If the kubeconfig file is removed or displaced, `kubectl` cannot reach the cluster control plane:
```bash
mv ~/.kube/config ~/.kube/config.bak
kubectl get pods
# The connection to the server localhost:8080 was refused - did you specify the right host or port?
```

![][image29]

Restoring the configuration file reveals the standard structure containing clusters, users, and contexts:
```bash
cat ~/.kube/config
```

![][image30]

When accessing the Kubernetes control plane from an external workstation (such as AWS CloudShell) via its public IP, the cluster TLS certificate (generated for private IP SANs) may cause verification failures. The connection can be configured with `insecure-skip-tls-verify: true` to enable remote administration:

![][image31]

---

### 17.4 Role-Based Access Control (RBAC) Mechanics
RBAC is governed by the `rbac.authorization.k8s.io` API group. It consists of three pillars:
- **Subject**: The entity requesting access (`User`, `Group`, or `ServiceAccount`).
- **Resource**: The API object being accessed (`pods`, `services`, `deployments`, `secrets`, `nodes`).
- **Verb**: The action permitted (`get`, `list`, `watch`, `create`, `update`, `patch`, `delete`).

#### Scope: Namespace vs. Cluster Level
| Scope | Permission Definition | Binding Mechanism | Typical Use Case |
| :--- | :--- | :--- | :--- |
| **Namespace Scope** | **`Role`** | **`RoleBinding`** | Granting developer access to manage pods strictly within `marketing-dev`. |
| **Cluster Scope** | **`ClusterRole`** | **`ClusterRoleBinding`** | Granting cluster monitoring tools read access to nodes and cluster-wide metrics. |

---

### 17.5 Practical RBAC Implementation Walkthrough

#### Step 1: Create a ServiceAccount (`developer-sa`)
```bash
kubectl create sa developer-sa -n demo
```

#### Step 2: Create a Long-Lived Token Secret for the ServiceAccount
In Kubernetes 1.24+, ServiceAccount tokens are no longer auto-generated as permanent secrets; they must be explicitly requested or declared:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: developer-sa-token
  namespace: demo
  annotations:
    kubernetes.io/service-account.name: "developer-sa"
type: kubernetes.io/service-account-token
```
```bash
kubectl apply -f sa-secret.yaml
```

#### Step 3: Define a Namespace-Scoped `Role` (`pod-reader-role`)
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: demo
rules:
- apiGroups: [""]            # Core API group (pods)
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
```

#### Step 4: Bind the Role to the ServiceAccount via `RoleBinding`
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods-binding
  namespace: demo
subjects:
- kind: ServiceAccount
  name: developer-sa
  namespace: demo
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```
Apply both manifests:
```bash
kubectl apply -f role.yaml
kubectl apply -f rolebinding.yaml
```

#### Step 5: Testing Permissions with `kubectl auth can-i`
Kubernetes provides an authorization test command allowing administrators to simulate actions on behalf of subjects:
```bash
# Test if developer-sa can list pods in demo namespace (Returns: yes)
kubectl auth can-i list pods --as=system:serviceaccount:demo:developer-sa -n demo

# Test if developer-sa can delete pods in demo namespace (Returns: no)
kubectl auth can-i delete pods --as=system:serviceaccount:demo:developer-sa -n demo

# Test if developer-sa can list pods in default namespace (Returns: no)
kubectl auth can-i list pods --as=system:serviceaccount:demo:developer-sa -n default
```

---

## 18. Advanced Pod Scheduling: Affinities, Anti-Affinities, Taints & Tolerations

By default, the `kube-scheduler` places pods based on available CPU and memory capacity. However, enterprise production systems require explicit, fine-grained control over pod placement:
- Ensuring database pods run only on high-memory nodes.
- Ensuring web server replicas are spread across different physical servers or cloud Availability Zones to guarantee High Availability.
- Ensuring frontend pods are co-located on the same low-latency rack as their backend caching layer.
- Reserving GPU nodes strictly for machine learning jobs.

---

### 18.1 Node Selection: `nodeName` vs. `nodeSelector`

#### 1. `nodeName` (Direct Hardcoded Bypass)
`nodeName` bypasses the `kube-scheduler` entirely:
```yaml
spec:
  nodeName: worker-node-2
```
If `worker-node-2` is overloaded or offline, the pod fails immediately. **Do not use in production**.

#### 2. `nodeSelector` (Simple Label Matching)
Label a node:
```bash
kubectl label node worker-1 disktype=ssd
```
Configure pod manifest:
```yaml
spec:
  nodeSelector:
    disktype: ssd
```
The scheduler filters nodes, placing the pod strictly on nodes containing the label `disktype=ssd`.

---

### 18.2 Node Affinity Deep Dive
Node Affinity is an advanced, expressive evolution of `nodeSelector` supporting operators (`In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt`) and priority weights.

#### The Two Rules of Node Affinity
1. **Hard Rule (`requiredDuringSchedulingIgnoredDuringExecution`)**:
   - The scheduler **must** satisfy the rule. If no matching node exists, the pod remains in a `Pending` state indefinitely.
2. **Soft Rule (`preferredDuringSchedulingIgnoredDuringExecution`)**:
   - A preference. The scheduler tries to find a matching node, but if none are available, it places the pod on any healthy node. Preferences carry **weights (1–100)** to break ties.

> [!NOTE]
> `IgnoredDuringExecution` means that if labels on a node change *after* a pod is already running, the pod will **not** be evicted; it continues running undisturbed.

#### Hard Rule Manifest Example
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: db-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: hardware-tier
            operator: In
            values: ["high-spec", "bare-metal"]
  containers:
  - name: db
    image: postgres:16
```

#### Soft Rule Manifest Example (Weighted Preferences)
```yaml
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values: ["us-east-1a"]
      - weight: 20
        preference:
          matchExpressions:
          - key: instance-type
            operator: In
            values: ["c5.xlarge"]
```

---

### 18.3 Pod Affinity & Pod Anti-Affinity

While Node Affinity schedules pods based on *node labels*, **Pod Affinity and Anti-Affinity** schedule pods based on the **labels of other Pods already running on those nodes**.

#### 1. Pod Affinity (Co-Location Pattern)
"Place this new pod on the same physical host (or availability zone) as an existing pod."
- **Example**: Co-locating a web frontend pod on the same host as an in-memory Redis cache pod to eliminate network latency.

#### 2. Pod Anti-Affinity (High Availability Spreading Pattern)
"Never place this pod on a host that is already running another instance of this application."
- **Example**: Ensuring that 3 replicas of an API service are scheduled on 3 completely different physical worker nodes or across 3 distinct AWS Availability Zones. If one server or AZ fails, the application remains fully online.

#### The `topologyKey` Concept
`topologyKey` defines the boundary of co-location or spreading:
- `topologyKey: kubernetes.io/hostname`: Spreads pods across individual **physical host machines**.
- `topologyKey: topology.kubernetes.io/zone`: Spreads pods across cloud **Availability Zones** (e.g., `us-east-1a`, `us-east-1b`, `us-east-1c`).
- `topologyKey: topology.kubernetes.io/region`: Spreads across entire geographic **regions**.

---

### 18.4 Real-World 3-Tier Enterprise Scheduling Architecture
Consider a complete production deployment consisting of a **Database**, an in-memory **Cache (Redis)**, and a **Web Frontend**:

1. **Database Tier**: Must run on high-performance bare-metal nodes (`nodeAffinity`).
2. **Cache Tier**: Must spread across distinct nodes for HA (`podAntiAffinity` to itself) AND must **never** run on the database host (`podAntiAffinity` to Database).
3. **Frontend Tier**: Must spread across distinct nodes for HA (`podAntiAffinity` to itself) AND must **co-locate** on the same nodes where Cache pods are running (`podAffinity` to Cache).

#### Complete Production Frontend Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deploy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      affinity:
        # 1. Co-locate frontend pods with Cache pods
        podAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values: ["redis-cache"]
            topologyKey: "kubernetes.io/hostname"
        # 2. Spread frontend replicas across separate physical nodes
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values: ["frontend"]
            topologyKey: "kubernetes.io/hostname"
      containers:
      - name: web
        image: nginx:alpine
```

---

### 18.5 Taints and Tolerations: Node Repulsion

While affinities attract pods to nodes, **Taints and Tolerations** allow nodes to **repel** sets of pods.

- **Taints** are applied to **Nodes**.
- **Tolerations** are applied to **Pods**.
- A node with a taint will refuse to accept any pod that does not explicitly declare a matching toleration.

#### Taint Effects
1. **`NoSchedule`**: Strong filter. New pods without a matching toleration will **never** be scheduled on this node. Existing pods already running on the node are unaffected.
2. **`PreferNoSchedule`**: Soft filter. The scheduler avoids placing untolerated pods on the node, but will do so if cluster capacity is exhausted.
3. **`NoExecute`**: Eviction filter. Untolerated pods are not scheduled, and **any existing untolerated pods currently running on the node are immediately evicted**!

#### Managing Taints via CLI
```bash
# Add a NoSchedule taint to a node
kubectl taint nodes worker-1 dedicated=gpu:NoSchedule

# Add a NoExecute taint to evict untolerated workloads
kubectl taint nodes worker-1 maintenance=true:NoExecute

# Remove a taint (note the trailing minus sign)
kubectl taint nodes worker-1 dedicated=gpu:NoSchedule-
```

#### Pod Manifest with Matching Toleration
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ml-job
spec:
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "gpu"
    effect: "NoSchedule"
  # Delayed eviction toleration for maintenance
  - key: "maintenance"
    operator: "Exists"
    effect: "NoExecute"
    tolerationSeconds: 3600    # Stay on node for 1 hour before being evicted
  containers:
  - name: trainer
    image: pytorch/pytorch:latest
```

---

## 19. Application Health Checks: Startup, Liveness & Readiness Probes

### 19.1 Why Container Status "Running" Is Insufficient
In a naive Docker setup, as long as the primary process PID 1 is alive, the container runtime reports the container as healthy. However, in enterprise distributed applications, a process can be:
- Deadlocked in an infinite loop or locked on database thread pools.
- Still initializing and warming up caches/JVM classes (unable to serve traffic for 60+ seconds).
- Out of critical resources (e.g., exhausted database connection pool).

If Kubernetes relied solely on process state, client traffic would be routed to unready containers, resulting in `HTTP 502 Bad Gateway` or `504 Gateway Timeout` errors.

Kubernetes solves this with **Probes**: periodic diagnostic checks performed by the `kubelet` directly on containers.

---

### 19.2 The Three Kubernetes Probe Types

#### 1. Startup Probe
- **Purpose**: Determines whether a slow-starting application has completed its initial bootstrapping.
- **Key Behavior**: When configured, **it completely disables Liveness and Readiness checks until it succeeds**. This prevents the `kubelet` from prematurely killing slow-booting legacy Java/Spring Boot applications before they have finished initialization.
- **On Failure**: If the Startup Probe exceeds its `failureThreshold`, the kubelet kills the container and initiates restarts according to `restartPolicy`.

#### 2. Liveness Probe
- **Purpose**: Determines whether the application container is healthy and actively functioning.
- **Key Behavior**: Detects deadlocks and internal memory corruptions where the process is running but cannot recover without a restart.
- **On Failure**: The `kubelet` kills the container and automatically initiates a restart according to `restartPolicy`.

#### 3. Readiness Probe
- **Purpose**: Determines whether the application is currently ready to accept incoming client network traffic.
- **Key Behavior**: If a container is temporarily overloaded, running heavy background calculations, or re-establishing a lost database connection, the Readiness Probe fails.
- **On Failure**: **The container is NOT killed**. Instead, the `kubelet` notifies the endpoints controller, which **immediately removes the Pod's IP address from all Service Endpoints**. Incoming client traffic is safely routed only to other healthy replicas until the probe passes again.

---

### 19.3 Probe Detection Mechanisms (Handlers)
1. **`httpGet`**: Performs an HTTP `GET` request against the Pod’s IP address on a specified port and path. Any response with a status code between **200 and 399** is considered a success.
2. **`tcpSocket`**: Attempts to open a TCP socket connection to a specified port on the container. If the connection can be established, the probe is successful. (Common for databases, Redis, message brokers).
3. **`exec`**: Runs a diagnostic command directly inside the container namespace. If the command exits with **status code 0**, the probe succeeds.

---

### 19.4 Probe Configuration Parameters
- **`initialDelaySeconds`**: Number of seconds after the container starts before liveness/readiness probes are initiated (gives app time to boot).
- **`periodSeconds`**: How often (in seconds) to perform the probe check (default: 10s).
- **`timeoutSeconds`**: Number of seconds after which the probe times out (default: 1s).
- **`successThreshold`**: Minimum consecutive successes required to mark the probe successful after a failure (default: 1).
- **`failureThreshold`**: Number of consecutive failures required to declare the probe failed and trigger remediation (default: 3).

---

### 19.5 Comprehensive Production Probes Manifest
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: production-app-probes
spec:
  containers:
  - name: web-app
    image: my-registry/enterprise-app:v2.1
    ports:
    - containerPort: 8080

    # 1. Startup Probe: Allow up to 120s for slow boot (30 * 4s)
    startupProbe:
      httpGet:
        path: /healthz/startup
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 4
      failureThreshold: 30

    # 2. Liveness Probe: Verify process health every 10s
    livenessProbe:
      httpGet:
        path: /healthz/liveness
        port: 8080
      periodSeconds: 10
      timeoutSeconds: 2
      failureThreshold: 3

    # 3. Readiness Probe: Verify traffic readiness every 5s
    readinessProbe:
      httpGet:
        path: /healthz/ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 2
      failureThreshold: 2
```

---

## 20. Helm: Kubernetes Package Management & Release Lifecycle

### 20.1 Why Helm?
Managing raw, static Kubernetes YAML files across multiple environments (Dev, QA, Staging, Prod) quickly becomes an unmanageable maintenance burden. A production microservice typically requires a Deployment, Service, ConfigMap, Secret, HPA, Ingress, and ServiceAccount—resulting in hundreds of lines of duplicated YAML with hardcoded values.

**Helm** is the official package manager for Kubernetes (analogous to `apt` for Debian/Ubuntu or `npm` for Node.js). Helm bundles related Kubernetes resources into a unified, version-controlled package called a **Helm Chart**.

#### Key Benefits of Helm
1. **Dynamic Templating**: Write manifests once using Go template syntax and inject environment-specific variables from a `values.yaml` file.
2. **Release Management**: Every installation or update creates an incremental, tracked **Release Revision**.
3. **One-Command Rollbacks**: Revert an entire distributed microservice deployment to a prior working release with a single CLI command (`helm rollback`).
4. **Dependency Management**: Declare and bundle third-party architecture dependencies (e.g., your web app automatically pulling in a Bitnami PostgreSQL or Redis chart).

---

### 20.2 Helm Chart Directory Structure
Generate a standard chart skeleton using `helm create mychart`:
```
mychart/
├── Chart.yaml          # Metadata: chart name, version, description, appVersion
├── values.yaml         # Default configuration values for templates
├── charts/             # Directory containing chart dependency archives
├── templates/          # Parameterized Kubernetes YAML template files
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── serviceaccount.yaml
│   ├── hpa.yaml
│   ├── ingress.yaml
│   ├── _helpers.tpl    # Reusable template partials and named snippets
│   └── NOTES.txt       # User guide displayed in CLI upon chart installation
```

#### Understanding `Chart.yaml`
```yaml
apiVersion: v2
name: payment-service
description: Enterprise Payment Gateway Microservice
type: application
version: 1.4.0        # The version of the Helm chart itself (SemVer)
appVersion: "2.8.1"   # The version of the application running inside the container
```

---

### 20.3 Go Templating Engine Syntax & Values Injection
Inside `templates/deployment.yaml`, hardcoded values are replaced with template directives referencing values passed from `values.yaml`:

#### `values.yaml`:
```yaml
replicaCount: 3
image:
  repository: nginx
  tag: "1.26"
  pullPolicy: IfNotPresent
service:
  type: ClusterIP
  port: 80
```

#### `templates/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-deploy
  labels:
    app.kubernetes.io/name: {{ .Chart.Name }}
    app.kubernetes.io/instance: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ .Chart.Name }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ .Chart.Name }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: {{ .Values.service.port }}
```

---

### 20.4 Essential Helm CLI Operations
```bash
# 1. Add and update community chart repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 2. Search for available packages
helm search repo nginx

# 3. Install a chart release with custom overrides
helm install my-web bitnami/nginx \
  --set replicaCount=4 \
  --set service.type=NodePort \
  --namespace production --create-namespace

# 4. Install using an environment-specific values file
helm install my-web bitnami/nginx -f values-prod.yaml -n production

# 5. Check status of installed releases
helm list -A

# 6. Upgrade a release (e.g., scaling replicas or updating image)
helm upgrade my-web bitnami/nginx --set replicaCount=6 -n production

# 7. View release revision history
helm history my-web -n production
# REVISION  UPDATED                   STATUS      CHART        DESCRIPTION
# 1         Wed Jun 10 10:00:00 2026  superseded  nginx-18.0.0 Install complete
# 2         Wed Jun 10 10:30:00 2026  deployed    nginx-18.0.0 Upgrade complete

# 8. Rollback to Revision 1 instantly
helm rollback my-web 1 -n production

# 9. Uninstall release and delete all associated cluster resources
helm uninstall my-web -n production
```

---

## 21. Kubernetes Monitoring & Observability: Prometheus, Grafana & Exporters

### 21.1 Prometheus Pull-Based Architecture
Effective cluster operations require real-time visibility into infrastructure health, container performance, and application business metrics. **Prometheus** is the CNCF graduated monitoring and alerting platform standard for cloud-native systems.

Unlike traditional push-based monitoring agents, Prometheus operates on a **Pull-Based Metrics Scraping Architecture**:
1. Target workloads and exporters expose an HTTP endpoint (typically `/metrics`) serving metrics in open plain-text Prometheus format.
2. The Prometheus Server periodically connects to each registered target over HTTP and "scrapes" (pulls) current metrics into its internal time-series database (TSDB).
3. Cluster targets are discovered automatically using the Kubernetes API (`ServiceMonitor`, `PodMonitor`, or node discovery annotations).

![][image32]

---

### 21.2 The Three Pillars of Kubernetes Exporters

#### 1. Node Exporter (Host Metrics)
Runs as a **DaemonSet** on every worker node (listening on port **9100**).
- Gathers hardware and OS kernel metrics directly from the host `/proc` and `/sys` filesystems.
- **Monitors**: Host CPU utilization, RAM usage, disk I/O saturation, network interface drops, filesystem capacity.

#### 2. cAdvisor (Container Resource Telemetry)
Built directly into the core `kubelet` binary on every node (accessible on port **10250**).
- Analyzes container cgroup resource consumption.
- **Monitors**: Exact CPU core seconds consumed per container, memory working set bytes, network bandwidth per container network namespace.

#### 3. `kube-state-metrics` (Cluster Object States)
Deploys as a lightweight standalone Deployment listening on port **8080**.
- Listens to the Kubernetes API server and generates metrics regarding the *state* of objects.
- **Monitors**: Number of desired vs available deployment replicas, pods in `CrashLoopBackOff`, node `Ready` conditions, PersistentVolume remaining capacity, container restart counts.

---

### 21.3 Deploying the Monitoring Stack with Helm (`kube-prometheus-stack`)
The industry standard method for deploying monitoring is the official `kube-prometheus-stack` Helm chart, which packages the Prometheus Operator, Alertmanager, Grafana, Node Exporter, and kube-state-metrics into an integrated deployment.

```bash
# Add prometheus-community chart repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install monitoring stack into dedicated namespace
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.service.type=NodePort \
  --set prometheus.service.type=NodePort
```

---

### 21.4 PromQL (Prometheus Query Language) Deep Dive
PromQL enables rich analytical queries against multidimensional time-series metrics.

#### Core Metric Types
- **Counter**: Cumulative metric that only increases (or resets to zero on restart). Example: `http_requests_total`. Always query counters using `rate()` or `increase()`.
- **Gauge**: Metric that represents a single numerical value that can arbitrarily go up or down. Example: `node_memory_MemAvailable_bytes`.

#### Essential Production PromQL Queries

1. **Calculate Cluster-Wide Node CPU Utilization Percentage**:
```promql
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```
*(Calculates percentage of time the CPU was NOT idle over the last 5 minutes).*

2. **Calculate Node Memory Usage Percentage**:
```promql
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

3. **Container Memory Usage by Pod**:
```promql
sum(container_memory_working_set_bytes{container!=""}) by (pod, namespace)
```

4. **Detecting Pod Crash Loops (Restarts > 5 in last hour)**:
```promql
increase(kube_pod_container_status_restarts_total[1h]) > 5
```

5. **Top 5 Memory-Consuming Pods in Cluster**:
```promql
topk(5, sum(container_memory_usage_bytes{container!=""}) by (pod))
```

---

### 21.5 Grafana Visualizations & Dashboards
Grafana connects to Prometheus as a data source and renders real-time visual dashboards.
- **Accessing Grafana**: Exposed via NodePort or Ingress. Default login: `admin` / `prom-operator`.
- **Community Dashboard Imports**: Instead of manually building charts, import official community dashboards via Dashboard ID:
  - **Dashboard ID `1860`**: *Node Exporter Full* (Comprehensive host CPU, RAM, disk, network, and temperature graphs).
  - **Dashboard ID `315`**: *Kubernetes Cluster Monitoring* (Cluster capacity, pod counts, and resource allocations).
  - **Dashboard ID `6417`**: *Kubernetes Deployments / StatefulSets overview*.

---

## 22. Production Monitoring Infrastructure: 2-VM Architecture

In high-reliability enterprise environments, running monitoring infrastructure inside the very cluster it monitors introduces a dangerous circular dependency: **if the Kubernetes cluster experiences network partition, etcd deadlock, or total node crash, the monitoring system goes down simultaneously, blinding operations teams to the failure**.

To eliminate this single point of failure, production architectures deploy a dedicated, external monitoring server.

![][image33]

---

### 22.1 VM 1: Application Server Setup
VM 1 hosts the production business workload (e.g., a Java Spring Boot Todo App running on port 8080) and exposes host OS telemetry:
```bash
# Install and enable Node Exporter on Application Server
sudo apt update
sudo apt install -y prometheus-node-exporter
sudo systemctl enable --now prometheus-node-exporter
```
Verify metrics are accessible locally on port 9100:
```bash
curl http://localhost:9100/metrics
```

---

### 22.2 VM 2: Monitoring Server Setup
VM 2 is an independent VM running:
1. **Prometheus Server**: Scrapes metrics from VM 1.
2. **Blackbox Exporter**: Performs synthetic endpoint probing (testing if `http://<APP_VM_IP>:8080` responds with `HTTP 200 OK`).
3. **Alertmanager**: Routes alerts to Slack or email when services fail.

#### Installing Monitoring Components
```bash
sudo apt update
sudo apt install -y prometheus prometheus-blackbox-exporter prometheus-alertmanager grafana
```

#### Configuring `prometheus.yml` Scrape Targets
Edit `/etc/prometheus/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/alert.rules.yml"

alerting:
  alertmanagers:
  - static_configs:
    - targets: ['localhost:9093']

scrape_configs:
  # 1. Scrape Host OS Metrics from App VM
  - job_name: 'app-server-host'
    static_configs:
    - targets: ['172.31.25.100:9100']

  # 2. Blackbox HTTP Synthetic Probe for Java Todo Application
  - job_name: 'todo-app-probe'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
        - http://172.31.25.100:8080
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 127.0.0.1:9115  # Blackbox exporter address
```

#### Defining Alerting Rules (`alert.rules.yml`)
```yaml
groups:
- name: application-alerts
  rules:
  - alert: TodoApplicationDown
    expr: probe_success == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Java Todo Application on App Server is DOWN"
      description: "Blackbox probe failed to receive HTTP 2xx from http://172.31.25.100:8080 for over 1 minute."

  - alert: HighServerMemoryUsage
    expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "App Server Memory usage exceeds 90%"
```

#### Configuring Alertmanager Notification Channel (`alertmanager.yml`)
```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'slack-notifications'
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
- name: 'slack-notifications'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/T00/B00/XXXXX'
    channel: '#production-alerts'
    send_resolved: true
    text: "Alert: {{ .CommonAnnotations.summary }}\nDescription: {{ .CommonAnnotations.description }}"
```

---

## 23. AWS EKS Architecture: Provisioning, Access Patterns, Ingress & Add-ons

### 23.1 Enterprise AWS EKS Architecture & Provisioning (`eksctl`)
**Amazon Elastic Kubernetes Service (EKS)** delivers a managed, production-grade Kubernetes control plane. AWS manages the scaling, multi-AZ high availability (spanning 3 separate Availability Zones), and automated security patching of the `kube-apiserver` and `etcd` cluster behind an AWS-managed Network Load Balancer (NLB).

#### Prerequisite Tooling Installation
Before provisioning or managing an EKS cluster, the required client toolchain must be installed:
- **AWS CLI v2**: Configured with IAM administrative credentials.
- **`eksctl`**: The official CLI tool developed by AWS and Weaveworks for creating and managing EKS clusters.
- **`kubectl`**: The Kubernetes CLI used to manage container workloads.

##### Installation on Windows (via Chocolatey)
```cmd
:: Open cmd.exe as Administrator
:: Install eksctl
choco install -y eksctl

:: Install kubectl
choco install -y kubernetes-cli
```

##### Installation on Linux
Download and install the official standalone binaries or use standard repository packages:
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

#### Provisioning the Cluster with `eksctl`
Execute the following command to bootstrap a production-ready EKS cluster with dedicated worker nodes:
```bash
eksctl create cluster \
  --name eks-cluster \
  --version 1.36 \
  --with-oidc \
  --nodegroup-name worker \
  --region us-east-1 \
  --node-type t2.medium \
  --ssh-access \
  --ssh-public-key nagaraj
```

##### Key Provisioning Parameters Explained
| Flag | Engineering Purpose |
| :--- | :--- |
| `--name eks-cluster` | Identifies the EKS cluster in the AWS account. |
| `--version 1.36` | Specifies the targeted Kubernetes minor version. |
| `--with-oidc` | Configures the **IAM OpenID Connect (OIDC) provider**, required for IRSA (IAM Roles for Service Accounts). |
| `--nodegroup-name worker` | Creates a managed EC2 Auto Scaling group for worker nodes. |
| `--region us-east-1` | Sets the AWS region hosting the control plane and data plane. |
| `--node-type t2.medium` | Hardware sizing for worker instances (2 vCPUs, 4 GiB RAM). |
| `--ssh-access --ssh-public-key` | Injects SSH keypair for direct host-level access to worker nodes. |

#### Updating Kubeconfig
Once cluster provisioning completes, configure your local client context:
```bash
aws eks update-kubeconfig --region us-east-1 --name eks-cluster
kubectl get nodes -o wide
```

#### Cluster Cleanup & Teardown
To prevent ongoing cloud infrastructure costs when labs or testing finish:
```bash
eksctl delete cluster --name eks-cluster --region us-east-1
```

---

### 23.2 Three Authentication & Access Patterns to Amazon EKS
Kubernetes has no internal database of AWS IAM Users or Roles. EKS integrates AWS IAM with Kubernetes RBAC through a three-stage authorization flow:

1. **IAM Permission**: The IAM identity requires permission to execute `eks:DescribeCluster`.
2. **Cluster Authorization**: The IAM identity's ARN must be explicitly mapped inside the `aws-auth` ConfigMap in the `kube-system` namespace.
3. **Kubernetes Permissions**: The mapped entry binds the IAM entity to internal Kubernetes RBAC groups (such as `system:masters` for full cluster administration or a custom role group).

```
   [AWS CLI / kubectl] 
          │  (Presents STS Presigned Token via GetCallerIdentity)
          ▼
   [EKS API Server] 
          │  (Validates IAM Identity via AWS IAM Authenticator)
          ▼
   [aws-auth ConfigMap (kube-system)]
          │  (Maps IAM ARN to internal User & RBAC Group)
          ▼
   [Kubernetes RBAC Engine] ──► Allow / Deny Operation
```

#### Method 1: Direct IAM User Access (`eks-direct`)
In this pattern, credentials (Access Key ID and Secret Access Key) belong directly to an individual IAM user.

##### Step 1: Create IAM User
```bash
aws iam create-user --user-name eks-direct
```

##### Step 2: Attach Inline EKS Describe Policy
Create `eks-describe-only-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "eks:DescribeCluster",
      "Resource": "*"
    }
  ]
}
```
Attach the policy to the IAM user:
```bash
aws iam put-user-policy \
  --user-name eks-direct \
  --policy-name EKSDescribeOnly \
  --policy-document file://eks-describe-only-policy.json
```

##### Step 3: Generate Access Keys & Configure AWS CLI Profile
```bash
aws iam create-access-key --user-name eks-direct
```
Configure a dedicated AWS CLI profile for this identity:
```bash
aws configure --profile eks-direct
# Enter Access Key ID, Secret Access Key, Default region (e.g., ap-south-1), and Output format (json)
```

##### Step 4: Map User in `aws-auth` ConfigMap
As a cluster administrator, edit the `aws-auth` ConfigMap:
```bash
kubectl edit configmap aws-auth -n kube-system
```
Add the `mapUsers` section:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::<ACCOUNT_ID>:role/worker-node-role
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
  mapUsers: |
    - userarn: arn:aws:iam::<ACCOUNT_ID>:user/eks-direct
      username: eks-direct
      groups:
        - system:masters
```

##### Step 5: Verify Access
```bash
aws eks update-kubeconfig --region ap-south-1 --name eks-cluster --profile eks-direct
kubectl get nodes
```

---

#### Method 2: IAM User Assuming a Role (`eks-role` → `eks-cluster-role`)
The **AssumeRole pattern** is the recommended enterprise security standard. Instead of assigning cluster-admin privileges to permanent user credentials, the user requests temporary STS session credentials by assuming an authorized role.

##### Step 1: Create the User
```bash
aws iam create-user --user-name eks-role
aws iam create-access-key --user-name eks-role
aws configure --profile eks-role
```

##### Step 2: Create the IAM Role with User Trust Policy
Create `trust-policy-user.json` defining which IAM principal can assume this role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<ACCOUNT_ID>:user/eks-role"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```
Create the IAM role:
```bash
aws iam create-role \
  --role-name eks-cluster-role \
  --assume-role-policy-document file://trust-policy-user.json
```

##### Step 3: Attach EKS Describe Policy to the Role
```bash
aws iam put-role-policy \
  --role-name eks-cluster-role \
  --policy-name EKSDescribeOnly \
  --policy-document file://eks-describe-only-policy.json
```

##### Step 4: Allow User to Assume the Role
Create `assume-role-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::<ACCOUNT_ID>:role/eks-cluster-role"
    }
  ]
}
```
Attach permission to the user:
```bash
aws iam put-user-policy \
  --user-name eks-role \
  --policy-name AssumeEKSClusterRole \
  --policy-document file://assume-role-policy.json
```

##### Step 5: Map the Role in `aws-auth` ConfigMap
```bash
kubectl edit configmap aws-auth -n kube-system
```
Add the role under `mapRoles`:
```yaml
data:
  mapRoles: |
    - rolearn: arn:aws:iam::<ACCOUNT_ID>:role/eks-cluster-role
      username: eks-cluster-role
      groups:
        - system:masters
```

##### Step 6: Configure AWS CLI Profile with Role Chaining
Edit `~/.aws/config` to define an automated assume-role profile:
```ini
[profile eks-role-access]
role_arn = arn:aws:iam::<ACCOUNT_ID>:role/eks-cluster-role
source_profile = eks-role
region = ap-south-1
```
Update kubeconfig and verify:
```bash
aws eks update-kubeconfig --region ap-south-1 --name eks-cluster --profile eks-role-access
kubectl get nodes
```

---

#### Method 3: EC2 Instance with IAM Role (`eks-bastion-cluster-role`)
For management bastion hosts, Jenkins build agents, or automated CI/CD runners running inside AWS, storing static IAM access keys is a major security hazard. Instead, attach an **IAM Instance Profile** directly to the EC2 instance.

##### Step 1: Create EC2 Trust Policy (`trust-policy-ec2.json`)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

##### Step 2: Create IAM Role & Attach Policy
```bash
aws iam create-role \
  --role-name eks-bastion-cluster-role \
  --assume-role-policy-document file://trust-policy-ec2.json

aws iam put-role-policy \
  --role-name eks-bastion-cluster-role \
  --policy-name EKSDescribeOnly \
  --policy-document file://eks-describe-only-policy.json
```

##### Step 3: Create Instance Profile & Attach to Bastion EC2
```bash
# Create instance profile
aws iam create-instance-profile --instance-profile-name eks-bastion-instance-profile

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name eks-bastion-instance-profile \
  --role-name eks-bastion-cluster-role

# Attach to running EC2 instance
aws ec2 associate-iam-instance-profile \
  --instance-id <BASTION_INSTANCE_ID> \
  --iam-instance-profile Name=eks-bastion-instance-profile
```

##### Step 4: Map Role in `aws-auth` ConfigMap
```bash
kubectl edit configmap aws-auth -n kube-system
```
Add under `mapRoles`:
```yaml
data:
  mapRoles: |
    - rolearn: arn:aws:iam::<ACCOUNT_ID>:role/eks-bastion-cluster-role
      username: eks-bastion-cluster-role
      groups:
        - system:masters
```

##### Step 5: Test from Bastion Host
SSH into the bastion host. Because the instance receives temporary credentials automatically from the EC2 metadata service (IMDS), no `aws configure` credentials are required:
```bash
aws eks update-kubeconfig --region ap-south-1 --name eks-cluster
kubectl get nodes
```

---

### 23.3 Granular Kubernetes RBAC & Custom Read-Only Access
Granting `system:masters` gives full cluster-admin control over the entire cluster. In production, team members should be granted **least-privilege read-only access**.

#### Step 1: Create Read-Only ClusterRole and ClusterRoleBinding
Save as `readonly-rbac.yaml`:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: developer-read-only
rules:
- apiGroups: ["", "apps", "batch", "networking.k8s.io"]
  resources: ["pods", "services", "deployments", "configmaps", "namespaces", "ingresses"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: bind-read-only-users
subjects:
- kind: Group
  name: readonly-group
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: developer-read-only
  apiGroup: rbac.authorization.k8s.io
```
Apply the RBAC manifest:
```bash
kubectl apply -f readonly-rbac.yaml
```

#### Step 2: Map Identity to `readonly-group` in `aws-auth`
Update `aws-auth` to map developers into `readonly-group` rather than `system:masters`:
```yaml
  mapUsers: |
    - userarn: arn:aws:iam::<ACCOUNT_ID>:user/developer-user
      username: developer-user
      groups:
        - readonly-group
```
Verification:
```bash
# This succeeds:
kubectl get pods -A

# This is blocked by RBAC:
kubectl delete pod nginx-pod
# Error from server (Forbidden): pods "nginx-pod" is forbidden: User "developer-user" cannot delete resource "pods"
```

---

### 23.4 AWS Load Balancer Controller (ALB/NLB), Subnet Tagging & ExternalDNS
The **AWS Load Balancer Controller** is an open-source Kubernetes controller that provisions and manages AWS Elastic Load Balancers (ALB for Layer 7 Ingress, NLB for Layer 4 Service) dynamically in response to Kubernetes resource events.

#### Step 1: Create IAM Policy for the Controller
Download the official IAM policy JSON and create the IAM policy:
```bash
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json
```

#### Step 2: Create IAM Service Account (IRSA) via `eksctl`
Link the IAM policy to a Kubernetes ServiceAccount using OIDC:
```bash
eksctl create iamserviceaccount \
  --cluster=eks-cluster \
  --namespace=alb \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::<ACCOUNT_ID>:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve \
  --region=ap-south-1
```

#### Step 3: Install AWS Load Balancer Controller via Helm
```bash
# Add official EKS charts repository
helm repo add eks https://aws.github.io/eks-charts
helm repo update eks

# Deploy the controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n alb --create-namespace \
  --set clusterName=eks-cluster \
  --set serviceAccount.create=false \
  --set vpcId=<VPC_ID> \
  --set region=ap-south-1 \
  --set serviceAccount.name=aws-load-balancer-controller
```

#### Step 4: VPC Subnet Tagging Requirements
For the AWS Load Balancer Controller to automatically discover and provision ALBs in the correct VPC subnets, AWS subnets must be properly tagged:

##### 1. Cluster Ownership Tag (All Subnets in Cluster VPC)
```bash
aws ec2 create-tags --resources <SUBNET_ID_1> <SUBNET_ID_2> \
  --tags Key=kubernetes.io/cluster/eks-cluster,Value=shared
```

##### 2. Public Subnet Tag (For Internet-Facing ALBs)
Public subnets (subnets with an Internet Gateway route) must have:
```bash
aws ec2 create-tags --resources <PUBLIC_SUBNET_ID_1> <PUBLIC_SUBNET_ID_2> \
  --tags Key=kubernetes.io/role/elb,Value=1
```

##### 3. Private Subnet Tag (For Internal ALBs)
Private subnets (subnets with NAT Gateway routes) must have:
```bash
aws ec2 create-tags --resources <PRIVATE_SUBNET_ID_1> <PRIVATE_SUBNET_ID_2> \
  --tags Key=kubernetes.io/role/internal-elb,Value=1
```

#### Step 5: Automated DNS Management with ExternalDNS
**ExternalDNS** dynamically synchronizes exposed Kubernetes Ingresses and Services with DNS providers like AWS Route 53.

```bash
# Add Bitnami Helm repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install ExternalDNS
helm install external-dns bitnami/external-dns \
  --set provider=aws \
  --set aws.region=ap-south-1 \
  --set aws.credentials.secretKey="<AWS_SECRET_KEY>" \
  --set aws.credentials.accessKey="<AWS_ACCESS_KEY>" \
  --set aws.zoneType=public \
  --set "domainFilters[0]=example.com" \
  --set policy=upsert-only \
  --set txtOwnerId="eks-cluster-externaldns" \
  --set logLevel=info \
  --namespace kube-system
```

#### Step 6: Hands-On Application & Ingress Deployment
Deploy a backend application and expose it via an AWS Application Load Balancer.

##### Application Deployment & Service (`hello.yaml`)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: helloworld
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      name: hello
      labels:
        app: hello
    spec:
      containers:
      - name: hello-container
        image: artisantek/k8s-helloworld:latest
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: hello
spec:
  type: LoadBalancer
  selector:
    app: hello
  ports:
  - targetPort: 8080
    port: 8080
```

##### ALB Ingress Manifest (`ingress.yaml`)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hello
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  ingressClassName: alb
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hello
            port:
              number: 8080
```
```bash
kubectl apply -f hello.yaml
kubectl apply -f ingress.yaml
kubectl get ingress hello
# ADDRESS: k8s-alb-xxxx.ap-south-1.elb.amazonaws.com
```

---

### 23.5 Official Kubernetes Dashboard Deployment & Authentication
The **Kubernetes Dashboard** is a web-based user interface for inspecting workloads, monitoring container resource metrics, and executing administrative workflows.

#### Step 1: Install Kubernetes Metrics Server
The Metrics Server collects CPU and memory usage from node `kubelet` summary APIs and is a prerequisite for dashboard telemetry and the Horizontal Pod Autoscaler (HPA):
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

#### Step 2: Install Kubernetes Dashboard via Helm
```bash
# Add official repository
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
helm repo update

# Install Dashboard release
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard \
  --create-namespace \
  --namespace kubernetes-dashboard
```

#### Step 3: Accessing the Dashboard UI
Depending on your cluster environment, the dashboard can be accessed using either of the following approaches:

##### On Bare-Metal / Kubeadm Clusters (NodePort Exposure)
```bash
kubectl expose service kubernetes-dashboard-kong-proxy \
  --type=NodePort \
  --target-port=8443 \
  --name=dashboard-nodeport \
  -n kubernetes-dashboard

# Access UI in browser at:
# https://<WORKER_NODE_IP>:<NODEPORT>
```

##### On Amazon EKS (Secure `kubectl proxy`)
```bash
kubectl proxy
```
Open the following URL directly in your local browser:
```
http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

#### Step 4: Configuring Cluster-Admin Authentication
To authenticate against the dashboard with full administrative permissions, create a dedicated `ServiceAccount`, generate a long-lived bearer token secret, and bind it to `cluster-admin`.

Save as `dashboard-admin.yaml`:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dashboard
  namespace: kubernetes-dashboard
---
apiVersion: v1
kind: Secret
metadata:
  name: dashboard-sa-token
  namespace: kubernetes-dashboard
  annotations:
    kubernetes.io/service-account.name: "dashboard"
type: kubernetes.io/service-account-token
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: crb
subjects:
- kind: ServiceAccount
  name: dashboard
  namespace: kubernetes-dashboard
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
```
Apply the manifest:
```bash
kubectl apply -f dashboard-admin.yaml
```

#### Step 5: Extract Bearer Token
```bash
kubectl get secret dashboard-sa-token -n kubernetes-dashboard -o jsonpath="{.data.token}" | base64 -d
```
Copy the decoded token string and paste it into the Kubernetes Dashboard login prompt.

#### Teardown / Cleanup
```bash
kubectl delete ns kubernetes-dashboard
```

---

### 23.6 AWS EBS & EFS CSI Drivers (Dynamic Cloud Storage)

#### 1. AWS EBS CSI Driver (Block Storage - `ReadWriteOnce`)
The Amazon EBS Container Storage Interface (CSI) driver allows Kubernetes to dynamically provision AWS EBS volumes (such as `gp3`) as PersistentVolumes.

##### Step 1: Identify Worker Node Role in `aws-auth`
```bash
kubectl -n kube-system describe configmap aws-auth
```
Identify the IAM role ARN attached under `mapRoles` (e.g., `eksctl-eks-cluster-nodegroup-worker-NodeInstanceRole-XXXX`).

##### Step 2: Attach `AmazonEBSCSIDriverPolicy` to the Node Role
Attach the AWS managed policy to allow worker instances to interact with EC2 EBS volume APIs:
```bash
aws iam attach-role-policy \
  --role-name <WORKER_NODE_ROLE_NAME> \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy
```

##### Step 3: Deploy the EBS CSI Driver
Deploy the official CSI driver overlay using Kustomize:
```bash
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver
```

##### Step 4: Define Dynamic EBS StorageClass
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
parameters:
  type: gp3
  encrypted: "true"
```
> [!IMPORTANT]
> Always set `volumeBindingMode: WaitForFirstConsumer`. This ensures the EBS volume is provisioned in the specific Availability Zone where the pod is scheduled, avoiding cross-AZ attach failures.

#### 2. AWS EFS CSI Driver (Shared File System - `ReadWriteMany`)
While EBS is limited to `ReadWriteOnce` (a block device can only attach to a single node at a time), **Amazon Elastic File System (EFS)** enables multi-pod, multi-node shared persistent storage (`ReadWriteMany`).
- **Architecture**: EFS provisions mount targets (ENIs) across each Availability Zone in your VPC.
- **Access Mode**: Multiple pods across different worker nodes read and write to the same shared directory concurrently.
- **Enterprise Use Cases**: WordPress `wp-content` directories, machine learning training datasets, shared CI/CD artifact caches, and distributed CMS platforms.

---

## 24. Advanced Kubernetes Engineering Modules

---

### 24.1 Horizontal Pod Autoscaler (HPA)

#### Overview & Autoscaling Mechanics
The **Horizontal Pod Autoscaler (HPA)** automatically scales the number of Pod replicas in a Deployment, ReplicaSet, or StatefulSet based on observed compute metrics (such as CPU or Memory utilization) or custom/external metrics (such as HTTP requests per second or message queue depth).

#### Prerequisites: Kubernetes Metrics Server
HPA relies on the Kubernetes Metrics API (`metrics.k8s.io`). The **Metrics Server** must be installed in the cluster to collect CPU/memory metrics from `cAdvisor` on each worker node:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```
Verify the metrics server is operational:
```bash
kubectl top nodes
kubectl top pods
```

#### The HPA Autoscaling Algorithm
The HPA controller runs periodically (default every 15 seconds) and calculates the target replica count using the following formula:

$$\text{Desired Replicas} = \left\lceil \text{Current Replicas} \times \left( \frac{\text{Current Metric Value}}{\text{Desired Metric Value}} \right) \right\rceil$$

For example, if current replicas = 4, target CPU utilization is 50%, and current average CPU utilization across pods is 75%:
$$\text{Desired Replicas} = \left\lceil 4 \times \left( \frac{75}{50} \right) \right\rceil = \lceil 4 \times 1.5 \rceil = 6 \text{ replicas}$$

#### Production HPA Manifest (`hpa.yaml`)
> [!IMPORTANT]
> For HPA to function, all containers in the targeted workload **must** define `resources.requests.cpu` (and/or memory). Without requests, HPA cannot calculate percentage utilization and will report `unknown`.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app-deploy
  minReplicas: 2
  maxReplicas: 10
  metrics:
  # 1. Target average CPU utilization at 70%
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  # 2. Target average Memory utilization at 80%
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    # Custom scaling velocity policies to prevent flapping
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300   # Wait 5 mins before scaling down
      policies:
      - type: Percent
        value: 20
        periodSeconds: 60
```

---

### 24.2 Ingress & AWS Load Balancer Controller

#### Ingress vs. Service Abstraction
While `NodePort` and `LoadBalancer` services operate at Layer 4 (TCP/UDP transport layer), **Ingress** operates at **Layer 7 (Application layer)**.
- Provides path-based routing (e.g., `api.example.com/orders` -> `order-svc`, `api.example.com/users` -> `user-svc`).
- Provides host-based virtual hosting (e.g., `billing.example.com` vs `portal.example.com`).
- Manages SSL/TLS termination centrally.
- Reduces cloud costs: A single AWS Application Load Balancer (ALB) can route to dozens of internal services instead of provisioning a separate expensive cloud LB per Service.

#### Production Ingress Manifest with SSL/TLS
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: enterprise-ingress
  namespace: production
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789012:certificate/xxxx-xxxx
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-api-svc
            port:
              number: 8080
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-svc
            port:
              number: 80
```

---

### 24.3 Kubernetes Gateway API

#### The Next Generation of Ingress
The **Kubernetes Gateway API** is the modern evolution of the Ingress API (`gateway.networking.k8s.io`). While Ingress overloaded routing, TLS, and infrastructure provisioning into a single monolithic manifest, the Gateway API cleanly separates roles:
1. **Infrastructure Provider / Platform Ops**: Defines `GatewayClass` (the controller implementation, e.g., Envoy, Istio, AWS VPC Lattice).
2. **Cluster Admin / DevOps**: Deploys `Gateway` objects (defining IP listeners, ports, and TLS certificates).
3. **Application Developer**: Writes `HTTPRoute`, `GRPCRoute`, or `TCPRoute` objects binding specific URL paths to backend Services across different namespaces.

#### Gateway Manifest (`gateway.yaml`)
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: external-gateway
  namespace: gateway-infra
spec:
  gatewayClassName: eg-gateway-class
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      certificateRefs:
      - name: wildcard-example-cert
    allowedRoutes:
      namespaces:
        from: All
```

#### HTTPRoute Manifest with Advanced Header Routing (`httproute.yaml`)
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-routing
  namespace: backend
spec:
  parentRefs:
  - name: external-gateway
    namespace: gateway-infra
  hostnames:
  - "api.example.com"
  rules:
  # Canary rule: Route beta testers to v2 backend
  - matches:
    - headers:
      - name: X-Beta-Tester
        value: "true"
    backendRefs:
    - name: backend-v2-svc
      port: 8080
  # Default production rule with traffic splitting
  - matches:
    - path:
        type: PathPrefix
        value: /v1
    backendRefs:
    - name: backend-v1-svc
      port: 8080
      weight: 90
    - name: backend-v2-svc
      port: 8080
      weight: 10
```

---

### 24.4 Advanced Helm Templating & Best Practices

#### Helm Lifecycle Hooks
Helm allows developers to intervene at critical milestones in a release lifecycle using **Chart Hooks** (annotated with `helm.sh/hook`):
- `pre-install` / `post-install`: Run database migration scripts or seed initial admin accounts before the main application pods boot.
- `pre-upgrade` / `post-upgrade`: Backup databases before rolling out a new release version.
- `pre-delete` / `post-delete`: Clean up external cloud resources before deleting releases.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-db-migration
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: db-migrate
        image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
        command: ["python", "manage.py", "migrate"]
```

---

### 24.5 Batch Processing: Jobs and CronJobs

#### 1. Kubernetes Job
A **Job** creates one or more Pods and ensures that a specified number of them successfully terminate (Exit code 0).
- **`completions`**: Total number of successful pod completions required.
- **`parallelism`**: Maximum number of pods executing simultaneously.
- **`backoffLimit`**: Number of retries before declaring the job failed (default: 6).

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: report-generator
spec:
  completions: 4
  parallelism: 2
  backoffLimit: 3
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: worker
        image: python:3.11-slim
        command: ["python", "-c", "import time; print('Processing batch chunk...'); time.sleep(5)"]
```

#### 2. Kubernetes CronJob
A **CronJob** manages time-based Jobs according to a standard 5-field cron schedule (`minute hour day-of-month month day-of-week`).
- **`concurrencyPolicy`**:
  - `Allow` (Default): Concurrent jobs can run simultaneously.
  - `Forbid`: Skips the new job run if the previous job is still executing.
  - `Replace`: Cancels the currently running job and launches the new one.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: nightly-db-backup
spec:
  schedule: "0 2 * * *"          # Runs every night at 2:00 AM UTC
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: backup
            image: postgres:16
            command: ["pg_dumpall", "-f", "/backup/db.sql"]
```

---

### 24.6 Network Policies & Micro-segmentation

#### Default Open Networking Model
By default, Kubernetes implements a **flat, non-isolated network**: any Pod can communicate with any other Pod across any namespace without restriction. If an unprivileged frontend container is compromised by an attacker, they can probe and attack backend databases directly over the internal network.

A **NetworkPolicy** acts as a distributed firewall (enforced via Linux iptables/eBPF by the CNI, e.g., Calico or Cilium) that isolates pods.

#### Production Default-Deny & Whitelisting NetworkPolicy
```yaml
# 1. Default Deny All Ingress Traffic in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
# 2. Whitelist: Only allow Frontend Pods to communicate with Database on Port 3306
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-db
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: mysql
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend
    ports:
    - protocol: TCP
      port: 3306
```

---

### 24.7 Admission Controllers & Kyverno Policy Engine

#### Kubernetes Dynamic Admission Controllers
Before an object is saved to `etcd`, the API server invokes **Admission Controllers**:
1. **Mutating Webhooks**: Modify or inject defaults into the object (e.g., injecting Istio sidecar proxies, adding default labels).
2. **Validating Webhooks**: Enforce security rules and reject requests that violate policies (e.g., blocking containers running as `root`).

#### Kyverno: Declarative Cloud-Native Policy Engine
Writing custom Golang admission webhooks is complex. **Kyverno** allows administrators to manage validation, mutation, and generation policies as native Kubernetes resources without coding.

#### Kyverno Policy Example: Enforce Resource Limits & Block Root
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: enterprise-security-standards
spec:
  validationFailureAction: Enforce   # Block deployment if rule is violated
  rules:
  # Rule 1: Disallow Privileged Containers
  - name: block-privileged
    match:
      any:
      - resources:
          kinds: ["Pod"]
    validate:
      message: "Privileged containers are strictly forbidden in production."
      pattern:
        spec:
          containers:
          - securityContext:
              privileged: false

  # Rule 2: Enforce Mandatory Resource Limits
  - name: require-limits
    match:
      any:
      - resources:
          kinds: ["Pod"]
    validate:
      message: "All containers must define CPU and Memory limits."
      pattern:
        spec:
          containers:
          - resources:
              limits:
                cpu: "?*"
                memory: "?*"
```

---

### 24.8 Pod Security Standards (PSS) & Pod Security Admission (PSA)

#### The Three Pod Security Standards
Replaced the deprecated PodSecurityPolicies (PSP):
1. **Privileged**: Completely unrestricted. Allows containers full access to host kernel, devices, and namespaces.
2. **Baseline**: Minimally restrictive default. Prevents known privilege escalations while allowing standard default configurations.
3. **Restricted**: Hardened production security. Enforces non-root execution, drops all Linux capabilities except `NET_BIND_SERVICE`, forbids host networking, and restricts volume types.

#### Applying PSA Levels to Namespaces
Pod Security Admission is applied declaratively via Namespace labels across three enforcement modes: `enforce`, `audit`, and `warn`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: banking-workloads
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
```

---

### 24.9 Declarative Configuration with Kustomize

#### Template-Free Declarative Customization
While Helm uses template parameterization, **Kustomize** (built natively into `kubectl` via `kubectl apply -k`) provides template-free customization through a **Base and Overlay** pattern:
- **`base/`**: Standard, reusable manifests.
- **`overlays/`**: Environment-specific patches (Dev, Staging, Prod) that modify replica counts, resource requests, or environment variables without altering the base files.

#### Directory Layout
```
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── dev/
    │   └── kustomization.yaml
    └── prod/
        ├── kustomization.yaml
        └── replica-patch.yaml
```

#### Overlay Configuration (`overlays/prod/kustomization.yaml`)
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- ../../base
namePrefix: prod-
commonLabels:
  environment: production
patches:
- target:
    kind: Deployment
    name: web-app
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 10
```
Deploy the production overlay:
```bash
kubectl apply -k overlays/prod
```

---

### 24.10 Container Storage Interface (CSI) Architecture

#### The Evolution from In-Tree to Out-of-Tree Storage
In early Kubernetes releases, storage volume plugins (AWS EBS, GCE PD, Azure Disk, Ceph) were compiled directly into the core `kubelet` and `kube-controller-manager` binaries (**in-tree**). This made testing, bug-fixing, and vendor upgrades risky and coupled to Kubernetes release cycles.

The **Container Storage Interface (CSI)** standardizes storage plugins as out-of-tree services:
- Storage vendors write standalone containerized plugins implementing standard gRPC specifications:
  1. **CSI Identity Service**: Reports driver metadata and capabilities.
  2. **CSI Controller Service**: Provisions, attaches, snapshots, and resizes storage volumes via cloud APIs.
  3. **CSI Node Service**: Formats and mounts physical storage block devices directly on the worker node.

---

### 24.11 Secrets Store CSI Driver (Vault / AWS Secrets Manager)

#### Eliminating Kubernetes Static Secrets
Storing passwords inside native Kubernetes `Secret` objects leaves sensitive keys vulnerable in `etcd` and local node memory. The **Secrets Store CSI Driver** allows Kubernetes to mount secrets, keys, and certificates stored in enterprise external secrets management vaults directly into Pod volumes:
- **AWS Secrets Manager / AWS Systems Manager Parameter Store**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Secret Manager**

#### Architectural Workflow
1. A pod requesting secrets mounts a volume with CSI driver `secrets-store.csi.k8s.io`.
2. The CSI driver talks directly to the external vault using the Pod's IAM Role / ServiceAccount (IRSA).
3. Secrets are fetched over encrypted TLS and mounted as **in-memory tmpfs files** inside the container.
4. Secrets are never persisted to disk and never stored as plain text inside `etcd`!

#### SecretProviderClass Manifest (`aws-secrets.yaml`)
```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: aws-db-secrets
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "prod/database/credentials"
        objectType: "secretsmanager"
        jmesPath: 
          - path: "username"
            objectAlias: "DB_USER"
          - path: "password"
            objectAlias: "DB_PASS"
---
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
spec:
  serviceAccountName: secure-app-sa
  containers:
  - name: app
    image: my-app:latest
    volumeMounts:
    - name: secrets-store-inline
      mountPath: "/mnt/secrets"
      readOnly: true
  volumes:
  - name: secrets-store-inline
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: "aws-db-secrets"
```
The application reads `/mnt/secrets/DB_USER` and `/mnt/secrets/DB_PASS` at runtime with enterprise-grade security.

---

## 25. Assignments

---

### Assignment 1: Understanding `imagePullPolicy` & Container Lifecycle Integrity

**Question**:
Explain `imagePullPolicy` in Kubernetes, why it is critical for production reliability, its available settings, default resolution rules, and industry best practices.

<details>
<summary><b>View Answer</b></summary>

#### What is `imagePullPolicy`?
`imagePullPolicy` is a Kubernetes container-level configuration setting that determines when the `kubelet` attempts to download (pull) a container image from an external container image registry (such as Docker Hub, Amazon ECR, Google Artifact Registry, or private Harbor registries) onto the local worker node.

It is defined inside a Pod or Deployment specification under `spec.containers[*].imagePullPolicy`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        imagePullPolicy: Always
```

#### Why `imagePullPolicy` Is Critical for Production Reliability
Configuring `imagePullPolicy` correctly directly impacts:
1. **Application Update Predictability**: Ensures that nodes do not run stale image binaries when updates are released.
2. **Cluster Startup Speed**: Caching images locally prevents multi-gigabyte downloads during horizontal autoscaling events.
3. **Network Bandwidth & Registry Rate Limits**: Prevents exceeding public registry rate limits (e.g., Docker Hub pull limits).
4. **Resilience During Registry Outages**: If an external registry experiences an outage, nodes with cached images can still restart containers if policy permits.

#### The Three Available Policy Values

| Policy Value | Operational Behavior | Recommended Environment | Advantages & Trade-Offs |
| :--- | :--- | :--- | :--- |
| **`Always`** | The `kubelet` contacts the registry on **every single container start** to resolve the image digest. If a newer image digest exists, it downloads it; if identical, it uses the cached version. | Development, Staging, CI/CD builds, or when using mutable tags (`latest`). | **Advantage**: Guaranteed to run the newest build.<br>**Disadvantage**: Slower startup latency; fails to start if external registry is unreachable. |
| **`IfNotPresent`** | The `kubelet` checks if the image exists in the local node cache. If present, it uses the local image **without querying the registry**. It only pulls over the network if the image is missing locally. | **Production Workloads** with immutable semantic version tags (e.g., `v1.4.2`). | **Advantage**: Maximum startup velocity, zero registry bandwidth overhead.<br>**Disadvantage**: Re-tagging an existing version will NOT update running nodes. |
| **`Never`** | The `kubelet` **never** queries the registry or attempts a network download. It strictly expects the image to have been pre-loaded onto the node. | Air-gapped secure networks, edge devices, local development (Minikube / KinD). | **Advantage**: 100% offline isolation.<br>**Disadvantage**: Pod crashes with `ErrImageNeverPull` if image is missing from node. |

#### Default Resolution Rules in Kubernetes
If an operator does not explicitly specify `imagePullPolicy`, Kubernetes automatically sets the default based on the container image tag:
- **If image tag is `:latest`** (or omitted entirely): Kubernetes defaults to **`Always`**.
- **If image tag is any explicit tag** (e.g., `:v1.2.0` or `:stable`): Kubernetes defaults to **`IfNotPresent`**.

#### Production Best Practice
> [!TIP]
> **Never use `:latest` in production manifests**.
> Always deploy immutable, unique version tags combined with `imagePullPolicy: IfNotPresent`:
> ```yaml
> image: myregistry.com/billing-service:v2.4.1
> imagePullPolicy: IfNotPresent
> ```
> This ensures that all worker nodes across multiple cloud availability zones run the exact same byte-for-byte binary, makes rollbacks predictable, and shields the cluster from upstream registry downtime.

</details>

---

### Assignment 2: Ephemeral In-Memory & Pod Storage with `emptyDir`

**Question**:
What is an `emptyDir` volume in Kubernetes, what is its lifecycle, how does it differ from persistent storage, and what are its primary enterprise use cases?

<details>
<summary><b>View Answer</b></summary>

#### What is an `emptyDir` Volume?
An `emptyDir` volume is a temporary scratch directory created on the worker node's host filesystem when a Pod is scheduled onto that node.
- It is initially empty upon pod startup.
- All containers residing within the same Pod can read and write to the `emptyDir` simultaneously, even if mounted at different internal container paths.

#### Lifecycle of `emptyDir`
- **Tied directly to the Pod lifecycle**: The data persists across container crashes and restarts *as long as the Pod itself remains on the node*.
- **Permanent Deletion**: If the Pod is terminated, deleted, evicted due to resource exhaustion, or rescheduled to another node, **all data stored in the `emptyDir` is permanently and irrevocably deleted**.

#### RAM-Backed `emptyDir` (Memory Medium)
By default, `emptyDir` volumes are backed by whatever medium is backing the node (such as local SSD or magnetic disk). However, you can configure Kubernetes to back the `emptyDir` with a **tmpfs (RAM-backed in-memory filesystem)**:
```yaml
volumes:
- name: cache-volume
  emptyDir:
    medium: Memory
    sizeLimit: 1Gi
```
This provides ultra-low latency in-memory performance for caching or cryptographic operations, with memory usage counting against the Pod’s overall memory limit.

#### Primary Enterprise Use Cases
1. **Inter-Container Communication (Sidecar Pattern)**: A content generator container downloads files or assets and writes them to `/shared-data`, while an `nginx` web container reads from `/shared-data` and serves client requests.
2. **Scratch Space & Temporary Computations**: Storing intermediate sort buffers, transient log transformations, or video rendering chunks that do not need to persist after job completion.
3. **Checkpoints & Temporary Work Directories**: Caching downloaded dependencies during build jobs.

</details>

---

### Assignment 3: Mounting ConfigMap as an Executable Script Volume

**Question**:
Given the following ConfigMap containing a startup script:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: startup-script
data:
  startup.sh: |
    #!/bin/bash
    echo "Container Initialized"
    sleep infinity
```
Write a complete Pod manifest that mounts this script into `/home`, executes `/home/startup.sh` as the container's primary startup `command`, and ensures executable file permissions (`0755`) are granted so the script runs without permission denial.

<details>
<summary><b>View Answer</b></summary>

#### Analysis of the Permission Issue
When a ConfigMap is mounted as a volume into a container, Kubernetes applies a default UNIX file mode of `0644` (`rw-r--r--`). Under this default permission:
- The script is readable by all users, but **lacks execute (`x`) permission**.
- Attempting to run `/home/startup.sh` directly as the container `command` results in:
  `container create failed: exec: "/home/startup.sh": permission denied`
![][image34]

To resolve this, specify `defaultMode: 0755` (`rwxr-xr-x`) inside the volume definition:
![][image35]

#### Complete Manifest: `manifest.yaml`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: startup-pod
spec:
  containers:
  - name: app
    image: ubuntu:latest
    command:
    - /home/startup.sh
    volumeMounts:
    - name: startup-script-volume
      mountPath: /home
  volumes:
  - name: startup-script-volume
    configMap:
      name: startup-script
      defaultMode: 0755        # Sets read, write, and execute permissions
```

#### Step-by-Step Execution and Verification
1. **Apply the ConfigMap**:
```bash
kubectl apply -f configmap.yaml
```
2. **Apply the Pod Manifest**:
```bash
kubectl apply -f manifest.yaml
```
3. **Verify Pod Execution and Logs**:
```bash
kubectl get pods startup-pod
# NAME          READY   STATUS    RESTARTS   AGE
# startup-pod   1/1     Running   0          12s

kubectl logs startup-pod
# Output: Container Initialized
```
4. **Inspect File Permissions Inside the Container**:
```bash
kubectl exec -it startup-pod -- ls -l /home
```
![][image36]
Output confirms `-rwxr-xr-x 1 root root ... startup.sh`, validating that permissions were successfully set to `0755`.

</details>

---

### Assignment 4: Authenticating Against Private Registries Using `imagePullSecrets`

**Question**:
How do you configure Kubernetes to pull container images from a private Docker Hub or private container registry? Provide the step-by-step secret creation and Pod manifest configuration.

<details>
<summary><b>View Answer</b></summary>

#### Architectural Overview
When pulling container images from private repositories (e.g., Docker Hub private repos, AWS ECR, Quay.io), the container runtime on the worker node requires authentication credentials. Kubernetes provides the `imagePullSecrets` mechanism to securely pass authentication tokens directly to the `kubelet` when pulling images for specific pods.

#### Step 1: Create the Docker Registry Secret via CLI
Use `kubectl create secret docker-registry` to generate a secret of type `kubernetes.io/dockerconfigjson`:
```bash
kubectl create secret docker-registry dockerhub-secret \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=nagarajkamath602 \
  --docker-password='<DOCKER_HUB_ACCESS_TOKEN>' \
  --docker-email=nagaraj@example.com
```

Verify secret creation:
```bash
kubectl get secrets dockerhub-secret
```

#### Step 2: Reference the Secret in the Pod Manifest (`pod.yaml`)
Attach the secret to the pod using the `spec.imagePullSecrets` array:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: private-nginx
spec:
  containers:
  - name: nginx
    image: nagarajkamath602/private:nginx
  imagePullSecrets:
  - name: dockerhub-secret
```

#### Step 3: Deployment and Verification
Apply the manifest and inspect pod status:
```bash
kubectl apply -f pod.yaml
kubectl get pods
```
![][image37]

Inspect pod events to verify authentication and successful image pull:
```bash
kubectl describe pod private-nginx
```
![][image38]

The events log confirms:
```
Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  18s   default-scheduler  Successfully assigned default/private-nginx to worker-node-1
  Normal  Pulling    17s   kubelet            Pulling image "nagarajkamath602/private:nginx"
  Normal  Pulled     14s   kubelet            Successfully pulled image "nagarajkamath602/private:nginx" in 3.12s
  Normal  Created    14s   kubelet            Created container nginx
  Normal  Started    14s   kubelet            Started container nginx
```

</details>

---

### Assignment 5: Granular In-Pod RBAC: ServiceAccount, Role & RoleBinding Verification

**Question**:
Create a dedicated Namespace `demo`, create a ServiceAccount `pod-reader-sa`, and assign it a Role that grants read-only access (`get`, `list`) to Pods within `demo`. Attach this ServiceAccount to a Pod and verify cluster access by executing into the pod and running `kubectl get po`.

<details>
<summary><b>View Answer</b></summary>

#### Architectural Concept
By default, processes running inside a Pod receive the permissions of the `default` ServiceAccount, which has zero access to query cluster resources. To allow in-pod tools (such as monitoring agents, operators, or CI/CD runner pods) to query the Kubernetes API securely:
1. Create a dedicated `ServiceAccount`.
2. Restrict its scope via a `Role` (granting only `get` and `list` on `pods`).
3. Bind the Role using a `RoleBinding`.
4. Inject the identity into the Pod via `spec.serviceAccountName`.

---

#### Step 1: Create the Dedicated Namespace (`namespace.yaml`)
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: demo
```
```bash
kubectl apply -f namespace.yaml
```

---

#### Step 2: Create the ServiceAccount (`serviceaccount.yaml`)
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pod-reader-sa
  namespace: demo
```
```bash
kubectl apply -f serviceaccount.yaml
```

---

#### Step 3: Define the RBAC Role (`role.yaml`)
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader-role
  namespace: demo
rules:
- apiGroups: [""]        # Core API group
  resources: ["pods"]
  verbs: ["get", "list"]
```
```bash
kubectl apply -f role.yaml
```

---

#### Step 4: Bind the Role to the ServiceAccount (`rolebinding.yaml`)
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-reader-binding
  namespace: demo
subjects:
- kind: ServiceAccount
  name: pod-reader-sa
  namespace: demo
roleRef:
  kind: Role
  name: pod-reader-role
  apiGroup: rbac.authorization.k8s.io
```
```bash
kubectl apply -f rolebinding.yaml
```

---

#### Step 5: Launch a Pod with the ServiceAccount Attached (`pod1.yaml`)
Use an image pre-packaged with the `kubectl` CLI tool (e.g., `bitnami/kubectl:latest`):
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kubectl-pod
  namespace: demo
spec:
  serviceAccountName: pod-reader-sa
  containers:
  - name: kubectl
    image: bitnami/kubectl:latest
    command:
    - sleep
    - "3600"
```
```bash
kubectl apply -f pod1.yaml
kubectl get pods -n demo
```
![][image39]

---

#### Step 6: Verify In-Pod Access Control
1. **Exec into the Pod**:
```bash
kubectl exec -it kubectl-pod -n demo -- bash
```
2. **Execute `kubectl get po` from inside the container**:
```bash
kubectl get po -n demo
```
![][image40]

The command succeeds and returns the list of pods inside the `demo` namespace, confirming that the container authenticated using its mounted ServiceAccount token and was successfully authorized by RBAC!

3. **Verify RBAC Constraint Enforcement**:
Inside the container, attempt to list resources outside the permitted scope:
```bash
# Attempting to list secrets in demo namespace:
kubectl get secrets -n demo
# Error from server (Forbidden): secrets is forbidden: User "system:serviceaccount:demo:pod-reader-sa" cannot list resource "secrets" in API group "" in the namespace "demo"

# Attempting to list pods in default namespace:
kubectl get po -n default
# Error from server (Forbidden): pods is forbidden: User "system:serviceaccount:demo:pod-reader-sa" cannot list resource "pods" in API group "" in the namespace "default"
```
This confirms that the pod's permissions are strictly locked down to read-only pod access within the `demo` namespace.

</details>

---

---

[image1]: ./images/image1.png
[image2]: ./images/image2.png
[image3]: ./images/image3.png
[image4]: ./images/image4.png
[image5]: ./images/image5.png
[image6]: ./images/image6.png
[image7]: ./images/image7.png
[image8]: ./images/image8.png
[image9]: ./images/image9.png
[image10]: ./images/image10.png
[image11]: ./images/image11.png
[image12]: ./images/image12.png
[image13]: ./images/image13.png
[image14]: ./images/image14.png
[image15]: ./images/image15.png
[image16]: ./images/image16.png
[image17]: ./images/image17.png
[image18]: ./images/image18.png
[image19]: ./images/image19.png
[image20]: ./images/image20.png
[image21]: ./images/image21.png
[image22]: ./images/image22.png
[image23]: ./images/image23.png
[image24]: ./images/image24.png
[image25]: ./images/image25.png
[image26]: ./images/image26.png
[image27]: ./images/image27.png
[image28]: ./images/image28.png
[image29]: ./images/image29.png
[image30]: ./images/image30.png
[image31]: ./images/image31.png
[image32]: ./images/image32.png
[image33]: ./images/image33.png
[image34]: ./images/image34.png
[image35]: ./images/image35.png
[image36]: ./images/image36.png
[image37]: ./images/image37.png
[image38]: ./images/image38.png
[image39]: ./images/image39.png
[image40]: ./images/image40.png
