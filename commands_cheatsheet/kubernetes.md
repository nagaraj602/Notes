# Kubernetes (kubectl) Commands Cheat Sheet

> Comprehensive Kubernetes cluster administration, pod diagnostics, rollouts, scaling, networking, storage, RBAC, and Helm commands based on engineering modules.

## 1. Cluster Bootstrap & Node Administration

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `sudo swapoff -a && sudo sed -i '/swap/d' /etc/fstab` | Immediately disables Linux swap memory and comments it out in `/etc/fstab`. Kubernetes kubelet requires swap to be disabled to guarantee memory QoS and OOM precision. | `swapoff -a` (current), `sed` (reboot persistent) | Node Setup, Prerequisites |
| `kubeadm init --pod-network-cidr=192.168.0.0/16` | Initializes the Kubernetes control plane master node with the Calico-compatible Pod network CIDR range. Generates PKI certificates and kubeconfig. | `--pod-network-cidr` (overlay network block) | Bootstrap, Control Plane |
| `kubeadm token create --print-join-command` | Generates a new short-lived bootstrap token and outputs the complete `kubeadm join` command with SHA256 discovery hash for joining new worker nodes. | `--print-join-command` (full syntax output) | Bootstrap, Worker Join |
| `kubectl get nodes -o wide` | Lists all cluster nodes with status (Ready/NotReady), roles, age, Kubernetes version, internal IP, external IP, OS image, kernel version, and container runtime. | `-o wide` (extended metadata) | Nodes, Health |
| `kubectl cordon <node_name>` | Marks a node as unschedulable. The kube-scheduler will cease scheduling any new pods onto this node while existing running pods continue uninterrupted. | None | Maintenance, Scheduling |
| `kubectl drain <node_name> --ignore-daemonsets --delete-emptydir-data` | Safely evicts all workloads from a node in preparation for kernel patching, reboot, or termination. Bypasses DaemonSets and removes local emptyDir storage. | `--ignore-daemonsets`, `--delete-emptydir-data` | Maintenance, Node Eviction |
| `kubectl uncordon <node_name>` | Marks a drained/cordoned node schedulable again, allowing the kube-scheduler to assign new pods to it. | None | Maintenance, Recovery |
| `kubectl label nodes <node_name> disktype=ssd env=prod` | Attaches key-value metadata labels to a worker node for targeting workloads via `nodeSelector` or `nodeAffinity` specifications. | `key=value` pairs | Nodes, Labeling |

## 2. Pod Lifecycle & Troubleshooting

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `kubectl get pods -A -o wide` | Queries all pods across all cluster namespaces (`-A`), displaying their running status, restart counts, age, pod IP, and assigned worker node host. | `-A` (all namespaces), `-o wide` | Pods, Health |
| `kubectl get pods -A --field-selector status.phase!=Running,status.phase!=Succeeded` | Filters for all pods that are NOT in a healthy Running or completed Succeeded state (e.g. CrashLoopBackOff, Pending, Evicted, Error). | `--field-selector` (server-side filter) | Troubleshooting, Outage |
| `kubectl describe pod <pod_name> -n <namespace>` | Prints detailed resource metadata, lifecycle conditions, container exit codes, volume mounts, and chronological Kubernetes events. First diagnostic command. | `-n <namespace>` | Diagnostics, Events |
| `kubectl logs -f <pod_name> -n <namespace>` | Follows (-f) the live standard output and standard error stream of the primary container running inside a pod. | `-f` (follow live output) | Logs, Streaming |
| `kubectl logs -f <pod_name> -c <container_name> --previous -n <namespace>` | Retrieves logs from the PREVIOUS crashed instance of a specific container in a pod, crucial for diagnosing root causes of CrashLoopBackOff. | `-c <container>`, `--previous` (crashed container) | Logs, CrashLoopBackOff |
| `kubectl exec -it <pod_name> -n <namespace> -- /bin/sh` | Opens an interactive terminal session inside the container for live environment variable inspection and in-cluster network connectivity testing. | `-it` (interactive tty), `-- /bin/sh` | Debugging, Shell |
| `kubectl top pods -n <namespace> --sort-by=memory` | Queries the metrics-server API to report live CPU (cores) and memory (MiB) utilization for all pods in a namespace, highlighting OOMKilled risk candidates. | `--sort-by=memory` (descending) | Metrics, Memory OOM |
| `kubectl delete pod <pod_name> -n <namespace> --grace-period=0 --force` | Forcefully deletes a stuck or terminating pod immediately, bypassing standard graceful termination signals. | `--grace-period=0`, `--force` | Emergency, Cleanup |

