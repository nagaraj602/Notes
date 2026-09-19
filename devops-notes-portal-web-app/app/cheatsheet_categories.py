"""
DevOps Commands & Examples Cheat Sheet - Category Definitions and Metadata
"""

from typing import Dict, Any, List, Optional

CHEATSHEET_CATEGORIES: List[Dict[str, Any]] = [
    {
        "id": "linux",
        "name": "Linux",
        "filename": "linux.md",
        "type": "commands",
        "icon": "fa-brands fa-linux",
        "color": "amber",
        "description": "Essential Linux administration, troubleshooting, networking, and system diagnostics commands."
    },
    {
        "id": "shell_script",
        "name": "Shell Script",
        "filename": "shell_script.md",
        "type": "commands",
        "icon": "fa-solid fa-terminal",
        "color": "emerald",
        "description": "Bash & Shell scripting commands, syntax, expansions, loops, and conditions."
    },
    {
        "id": "github",
        "name": "Github",
        "filename": "github.md",
        "type": "commands",
        "icon": "fa-brands fa-github",
        "color": "slate",
        "description": "Git & GitHub CLI operations, branch management, rebasing, tags, and conflict resolution."
    },
    {
        "id": "build_tools",
        "name": "Build Tools (Maven, Python, C, NodeJS)",
        "filename": "build_tools.md",
        "type": "commands",
        "icon": "fa-solid fa-gears",
        "color": "rose",
        "description": "Build tools, dependencies, and packaging CLI commands across Maven, Python, C, and Node.js."
    },
    {
        "id": "aws",
        "name": "AWS",
        "filename": "aws.md",
        "type": "commands",
        "icon": "fa-brands fa-aws",
        "color": "amber",
        "description": "AWS CLI v2 commands for EC2, S3, IAM, VPC, EKS, CloudWatch, and RDS management."
    },
    {
        "id": "docker",
        "name": "Docker",
        "filename": "docker.md",
        "type": "commands",
        "icon": "fa-brands fa-docker",
        "color": "sky",
        "description": "Docker container lifecycle, image optimization, buildx, networks, and compose commands."
    },
    {
        "id": "kubernetes",
        "name": "Kubernetes",
        "filename": "kubernetes.md",
        "type": "commands",
        "icon": "fa-solid fa-dharmachakra",
        "color": "indigo",
        "description": "Kubectl cluster operations, debugging, rollouts, logs, pod health, and resource configurations."
    },
    {
        "id": "helm",
        "name": "Helm",
        "filename": "helm.md",
        "type": "commands",
        "icon": "fa-solid fa-anchor",
        "color": "blue",
        "description": "Helm chart package manager commands, repositories, value overrides, releases, and rollbacks."
    },
    {
        "id": "terraform",
        "name": "Terraform",
        "filename": "terraform.md",
        "type": "commands",
        "icon": "fa-solid fa-cubes-stacked",
        "color": "violet",
        "description": "Terraform IaC CLI commands, state operations, workspaces, module imports, and plan execution."
    },
    {
        "id": "ansible",
        "name": "Ansible",
        "filename": "ansible.md",
        "type": "commands",
        "icon": "fa-solid fa-network-wired",
        "color": "red",
        "description": "Ansible ad-hoc commands, playbook executions, vault encryption, and inventory checks."
    },
    {
        "id": "monitoring",
        "name": "Monitoring Tools",
        "filename": "monitoring.md",
        "type": "commands",
        "icon": "fa-solid fa-chart-line",
        "color": "teal",
        "description": "PromQL queries, Grafana dashboards, Datadog CLI, cAdvisor, and alert management commands."
    },
    {
        "id": "shell_examples",
        "name": "Shell Script Examples",
        "filename": "shell_examples.md",
        "type": "examples",
        "icon": "fa-solid fa-code",
        "color": "emerald",
        "description": "Production-ready automation shell scripts for backup, log rotation, and server maintenance."
    },
    {
        "id": "k8s_manifests",
        "name": "Kubernetes Manifest Files",
        "filename": "k8s_manifests.md",
        "type": "examples",
        "icon": "fa-solid fa-file-code",
        "color": "indigo",
        "description": "Production Kubernetes YAML manifests including Deployments, Ingress, StatefulSets, and Probes."
    },
    {
        "id": "terraform_examples",
        "name": "Terraform YAML / HCL Examples",
        "filename": "terraform_examples.md",
        "type": "examples",
        "icon": "fa-solid fa-layer-group",
        "color": "violet",
        "description": "Complete Terraform module architectures, remote state lock setups, and cloud-init integrations."
    },
    {
        "id": "ansible_examples",
        "name": "Ansible Example Files",
        "filename": "ansible_examples.md",
        "type": "examples",
        "icon": "fa-solid fa-boxes-packing",
        "color": "rose",
        "description": "Complete Ansible playbooks for multi-tier configurations, server hardening, and rolling restarts."
    },
    {
        "id": "dockerfile_examples",
        "name": "Dockerfile Example Files",
        "filename": "dockerfile_examples.md",
        "type": "examples",
        "icon": "fa-brands fa-docker",
        "color": "sky",
        "description": "Optimized multi-stage and distroless Dockerfiles for Node, Java, Python, and Go applications."
    }
]


def get_category_meta(category_id: str) -> Optional[Dict[str, Any]]:
    """Finds category metadata by id or filename."""
    if not category_id:
        return None
    target = category_id.lower().strip()
    for cat in CHEATSHEET_CATEGORIES:
        if cat["id"].lower() == target or cat["filename"].lower() == target:
            return cat
    return None
