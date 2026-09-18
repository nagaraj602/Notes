# Terraform Commands Cheat Sheet

> Essential Terraform CLI commands for infrastructure provisioning, state file management, workspace branching, and drift detection.

| Command | Description & AI Explanation | Category / Tags |
| :--- | :--- | :--- |
| `terraform init -backend-config="bucket=my-state-bucket" -backend-config="dynamodb_table=tf-locks"` | Initializes working directory, downloads required provider plugins, and connects remote S3 backend with DynamoDB state locking. | Initialization, Backend |
| `terraform fmt -recursive` | Recursively rewrites all .tf and .tfvars files in current and sub-modules to canonical format and style conventions. | Formatting, Standards |
| `terraform validate` | Verifies syntactical validity and internal consistency of Terraform configuration files independently of remote state or cloud APIs. | Validation, CI/CD Gate |
| `terraform plan -out=tfplan -detailed-exitcode` | Creates an execution plan and saves it to binary file tfplan. Returns exit code 0 (no changes), 2 (changes present), or 1 (error) for CI pipelines. | Plan, Automation |
| `terraform apply -auto-approve tfplan` | Applies the exact pre-computed execution plan without interactive user confirmation prompt, guaranteeing deterministic deployment. | Apply, Provisioning |
| `terraform destroy -target=aws_instance.bastion` | Destroys only a specific targeted resource rather than tearing down the entire infrastructure stack. Useful for testing single component lifecycles. | Targeted Destroy |
| `terraform state list` | Lists all resource addresses currently tracked inside the Terraform state file. | State Management |
| `terraform state show aws_vpc.main` | Displays all attributes, IDs, CIDRs, and metadata recorded in state for a specific resource without querying cloud provider APIs. | State Inspection |
| `terraform state rm aws_s3_bucket.legacy` | Removes resource from Terraform state tracking without destroying the physical S3 bucket in AWS, allowing manual decommissioning. | State Management |
| `terraform import aws_security_group.web sg-0123456789abcdef0` | Imports pre-existing AWS resource into Terraform state management, aligning legacy infrastructure with IaC. | Adoption, Import |
| `terraform refresh` | Reads current state of remote cloud resources and reconciles local state metadata without modifying physical infrastructure. | Drift Detection |
| `terraform workspace new staging && terraform workspace select staging` | Creates and switches to isolated state workspace 'staging', enabling multi-environment provisioning from identical code. | Workspaces, Multi-Env |
| `terraform output -json` | Extracts all output variables defined in configuration in structured JSON format, ideal for consumption by Ansible or CI scripts. | Outputs, Integration |