## 3. Deployments, Scaling & Zero-Downtime Rollouts

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `kubectl create deployment web-app --image=nginx:1.25-alpine --replicas=3 -n prod` | Imperatively creates a Deployment resource managing a ReplicaSet of 3 pod replicas running Nginx in the `prod` namespace. | `--image`, `--replicas=3`, `-n` | Deployment, Imperative |
| `kubectl set image deployment/web-app web-app=nginx:1.26-alpine -n prod --record` | Triggers a zero-downtime rolling update by updating the container image tag. `--record` documents the command in rollout history. | `deployment/<name> <container>=<image>` | Rolling Update, CI/CD |
| `kubectl rollout status deployment/web-app -n prod` | Watches deployment rolling update progress in the terminal, blocking until all new replica pods pass readiness probes or until timeout triggers. | None | CI/CD, Verification |
| `kubectl rollout history deployment/web-app -n prod` | Lists all historical revisions of a deployment with recorded change-causes, showing revision numbers available for rollback. | None | Rollout, History |
| `kubectl rollout undo deployment/web-app --to-revision=2 -n prod` | Instantly rolls back a deployment to revision 2, terminating problematic replica pods and restoring previous stable workloads without downtime. | `--to-revision=<number>` | Rollback, Recovery |
| `kubectl rollout restart deployment/web-app -n prod` | Performs a rolling restart of all pods in a deployment one by one without modifying deployment configuration. Useful for reloading ConfigMaps. | None | Zero-Downtime Restart |
| `kubectl scale deployment web-app --replicas=10 -n prod` | Manually scales the replica count of a deployment to 10 pods to absorb anticipated traffic spikes or load testing. | `--replicas=<count>` | Scaling, Capacity |
| `kubectl autoscale deployment web-app --min=3 --max=15 --cpu-percent=80 -n prod` | Creates a HorizontalPodAutoscaler (HPA) targeting average CPU utilization of 80% to scale pods automatically between 3 and 15 replicas. | `--min`, `--max`, `--cpu-percent` | Autoscaling, HPA |

## 4. Services, Networking & Ingress

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `kubectl expose deployment web-app --port=80 --target-port=80 --type=ClusterIP -n prod` | Creates a internal virtual ClusterIP Service providing stable DNS and load balancing across all pods matching the deployment label selector. | `--port` (svc), `--target-port` (pod), `--type=ClusterIP` | Services, Internal |
| `kubectl expose deployment web-app --port=80 --target-port=80 --type=NodePort -n prod` | Exposes the service externally across each cluster node's IP on a static high port in the range 30000-32767. | `--type=NodePort` | Services, External |
| `kubectl get svc -A` | Lists all Services across all namespaces showing Type, Cluster-IP, External-IP, Ports, and Age. | `-A` (all namespaces) | Services, Inventory |
| `kubectl port-forward svc/web-app 8080:80 -n prod` | Creates a secure localhost tunnel from workstation port 8080 directly to cluster service port 80, bypassing Ingress and firewalls for testing. | `local_port:service_port` | Debugging, Local Access |
| `kubectl get endpoints <service_name> -n prod` | Displays the live pod IPs and ports currently registered as healthy backends for a Service. If empty, check pod readiness probes and selectors. | Replaces endpoint slices lookup | Networking, Endpoints |
| `kubectl get ingress -A` | Lists all Ingress resources across all namespaces, displaying their assigned load balancer hostnames/IPs, rules, and TLS settings. | `-A` (all namespaces) | Ingress, Routing |
| `kubectl describe ingress <ingress_name> -n prod` | Details host routing rules, TLS certificate secrets, path rewrites, and backend service targets configured on an Ingress resource. | None | Ingress, Diagnostics |

## 5. Configuration Management: ConfigMaps & Secrets

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `kubectl create configmap app-config --from-file=application.properties -n prod` | Creates a ConfigMap storing the entire content of an application configuration file, ready to be mounted as a file or injected as environment variables. | `--from-file=<path>` | ConfigMaps, Files |
| `kubectl create configmap env-config --from-literal=APP_ENV=prod --from-literal=LOG_LEVEL=info -n prod` | Creates a ConfigMap from key-value literal string pairs directly from the command line without creating intermediate files. | `--from-literal=KEY=VALUE` | ConfigMaps, Literals |
| `kubectl create secret generic db-creds --from-literal=username=dbadmin --from-literal=password=SecretPass! -n prod` | Creates an Opaque Kubernetes Secret resource with base64-encoded key-value pairs stored encrypted in etcd. | `create secret generic`, `--from-literal` | Secrets, Security |
| `kubectl get secret db-creds -n prod -o jsonpath="{.data.password}" \| base64 -d` | Extracts and decodes base64-encoded secret data directly from Kubernetes Secret resource into plain text in the terminal. | `-o jsonpath`, `base64 -d` | Secrets, Decoding |
| `kubectl get configmap,secret -n prod` | Lists all ConfigMaps and Secrets defined in the specified namespace. | Multiple resource query | Configuration, Inventory |

