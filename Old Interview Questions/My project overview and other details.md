E-Commerce - Marketplace Risk Detection Platform
PROJECT OVERVIEW
The project involved building a Marketplace Seller Risk & Abuse Detection Platform for a large online marketplace connecting third-party sellers with buyers. As the platform scaled to tens of thousands of sellers and millions of listings, it became a target for fake listings, review manipulation, seller account takeovers, and abuse ratings using networks of fake accounts.

The platform continuously ingests signals from listing creation, seller account activity, orders, and reviews, detects suspicious patterns in near real-time, routes high-confidence cases for automated action and lower-confidence cases to a trust & safety analyst queue, and triggers enforcement actions (seller suspension, listing takedown, payout holds) through the marketplace's existing systems.

It was designed using a microservices architecture to allow independent scaling of ingestion, detection, and case-management workloads.

MICROSERVICES ARCHITECTURE
The platform consisted of approximately 22-25 microservices. Key microservices include:

Event Ingestion Service: Consumes events from marketplace Kafka topics (listings, seller accounts, orders, reviews) and normalizes them into an internal schema.
Signal Enrichment Service: Adds contextual data like device fingerprinting, IP geolocation, and seller account history to incoming events.
Entity Graph Service: Maintains a graph of relationships between sellers, devices, payment methods, and addresses to surface hidden links between related accounts.
Velocity Rule Engine Service: Evaluates real-time rules against event streams (e.g., listings-per-hour thresholds, multiple accounts sharing a device).
Anomaly Scoring Service: Generates a statistical anomaly score based on seller/account behavior, feeding in as a signal alongside rule outputs.
Risk Aggregation Service: Combines rule hits and anomaly scores into a risk score per entity and determines routing (auto-action, analyst review, or dismiss).
Case Queue Service: Maintains the prioritized queue of flagged entities awaiting analyst review, with SLA-based aging.
Enforcement Orchestration Service: Converts confirmed decisions into calls to the marketplace's existing seller/listing APIs (suspension, takedown, payout hold), with retry handling.
TOOLS & TECHNOLOGIES
Kubernetes: For container orchestration and independent autoscaling of ingestion, detection, and case-management workloads.
Jenkins: For CI/CD pipelines, including canary rollouts for rule/config changes.
Kafka: Backbone for consuming marketplace events and internal service communication, partitioned by seller ID.
Prometheus & Grafana: For monitoring detection latency, queue depth, false-positive rate, and Kafka consumer lag.
ELK Stack: For centralized logging and audit trails.
Distributed Databases (MongoDB, Redis, Neo4j): Used across services based on access pattern: case data, real-time velocity counters, and entity relationship graphs respectively.
Java / Go: Backend languages used for the microservices.
KEY RESULTS & IMPACT
Reduced average time-to-detection for abusive seller activity from days to under 10 minutes for high-confidence automated cases.
Cut manual review workload for the trust & safety team by an estimated 60%.
Reduced fake listing and review manipulation incidents, improving buyer trust metrics.
Improved detection pipeline stability during peak sale events through better autoscaling and Kafka partition tuning.
Anticipated Follow-Up Questions
Only if asked specifically during the interview
“How did you handle scaling during peak events like flash sales?”
“We ran ingestion and detection services in a separate node pool with Horizontal Pod Autoscaling tied to Kafka consumer lag rather than just CPU, and over-provisioned Kafka partitions ahead of known peak events.”

“How did you deploy rule changes safely, given the risk of false positives?”
“Rule changes went through Jenkins pipelines that ran them against shadow traffic first, comparing flag rates against production before promoting, with automated rollback if false-positive rate SLOs were breached.”

“How did the platform avoid becoming a single point of failure for enforcement actions?”
“The Enforcement Orchestration Service only made outbound calls to existing seller/listing APIs. If those were unavailable, we queued actions with retry/backoff rather than blocking the detection pipeline.”

Preparation Questions & Answers
Key responses tailored to this architecture and role.

1. Introduction
Use this response when the interviewer asks variations of:
Tell me about yourself / your background
Walk me through your resume or profile
What are your day-to-day responsibilities?
Walk me through your DevOps experience
I am Nagaraj, and I currently work as a DevOps Engineer. My primary focus is on automating the deployment and management of software applications, and I work with a wide variety of tools and technologies to make that happen.

I have hands-on experience with Jenkins, our CI/CD tool, which takes source code from developers and deploys it into different environments. I've also worked extensively with Git for source code management, creating repositories, managing branches, merging code, and resolving merge conflicts. In my team, I also take on the Admin role for both Git and Jenkins, so I handle a good share of tickets specifically related to these tools, including branching strategy, creating and deleting branches, and merge-related issues.

On the cloud side, I manage and maintain infrastructure on AWS, working with services like EC2, S3, VPC, Load Balancing, Auto Scaling, CloudWatch, CloudTrail, and IAM.

I'm responsible for our containerization stack, primarily Docker and Kubernetes. I've written Dockerfiles and optimized them using multi-stage builds to reduce image size. For deploying and managing applications on Kubernetes, I use Helm to package and template our workloads, which makes deployments more consistent and easier to manage across environments.

