# 📚 DevOps Master Notes & Knowledge Hub

Welcome to the comprehensive DevOps & Cloud Engineering repository maintained by **Nagaraj Kamath**. This repository serves as a centralized knowledge base for real-world DevOps workflows, cloud architecture, automation scripts, and technical interview preparation.

---

## 🗂️ Repository Contents

| Directory / File | Description |
| :--- | :--- |
| [**`devops-notes-portal-web-app/`**](./devops-notes-portal-web-app/) | Full-stack FastAPI & Dockerized web application with live Git sync, search, and interview trackers |
| [**`AWS notes.md`**](./AWS%20notes.md) | Comprehensive AWS architecture, services, troubleshooting, and production notes |
| [**`Terraform/`**](./Terraform/) | Infrastructure as Code (IaC) modules, configurations, and best practices |
| [**`Interview Questions/`**](./Interview%20Questions/) | Curated technical question banks collected from real-world senior DevOps interview rounds |
| [**`Nagaraj_interviews/`**](./Nagaraj_interviews/) | Structured interview schedules, round logs, company notes, and Q&A history |
| [**`Jenkins-Assignment/`**](./Jenkins-Assignment/) | CI/CD pipelines, Declarative Jenkinsfiles, and automated testing setups |

---

## 🚀 Quickstart: DevOps Hub Web Application

The interactive web portal located in [`devops-notes-portal-web-app/`](./devops-notes-portal-web-app/) lets you explore notes with in-page search, view interactive Mermaid architecture flowcharts, and manage interview schedules.

### Universal 1-Click Deployment (`deploy.sh`)
Compatible with **Windows (Git Bash)**, **Ubuntu / Debian Linux (GCP VM)**, and **macOS**:

```bash
cd devops-notes-portal-web-app
chmod +x deploy.sh
./deploy.sh
```

Choose your deployment target from the interactive menu:
1. **Docker Compose** (Maps ports `80` and `8000` with auto-restart)
2. **Cloudflare Tunnel** (Access securely over HTTPS on GCP with **zero open firewall ports**)
3. **Docker Desktop Kubernetes** (Local cluster on Windows/macOS)
4. **Kubeadm Cluster** (Multi-node production Kubernetes with NodePort 30080)
5. **GCP Ubuntu Full Setup** (Automated Docker install + App launch + Cloudflare Tunnel)
6. **Docker Hub Image Build & Push** (With automatic account switch detection & login)
7. **GCP VM Auto-Schedule** (Auto shutdown at 11:00 PM IST & auto startup at 6:00 AM IST)

For in-depth deployment documentation, refer to the [DevOps Notes Portal README](./devops-notes-portal-web-app/README.md).
