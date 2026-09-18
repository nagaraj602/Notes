# Helm Commands Cheat Sheet

> Essential Helm 3 package management commands for chart deployment, values customization, releases, and rollback operations.

| Command | Description & AI Explanation | Category / Tags |
| :--- | :--- | :--- |
| `helm repo add bitnami https://charts.bitnami.com/bitnami && helm repo update` | Registers an upstream Helm chart repository locally and fetches the latest index.yaml containing chart versions and metadata. | Repositories, Setup |
| `helm search repo nginx` | Searches all configured local repositories for available charts matching keyword 'nginx', displaying latest chart and app versions. | Search, Discovery |
| `helm install my-release bitnami/nginx -f values-prod.yaml --namespace prod --create-namespace` | Installs chart as 'my-release' using custom production values override file, creating target namespace if it does not exist. | Deployment, Releases |
| `helm upgrade --install my-release ./my-chart -f values.yaml --set replicaCount=3 -n prod` | Idempotent deployment command: upgrades release if it already exists, or installs it if not found. Ideal for CI/CD pipeline automation. | CI/CD, Idempotent |
| `helm diff upgrade my-release ./my-chart -f values.yaml` | (Helm-diff plugin) Generates a colored diff showing exactly what Kubernetes resources and values will change before applying upgrade. | Safe Upgrades, Diff |
| `helm history my-release -n prod` | Displays complete revision history of a release, showing revision numbers, timestamps, status, chart version, and user descriptions. | History, Audit |
| `helm rollback my-release 2 -n prod` | Rolls back release to revision 2, automatically applying previous values and manifests to recover from failed deployments. | Rollback, Recovery |
| `helm template my-release ./my-chart -f values.yaml > rendered-manifests.yaml` | Evaluates Helm Go-templates with supplied values and renders raw Kubernetes manifests to stdout without contacting the cluster. | Dry-run, CI/CD Lint |
| `helm lint ./my-chart` | Verifies Helm chart syntax, checking Chart.yaml formatting, template Go-syntax, and mandatory value requirements. | Linting, Quality Gate |
| `helm package ./my-chart -d ./dist/` | Packages directory into a versioned tarball (e.g. my-chart-1.2.0.tgz) ready for publishing to ChartMuseum or OCI registries. | Packaging, Artifacts |
| `helm get values my-release -n prod -a` | Retrieves all user-supplied and default values applied to the live running release inside the cluster. | Inspection, Values |
| `helm uninstall my-release -n prod --keep-history` | Uninstalls all Kubernetes resources associated with release while retaining release history for potential future rollbacks. | Uninstall, Clean-up |
