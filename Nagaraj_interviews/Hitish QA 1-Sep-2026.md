# 🏢 Hitish QA 1-Sep-2026 - Interview Experience & Question Bank

> Real DevOps interview questions, technical follow-up questions, and production-tested solutions recorded from actual interview rounds.

---

## 📋 Interview Schedules & Metadata

- **Company:** Hitish QA 1-Sep-2026

---

## ❓ Technical Questions & Answers

### 🎯 Round: Technical Round 1

#### Q1: How do the Jenkins master and slave communicate?
**Tags:** `Linux` `jenkins` `Kubernetes` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Follow-up / Sub-questions:**
- So I said it is through SSH connection right? So how do you establish an SSH connection? Basically how that SSH connection gets authenticated?
- Is there any other way where master can communicate with slaves other than an SSH connection?
- Why is there a method called JNLP (Java Network Launch Protocol)? What are the use cases for it?

**Answer / Solution:**
If a slave is sitting behind a firewall, the master node cannot directly bypass it and communicate via SSH. In this case, you use JNLP. It establishes an inbound connection where the agent reaches out to communicate with the master.

**Action Items / Takeaways:**
Review how both SSH and JNLP connections happen, and look at the "Manage Nodes" section in Jenkins.
Kubernetes Troubleshooting: Pods & Deployments

</details>

---

#### Q2: You run the kubectl top nodes command. It is showing plenty of CPU available, but a pod remains in a pending state. What could be the possible reasons for it?
**Tags:** `Kubernetes` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Follow-up / Sub-questions:**
- Any other reasons you can think of?

**Answer / Solution:**
The requested CPU might be greater than the allocatable CPU, memory shortage, node taints, node affinity/anti-affinity rules, and topology constraints.

</details>

---

#### Q3: You deploy 10 replicas. Five new pods become healthy, but the other five never start. What are the potential causes, how do you investigate, and how will you troubleshoot?
**Tags:** `Kubernetes` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

To be reviewed / prepared.

</details>

---

#### Q4: You deployed version 2 of an application. Within 2 minutes, production traffic starts failing. What are your first five actions?
**Tags:** `Kubernetes` `Agile` `Monitoring tools` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Answer / Solution:**
Confirm the impact (verify production is actually down).
Check the metrics dashboards and errors, comparing V1 and V2.
Determine if it is immediately fixable (create a hotfix).
If it is not immediately fixable, roll back to the previous stable deployment.
Then investigate, do a Root Cause Analysis (RCA), circulate it to the team, and explain the scenario/fix to the clients. Do not prioritize RCA over restoring production.
Kubernetes: Autoscaling & Resource Management

</details>

---

#### Q5: Your production traffic is increasing, and your cluster has reached around 90% utilization. In this scenario, what would you do?
**Tags:** `Kubernetes` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Follow-up / Sub-questions:**
- What if the cluster autoscaler refuses to add another node?

</details>

---

#### Q6: CPU utilization is 90% but your HPA (Horizontal Pod Autoscaler) stays at three replicas. What do you check?
**Tags:** `Kubernetes` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Follow-up / Sub-questions:**
- What in the HPA configuration are you going to increase or decrease?
- Take a scenario where HPA isn't scaling up. What potential areas are you going to check?

</details>

---

#### Q7: What is the difference between HPA and VPA (Vertical Pod Autoscaler)?
**Tags:** `Kubernetes` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Follow-up / Sub-questions:**
- What is VPA? Can you explain again?

</details>

---

#### Q8: How do you perform a Kubernetes rolling update?
**Tags:** `jenkins` `Kubernetes` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Follow-up / Sub-questions:**
- Pick any one method (e.g., Blue-Green) and explain it in detail.
- What are you going to update in order to switch the traffic from blue to green? How are you going to do it?
- Environments, Promotion & CI/CD Pipelines

</details>

---

#### Q9: Can you describe any issues you have come across or faced when doing a deployment to production?
**Tags:** `Kubernetes` `Agile` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Answer / Solution:**
Don't just mention pre-prod issues (like missing ports or basic typos). Have solid, real-world production use cases prepared.

</details>

---

#### Q10: What testing is done with respect to different environments? Why is there a dev, staging, pre-prod, and prod? What happens from stage to stage?
**Tags:** `Agile` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

To be reviewed / prepared.

</details>

---

#### Q11: How are you going to ship/promote the code from dev to production?
**Tags:** `jenkins` `Build tools` `Docker` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Answer / Solution:**
The core ideology is "Build once, deploy many." You do not rebuild the image for every environment; you promote the same artifact. Understand architectural strategies (e.g., using a single generic CI pipeline for lower environments deploying to different namespaces, and a separate, restricted pipeline with approval gates for production).
Docker Images & Security

</details>

---

#### Q12: Do you know what a distroless image is? What is the use of it?
**Tags:** `Docker` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Answer / Solution:**
Don't just stop at Alpine images. Understand the concept and security benefits of distroless images.

</details>

---

#### Q13: What do you understand by a golden image? Have you heard about it?
**Tags:** `Docker` `AWS` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Answer / Solution:**
In enterprise environments, you don't pull base images randomly via Dockerfile. You create a standardized, pre-configured "Golden Image" (or AMI in AWS) and build on top of that.

</details>

---

#### Q14: Your application needs a DB password. How would you securely provide it to the pod?
**Tags:** `AWS` `Kubernetes` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Answer / Solution:**
Integrate with a secrets manager (like AWS Secrets Manager), store the DB password there, and inject it into the pod using a secret key reference.
Helm & Monitoring

</details>

---

#### Q15: What is the use of Helm and why should we go with it?
**Tags:** `Kubernetes` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Follow-up / Sub-questions:**
- Are you aware of Helm hooks and can you give a use case for it?

**Answer / Solution:**
Look into Helm hooks deeply, as they are widely used in enterprise deployments.

</details>

---

#### Q16: How would you design monitoring and alerting for a production-grade application?
**Tags:** `Monitoring tools` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Follow-up / Sub-questions:**
- What is the architecture, what tools are you going to use, and what things will you put in place?

**Answer / Solution:**
Prepare a complete architectural overview for this answer, not just isolated tool names.
WS/Infrastructure

</details>

---

#### Q17: You have an EC2 instance which is running, but you cannot SSH into it. How do you check and how do you move forward with this?
**Tags:** `Linux` `jenkins` `Docker` `AWS` | **Difficulty:** `Moderate`

<details open>
<summary><strong>💡 Answer / Solution & Takeaways</strong></summary>

**Follow-up / Sub-questions:**
- Any other reasons you can think of?

**Answer / Solution:**
Check the Security Groups and Network ACLs to ensure TCP port 22 is explicitly allowed.

**Action Items / Takeaways:**
JNLP: How it works and how it connects behind firewalls.
Distroless Images: What they are and their benefits.
Golden Images: How to create them and why enterprises use them.

</details>

---