## 6. Persistent Storage: PV, PVC & StorageClasses

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `kubectl get storageclass` | Lists dynamic storage provisioners (e.g. AWS EBS CSI `gp3`, local-path, Ceph) and reclaim policies configured across the cluster. | Short alias: `sc` | Storage, Provisioning |
| `kubectl get pv` | Lists cluster-wide PersistentVolumes showing storage capacity, access modes (`RWO`, `ROX`, `RWX`), reclaim policy (`Retain`/`Delete`), and claim binding. | None | Storage, Volumes |
| `kubectl get pvc -n prod` | Lists PersistentVolumeClaims in the namespace showing Bound/Pending status, matching PV volume name, and requested capacity. | None | Storage, Claims |
| `kubectl describe pvc <pvc_name> -n prod` | Displays detailed status of a PVC. If stuck in `Pending`, reveals whether the dynamic CSI driver failed to provision volume or quota was exceeded. | None | Storage, Troubleshooting |

## 7. Security, ServiceAccounts & RBAC

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `kubectl auth can-i create deployments --as system:serviceaccount:prod:deploy-bot -n prod` | Tests RBAC authorization permissions of a specific ServiceAccount without having to assume its token. Returns `yes` or `no`. | `--as <user/serviceaccount>`, `-n` | RBAC, Authorization |
| `kubectl auth can-i '*' '*' -n kube-system` | Checks if the current authenticated user has full cluster-admin wildcard permissions inside the critical `kube-system` namespace. | `can-i '<verb>' '<resource>'` | Security, Audit |
| `kubectl create serviceaccount deploy-bot -n prod` | Creates a Kubernetes ServiceAccount used by automated CI/CD pipelines (Jenkins, GitHub Actions, GitLab) to authenticate with the API server. | `serviceaccount` (alias: `sa`) | Security, Identity |
| `kubectl get role,rolebinding -n prod` | Lists namespace-scoped RBAC Roles (permission sets) and RoleBindings (associations between users/ServiceAccounts and Roles). | None | RBAC, Audit |
| `kubectl get clusterrole,clusterrolebinding \| grep admin` | Queries cluster-wide administrative RBAC bindings granting permissions across all namespaces. | None | RBAC, Cluster Scope |

## 8. Cluster Health, Events & Resource Quotas

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `kubectl get events -A --sort-by='.metadata.creationTimestamp'` | Displays all cluster-wide events (container crashes, image pull failures, OOM kills, node reboots) sorted chronologically. Essential during outages. | `--sort-by='.metadata.creationTimestamp'` | Events, Root Cause Analysis |
| `kubectl top nodes` | Queries metrics-server for live CPU and memory utilization percentages and raw core/memory counts across all worker and control plane nodes. | None | Metrics, Node Capacity |
| `kubectl get resourcequotas -A` | Displays hard limits and current usage for compute resources (CPU, RAM) and object counts across namespaces. | Short alias: `quota` | Quotas, Multi-Tenancy |
| `kubectl diff -f deployment.yaml` | Performs a server-side dry-run comparison between local YAML manifests and live cluster state, highlighting changes in colored diff format. | Safe Apply, IaC | IaC, Safe Apply |
| `kubectl apply -f ./manifests/` | Declaratively applies all YAML configuration files inside a directory to achieve desired cluster state. | `-f <directory>` | GitOps, IaC |

## 9. Helm Package Management Operations

| Command | Description & AI Explanation | Key Flags / Syntax | Tags |
| :--- | :--- | :--- | :--- |
| `helm repo add bitnami https://charts.bitnami.com/bitnami && helm repo update` | Adds an external Helm chart repository and downloads the latest index metadata of all published application charts. | `repo add`, `repo update` | Helm, Repositories |
| `helm search repo bitnami/nginx` | Searches local repository indexes for matching chart names, available chart versions, and upstream application versions. | `search repo <term>` | Helm, Search |
| `helm install my-app bitnami/nginx -f values-prod.yaml -n prod --create-namespace` | Deploys a new Helm release named `my-app` into namespace `prod`, overriding default parameters with custom values from `values-prod.yaml`. | `-f <values_file>`, `-n`, `--create-namespace` | Helm, Deployment |
| `helm upgrade --install my-app bitnami/nginx -f values.yaml -n prod` | Idempotently upgrades an existing Helm release if present, or installs it fresh if it doesn't exist yet. The standard command for CI/CD pipelines. | `--install` (idempotent flag) | Helm, CI/CD |
| `helm list -A` | Lists all deployed Helm releases across all namespaces with release name, namespace, revision, status, chart version, and app version. | `-A` (all namespaces) | Helm, Releases |
| `helm history my-app -n prod` | Displays complete revision history of a Helm release, showing dates, status (superseded/deployed), and descriptions for auditing. | `history <release_name>` | Helm, Auditing |
| `helm rollback my-app 2 -n prod` | Instantly rolls back a Helm release to revision 2, recreating previous manifests and configurations atomically. | `rollback <release> <revision>` | Helm, Rollback |
| `helm uninstall my-app -n prod` | Removes all Kubernetes resources (Deployments, Services, ConfigMaps, Secrets) associated with the specified Helm release. | `uninstall <release>` | Helm, Cleanup |
