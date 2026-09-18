# Kubernetes (kubectl) Commands Cheat Sheet

> Essential Kubernetes cluster administration, pod diagnostics, rollouts, scaling, networking, and security commands.

| Command | Description & AI Explanation | Category / Tags |
| :--- | :--- | :--- |
| `kubectl get pods -A -o wide --field-selector status.phase!=Running` | Queries all cluster namespaces for pods that are NOT in Running state (e.g. CrashLoopBackOff, Pending, Evicted), listing host node assignments. | Troubleshooting, Health |
| `kubectl describe pod <pod-name> -n <namespace>` | Prints detailed resource metadata, lifecycle conditions, and chronological Kubernetes events (pull errors, OOMKills, probe failures). First debugging step. | Diagnostics, Events |
| `kubectl logs -f <pod-name> -c <container-name> --previous` | Retrieves logs from the PREVIOUS crashed instance of a container inside a pod, essential for diagnosing CrashLoopBackOff causes. | Logs, Troubleshooting |
| `kubectl exec -it <pod-name> -n <namespace> -- /bin/sh` | Opens an interactive terminal session inside the container for live environment variable and network connectivity testing. | Debugging, Shell |
| `kubectl port-forward svc/<service-name> 8080:80 -n <namespace>` | Forwards local workstation port 8080 directly to cluster service port 80, bypassing Ingress and load balancers for private service testing. | Networking, Debugging |
| `kubectl rollout status deployment/<dep-name> -n <namespace>` | Watches deployment rolling update progress, blocking until all new replica pods pass readiness probes or until timeout triggers. | Deployment, CI/CD |
| `kubectl rollout undo deployment/<dep-name> -n <namespace>` | Instantly rolls back a deployment to its previous stable revision, terminating problematic replica pods and restoring healthy workloads. | Rollback, Recovery |
| `kubectl scale deployment <dep-name> --replicas=5 -n <namespace>` | Manually scales the replica count of a deployment to 5 pods for traffic spikes or load testing. | Scaling, Capacity |
| `kubectl top nodes && kubectl top pods -n <namespace> --sort-by=memory` | Queries metrics-server for live CPU and memory utilization across nodes and pods, highlighting potential OOM candidates. | Metrics, Performance |
| `kubectl get events -n <namespace> --sort-by='.metadata.creationTimestamp'` | Displays cluster events sorted chronologically to pinpoint recent scheduling bottlenecks, node pressure, or container crashes. | Events, Diagnostics |
| `kubectl cordon <node-name> && kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data` | Marks node unschedulable (cordon) and safely evicts all workloads (drain) for zero-downtime node kernel updates or AMI rotation. | Node Maintenance |
| `kubectl uncordon <node-name>` | Marks a drained node schedulable again, allowing the kube-scheduler to assign new pods to it. | Node Maintenance |
| `kubectl auth can-i create deployments --as system:serviceaccount:prod:app-sa -n prod` | Tests RBAC permissions of a specific ServiceAccount without having to assume its token. | RBAC, Security |
| `kubectl get secret <secret-name> -n <namespace> -o jsonpath="{.data.password}" \| base64 -d` | Extracts and decodes base64 encoded secret data directly from Kubernetes Secret resource into plain text. | Secrets, Configuration |
| `kubectl diff -f deployment.yaml` | Performs a server-side dry-run comparison between local YAML manifests and live cluster state, highlighting changes in colored diff format. | Safe Apply, IaC |
