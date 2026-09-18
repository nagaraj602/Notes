# Monitoring & Observability Commands Cheat Sheet

> Essential PromQL queries, Grafana CLI, Alertmanager, and Linux telemetry commands for production monitoring.

| Command | Description & AI Explanation | Category / Tags |
| :--- | :--- | :--- |
| `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` | PromQL: Calculates percentage of total CPU utilization per instance over 5-minute rate window by inverting idle CPU seconds. | PromQL, CPU Monitoring |
| `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100` | PromQL: Accurate memory utilization percentage taking into account buffers and reclaimable page cache. | PromQL, Memory |
| `(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_free_bytes{mountpoint="/"}) / node_filesystem_size_bytes{mountpoint="/"} * 100` | PromQL: Root filesystem disk utilization percentage for alerting before disk hits 100% capacity. | PromQL, Disk Capacity |
| `sum(rate(container_cpu_usage_seconds_total{namespace="prod"}[5m])) by (pod)` | PromQL: Calculates per-pod CPU core consumption rate in production namespace to size pod resource limits. | PromQL, Kubernetes Pods |
| `sum(container_memory_working_set_bytes{namespace="prod"}) by (pod)` | PromQL: Evaluates memory working set size per pod used by Kubernetes OOMKiller for eviction decisions. | PromQL, OOM Monitoring |
| `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100` | PromQL: HTTP 5xx server error rate percentage across microservices for SLA/SLO breach alerting. | PromQL, SLO / SLA |
| `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))` | PromQL: Computes 99th percentile (p99) API latency across all requests, catching edge-case slowdowns. | PromQL, Latency |
| `amtool alert --alertmanager.url=http://alertmanager:9093` | Alertmanager CLI: Queries active firing and silenced alerts directly from Alertmanager API. | Alertmanager, Alerts |
| `amtool silence add "alertname=HighCpuUsage" --duration=2h --comment="Kernel patching window"` | Creates a 2-hour alert silence in Alertmanager to prevent notification noise during planned maintenance. | Alertmanager, Maintenance |
| `grafana-cli plugins install grafana-piechart-panel` | Installs community visualization plugin on Grafana server instance. | Grafana, Dashboards |
| `curl -s http://localhost:9100/metrics \| grep node_load1` | Queries Prometheus Node Exporter directly on port 9100 to verify metrics scraping endpoint is healthy. | Exporter, Health Check |