I've worked with Terraform to provision infrastructure as code on AWS, and I use Ansible as our configuration management tool.

Day-to-Day Responsibilities
Day to day, most of my work revolves around resolving tickets, mainly around build issues, deployment issues, Git issues, and Jenkins issues. Jira is our ticketing tool, and we prioritize tickets based on severity. Some are critical and need to be closed within a few hours. Alongside ticket work, I also focus on automation, which is an ongoing effort since there's always something that can be automated or improved.

2. Explain your Project
Use this response when the interviewer asks:
Can you walk me through the key components and architecture of your project?
I am currently working on an e-commerce project where we are developing a large-scale Marketplace Seller Risk & Abuse Detection Platform. The platform continuously ingests signals across listings, seller activity, orders, and reviews to detect and mitigate fraudulent patterns and abuse in near real-time.

In this project, I primarily handle the DevOps side of things. This includes managing the CI/CD pipeline end-to-end, starting from Git and going all the way through to deployment on EKS.

I provision infrastructure using Terraform, and for any patching or configuration management needs, we use Ansible. For monitoring, we rely on Prometheus and Grafana for metrics, along with the ELK stack for logging.

3. Explain your CI/CD strategy
Use this response when the interviewer asks:
How do you handle continuous integration and continuous deployment?
For this project, our CI/CD pipeline is built using Jenkins and covers the complete flow, starting from a developer raising a PR to final deployment on EKS. We maintain two pipelines per repo (a PR pipeline for validation and a deployment pipeline for build and release) built using a shared library approach, so common logic like Git checkout, Docker builds, Trivy scans, and Helm-based deployments is reused across projects instead of duplicated per repo.

CI Pipeline
The CI pipeline runs on every PR into dev, staging, or master, acting as our pre-merge quality gate. It starts with a Git checkout, followed by unit tests and static code analysis using SonarQube with a quality gate that hard-fails on code quality issues. Once Sonar passes, we build the Docker image locally without pushing it to ECR, then run Trivy scans across the filesystem, Dockerfile configuration, and the built image, gating on Critical and High severity vulnerabilities. If any check fails, the developer fixes the code on their feature branch and re-raises the PR. This gate runs consistently across all three branches, since it also catches new vulnerabilities surfacing between promotions, not just new code changes.

Pipeline status is reported back to GitHub directly on the PR for quick feedback, and every PR also requires approval from two admins before merging, ensuring senior oversight across the pipeline.

CD Pipeline
The CD pipeline runs after a PR is approved and merged, handling build and deployment. It builds the Docker image, pushes it to ECR, updates our Helm chart values, and deploys to the environment corresponding to the branch.

On merge to dev, the pipeline auto-deploys to a lower environment for QA testing. Once complete, a PR is raised into staging, and on merge, the change is auto-deployed to UAT for integration testing across the full flow. Once validated in UAT, a PR is raised into master where the deployment pipeline runs up to production but pauses at a manual input step, requiring explicit confirmation before it proceeds, giving us a controlled release window rather than continuous auto-deployment to prod.

Centralized Scanning
We also have a centralized scanning pipeline that runs scans across all our images and repositories independently of the build pipeline. Results are aggregated into a central vulnerability management platform, giving us consistent visibility across projects instead of results being scattered across individual Jenkins jobs. This also gives us severity-based triage, ownership assignment, and ticket creation for tracking remediation, while keeping our build pipeline fast and lightweight.

4. Explain your Branching Strategy
Use this response when the interviewer asks:
What branching strategy do you use for version control and why?
We follow a branching strategy with dev, staging, and master as our primary branches, with all feature work happening in short-lived feature branches created off dev.

Feature Development
When a developer picks up a ticket, they create a feature branch off dev, write and commit their code locally, and test it in their own local environment. Once the change is ready, they raise a PR back into dev.

Pre-Merge Gate
Every PR into dev goes through a pre-merge gate consisting of unit tests, SonarQube analysis for code quality, and a lightweight Trivy scan that gates on Critical and High severity vulnerabilities. If any of these checks fail, the developer fixes the code on their feature branch and re-raises the PR.

In addition to these automated checks, every PR into any branch (dev, staging, or master) requires approval from two admins before it can be merged. This ensures senior oversight on every merge across the entire pipeline, not just at the code-quality level.

DEV Branch
Once the PR is approved and merged into dev, our deployment pipeline automatically deploys the change to a lower environment, where QA carries out individual microservice testing, validating each service in isolation before it moves further down the pipeline.

Staging Branch / UAT
Once testing on the lower environment is complete, a PR is raised from dev into staging, again requiring two-admin approval. On merge, the change is auto-deployed to the UAT environment, where we run integration testing across the full flow, validating how all the microservices interact together end-to-end, rather than in isolation.

Master Branch / Production
Once the release is validated in UAT, a PR is raised from staging into master, again requiring two-admin approval. Deployment to production is not automated; releases are scheduled and deployed manually on a designated production deployment day, giving us a controlled release window rather than continuous auto-deployment to prod.
