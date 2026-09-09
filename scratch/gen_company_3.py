# -*- coding: utf-8 -*-
"""Generator for Feuji interview round (Level 1)."""

def get_feuji_markdown():
    return """<details open>
<summary><h2>🏢 Feuji</h2></summary>

<details open>
<summary><h3>Level 1</h3></summary>

#### 【 CI/CD 】

<details>
<summary><strong>● Can you explain the CI/CD setup you have worked with?</strong></summary>

**Answer:**
In my recent role, I designed an automated, enterprise **GitOps CI/CD pipeline** running across **GitHub Actions**, **AWS ECR**, and **Argo CD** deploying to an **AWS EKS** multi-tenant cluster:

1. **Continuous Integration (CI):**
   - Developer opens a Pull Request -> Triggers GitHub Actions workflow.
   - **Static Analysis & Testing:** Runs linting, unit tests, and **SonarQube** Quality Gate verification.
   - **Security Auditing:** Scans dependencies with Trivy and Snyk for critical CVEs.
   - **Containerization:** On merge to `main`, executes a multi-stage Docker build, tags the image with the Git commit SHA (`${IMAGE_TAG}`), scans the container image with Trivy, and pushes it to **AWS ECR**.

2. **Continuous Delivery (CD) via GitOps:**
   - A dedicated GitHub Actions step updates the Kubernetes Helm chart values repository (`image.tag: <commit-sha>`).
   - **Argo CD** continuously monitors the Helm Git repository. Upon detecting commit drift, Argo CD triggers an automated sync, executing a rolling deployment to the EKS cluster.
   - Automatic canary analysis via **Argo Rollouts** validates error rates and latency before shifting 100% of user traffic.
</details>

#### 【 KUBERNETES 】

<details>
<summary><strong>● Have you deployed any monitoring systems and worked with microservices running in an EKS cluster?</strong></summary>

**Answer:**
Yes, I have extensive hands-on experience architecting and operating production microservices on **AWS EKS** combined with full-stack observability:

- **EKS Architecture:** Designed multi-AZ EKS clusters leveraging **Karpenter** and Cluster Autoscaler for node provisioning, AWS Load Balancer Controller for Application Load Balancers, and AWS VPC CNI for native pod networking.
- **Monitoring Deployments:** Deployed and managed the **Prometheus Operator (kube-prometheus-stack)** with Alertmanager, Grafana, and an **OpenSearch / Fluent Bit** centralized logging pipeline running as DaemonSets across all worker nodes.
- **Observability Integration:** Instrumented containerized Java, Go, and Python microservices with OpenTelemetry (OTel) agents exporting metrics and distributed traces into Grafana and Jaeger.
</details>

<details>
<summary><strong>↳ Follow-up: As part of this CI/CD setup, did you deploy applications to an EKS cluster?</strong></summary>

**Answer:**
Yes, deployments to the EKS cluster were completely automated through **GitOps with Argo CD**:

1. **Deployment Artifacts:** Applications were packaged as standard **Helm charts** parameterized for different environments (`values-dev.yaml`, `values-stage.yaml`, `values-prod.yaml`).
2. **GitOps Synchronization:** Argo CD Application controllers tracked the environment manifests in Git. When the CI pipeline committed an updated image tag, Argo CD reconciled the desired state against the EKS cluster.
3. **Traffic Management:** Handled via **AWS Load Balancer Controller**, dynamically provisioning Target Groups and Application Load Balancers (ALBs) mapped to Kubernetes Ingress resources using IP-mode routing directly to Pod IPs.
</details>

<details>
<summary><strong>↳ Follow-up: If, after a deployment, a user is unable to access the application, how would you troubleshoot the issue?</strong></summary>

**Answer:**
I follow a methodical top-down diagnostic workflow spanning **DNS/Ingress -> Service/Endpoints -> Pods/Containers**:

```
[ 1. Ingress & DNS ]
  |-- dig api.company.com (Verify Route 53 points to ALB DNS)
  |-- kubectl get ingress -n <namespace> (Inspect Ingress status & ALB annotations)
  +-- Check AWS ALB Target Group: Are target pods showing 'healthy' or 'unhealthy'?

[ 2. Service & Endpoints (Core Binding Check) ]
  |-- kubectl get svc <service-name> -n <namespace>
  +-- kubectl get endpoints <service-name> -n <namespace>
        |-- If endpoints list is EMPTY:
        |   The Service 'selector' does NOT match Pod 'labels'!
        +-- If endpoints exist: Proceed to Pod inspection

[ 3. Pod Health & Status ]
  |-- kubectl get pods -n <namespace> -l app=<app-name>
  |     |-- Check Pod Phase: Running, CrashLoopBackOff, Pending, ImagePullBackOff?
  +-- kubectl describe pod <pod-name> -n <namespace>
        |-- Check 'Conditions': Initialized, Ready, ContainersReady, PodScheduled
        +-- If Pod is Running but NOT Ready (0/1):
            The 'readinessProbe' is failing, preventing ingress traffic!

[ 4. Logs & Container Diagnostics ]
  |-- kubectl logs <pod-name> -n <namespace> --tail=100
  |-- kubectl logs <pod-name> -n <namespace> --previous (If restarted)
  +-- Port-forward directly to pod:
      kubectl port-forward pod/<pod-name> 8080:8080 -n <namespace>
      curl -Iv http://localhost:8080/health
```
</details>

#### 【 MONITORING 】

<details>
<summary><strong>↳ Follow-up: How did you configure monitoring systems such as the ELK stack and Grafana for your microservices?</strong></summary>

**Answer:**
I implemented an integrated observability architecture combining **Fluent Bit + OpenSearch (ELK)** for logs and **Prometheus + Grafana** for metrics:

1. **Centralized Logging (ELK / OpenSearch):**
   - **Log Collection:** Deployed **Fluent Bit** as a `DaemonSet` on every EKS node. It tails container stdout/stderr logs from `/var/log/containers/*.log`.
   - **Metadata Enrichment:** The Fluent Bit `kubernetes` filter queries the Kubelet API to attach namespace, pod name, container name, and label metadata to every log entry.
   - **Ingestion & Visualization:** Forwarded structured JSON logs into an **Amazon OpenSearch Service** cluster. Developers query and filter logs using **OpenSearch Dashboards / Kibana** with saved index patterns (`app-logs-*`).

2. **Metrics & Visualization (Prometheus & Grafana):**
   - Deployed **kube-prometheus-stack** via Helm.
   - Microservices expose application telemetry at `/metrics` using Prometheus client libraries.
   - Defined `ServiceMonitor` Custom Resources matching service labels to configure Prometheus scrapers declaratively.
   - Configured **Grafana** with Prometheus as the default timeseries datasource and Alertmanager for threshold notifications.
</details>

<details>
<summary><strong>↳ Follow-up: What kind of dashboards did you create in Grafana?</strong></summary>

**Answer:**
I engineered role-specific Grafana dashboards organized across three operational levels:

1. **Kubernetes Infrastructure Dashboard:**
   - Cluster-wide CPU and Memory capacity vs. requests/limits.
   - Node status, disk pressure, and network throughput.
   - Pod restart counts, deployment replica health, and PVC storage utilization.

2. **Microservice Application Dashboard (RED Method):**
   - **Rate:** Requests per second (RPS) broken down by HTTP endpoint and response code (`2xx`, `4xx`, `5xx`).
   - **Errors:** Error rate percentage (`(5xx / Total Requests) * 100`).
   - **Duration:** Request latency distribution visualized at **p50, p95, and p99** percentiles.

3. **Runtime & Middleware Dashboards:**
   - **JVM Telemetry:** Heap memory utilization, Garbage Collection (GC) pause duration and frequency, active thread count.
   - **Database Connection Pool:** HikariCP active connections, idle connections, and connection acquisition wait times.

4. **Business & Transactional Dashboards:**
   - Completed payments per minute, payment processing failure categories, and third-party gateway response times.
</details>

<details>
<summary><strong>● What is SLI (Service Level Indicator) and SLO (Service Level Objective)?</strong></summary>

**Answer:**
In modern Site Reliability Engineering (SRE):

1. **SLI (Service Level Indicator):**
   - A **quantifiable, real-time metric** that measures how well a service is performing at any given moment.
   - Usually expressed as: `SLI = (Good Events / Total Events) * 100%`.
   - *Example:* "Percentage of successful HTTP requests (non-5xx) processed in under 300ms."

2. **SLO (Service Level Objective):**
   - A **target reliability goal** set by engineering and business stakeholders for an SLI over a specific rolling time window (e.g., 30 days).
   - *Example:* "The Payment Service SLI must be >= 99.95% over any rolling 30-day window."

3. **Relationship with SLA & Error Budget:**
   - **SLA (Service Level Agreement):** The contractual commitment to external clients with financial penalties if breached (usually set lower than the internal SLO, e.g., 99.9%).
   - **Error Budget:** `100% - SLO`. For an SLO of 99.95%, the allowable downtime/error budget over 30 days is **0.05% (~21.6 minutes)**.
</details>

<details>
<summary><strong>↳ Follow-up: Given a payment microservice, how would you define SLIs and SLOs for it, and how would you implement monitoring for them using Grafana?</strong></summary>

**Answer:**
For a mission-critical **Payment Microservice**, reliability and latency are paramount:

**1. Defined SLIs and SLOs:**
- **Availability SLI:**
  $$\text{SLI}_{\text{avail}} = \frac{\sum \text{rate(http\_requests\_total}\{\text{status} ! \sim \text{"5.."}\}[5m])}{\sum \text{rate(http\_requests\_total}[5m])} \times 100$$
  - **Availability SLO:** **99.99%** successful responses over a rolling 30-day period.
- **Latency SLI:**
  $$\text{SLI}_{\text{latency}} = \frac{\sum \text{rate(http\_request\_duration\_seconds\_bucket}\{\text{le}="0.5"\}[5m])}{\sum \text{rate(http\_request\_duration\_seconds\_count}[5m])} \times 100$$
  - **Latency SLO:** **99%** of requests must complete in under **500ms** over 30 days.

**2. Grafana Implementation:**
- **Error Budget Gauge Panel:** Visualizes remaining error budget in percentage using PromQL:
  ```promql
  (
    (sum(increase(http_requests_total{job="payment-service", status!~"5.."}[30d])) or vector(0))
    /
    sum(increase(http_requests_total{job="payment-service"}[30d]))
    - 0.9999
  ) / (1 - 0.9999) * 100
  ```
- **Multi-Window Multi-Burn-Rate Alerts:** Configured in Alertmanager to fire high-priority pages to on-call engineers if the service consumes **2% of the 30-day budget in 1 hour** (Burn Rate = 14.4x), preventing total budget exhaustion.
</details>

<details>
<summary><strong>↳ Follow-up: In the context of dashboards, do you know what the 'golden signals' are in monitoring?</strong></summary>

**Answer:**
The **Four Golden Signals** are the foundational monitoring metrics defined in Google's SRE framework for monitoring customer-facing systems:

1. **Latency:**
   - The time it takes to service a request.
   - Crucial distinction: Measure latency of **successful requests** separately from **failed requests** (e.g., a fast HTTP 500 error can falsely mask slow database queries).

2. **Traffic:**
   - A measure of demand placed on the system.
   - Measured as HTTP requests per second (RPS), concurrent active connections, or network I/O bits/sec.

3. **Errors:**
   - The rate of requests that fail.
   - Includes **explicit errors** (HTTP 500 internal errors), **implicit errors** (HTTP 200 containing an error payload), and policy violations (aborted transactions).

4. **Saturation:**
   - A measure of how full your service is, emphasizing the most constrained resources.
   - Examples: Memory usage %, CPU throttling percentage, database connection pool exhaustion, or disk queue depth. Systems degrade non-linearly when saturation exceeds 85%.
</details>

<details>
<summary><strong>↳ Follow-up: Suppose you need to collect and monitor logs from millions of real users in real time — how would you design and implement such a real-time monitoring system?</strong></summary>

**Answer:**
Handling real-time logs from millions of concurrent users requires a distributed, highly decoupled **streaming ingest and analytics architecture**:

```
[ Millions of Users / Edge Clients ]
                |
          (HTTPS / WSS)
                v
[ AWS CloudFront CDN / API Gateway ]
                |
                v
  [ Ingestion Layer: Apache Kafka / AWS Kinesis ]
  (Partitioned by user_id / session_id; absorbs massive traffic spikes)
                |
      +---------+---------+
      |                   |
      v                   v
[ Stream Processing ]   [ Data Firehose: Cold Storage ]
(Apache Flink / Spark)   |
- Real-time aggregation  v
- Error rate anomalies   [ Amazon S3 Data Lake ]
- Security abuse checks  (Parquet / Snappy format; queryable via Athena)
      |
      v
[ High-Throughput Search / Analytics ]
- OpenSearch / ClickHouse Cluster
- Grafana Real-Time Dashboards & Alerts (< 5s latency)
```

**Key Architectural Decisions:**
1. **Decoupled Buffer (Apache Kafka / AWS Kinesis):**
   Edge ingestion services never write directly to Elasticsearch/OpenSearch. Kafka acts as an elastic shock absorber with multiple partitions to prevent backpressure from crashing services during traffic surges.
2. **Stream Processing (Apache Flink):**
   Computes rolling sliding-window aggregations (e.g., counting HTTP 5xx errors per second) and detects anomalous patterns in real time without storing every raw payload in the search index.
3. **Tiered Storage (Hot vs. Cold):**
   - **Hot Storage (ClickHouse / OpenSearch):** Indexes aggregated logs and error traces for 7 days for sub-second developer debugging.
   - **Cold Storage (Amazon S3):** Kinesis Data Firehose converts logs into Parquet format for long-term retention and cost-effective compliance queries using Amazon Athena.
</details>
</details>
</details>"""
