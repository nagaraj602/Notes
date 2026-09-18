# AWS CLI v2 Commands Cheat Sheet

> Production AWS CLI commands for EC2, S3, IAM, VPC, EKS, CloudWatch, and RDS infrastructure management.

| Command | Description & AI Explanation | Category / Tags |
| :--- | :--- | :--- |
| `aws sts get-caller-identity` | Verifies current AWS CLI credential authentication, returning the IAM ARN, Account ID, and UserId. First sanity check before running AWS commands. | IAM, Authentication |
| `aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --query "Reservations[*].Instances[*].[InstanceId,PrivateIpAddress,PublicIpAddress,Tags[?Key=='Name'].Value\|[0]]" --output table` | Queries running EC2 instances with JMESPath projection, printing Instance ID, Private IP, Public IP, and Name tag in a clean formatted ASCII table. | EC2, Compute |
| `aws ec2 stop-instances --instance-ids i-0123456789abcdef0` | Gracefully stops an EC2 instance without deleting attached EBS root volumes, halting compute hour billing. | EC2, Cost Management |
| `aws ec2 describe-security-groups --filters "Name=ip-permission.from-port,Values=22" --query "SecurityGroups[*].[GroupId,GroupName,IpPermissions[?FromPort==\`22\`].IpRanges[*].CidrIp]" --output json` | Audits security groups allowing inbound SSH (port 22) traffic, identifying dangerous 0.0.0.0/0 exposure. | Security, VPC, Audit |
| `aws s3 sync ./dist/ s3://my-static-bucket/ --delete --cache-control "max-age=31536000"` | Incrementally uploads frontend assets to S3, removes remote files no longer in local directory, and sets aggressive 1-year browser cache headers. | S3, Web Hosting |
| `aws s3 ls s3://my-data-bucket/ --recursive --human-readable --summarize` | Recursively inspects an S3 bucket path and computes total object count and cumulative storage size in MB/GB. | S3, Storage |
| `aws iam list-access-keys --user-name devops-admin` | Lists IAM access key IDs and creation dates for a specific user to track key age and enforce key rotation policies. | IAM, Security |
| `aws eks update-kubeconfig --region us-east-1 --name prod-cluster` | Downloads cluster API endpoint and CA certificate, automatically configuring local ~/.kube/config to interact with AWS EKS cluster via kubectl. | EKS, Kubernetes |
| `aws rds describe-db-instances --query "DBInstances[*].[DBInstanceIdentifier,DBInstanceClass,Engine,DBInstanceStatus,Endpoint.Address]" --output table` | Lists RDS database instances, displaying compute tier, database engine (postgres/mysql), status, and endpoint DNS. | RDS, Database |
| `aws logs tail /aws/eks/prod-cluster/cluster --follow --filter-pattern "ERROR"` | Streams real-time CloudWatch log events from EKS control plane logs matching ERROR keyword directly to the terminal. | CloudWatch, Observability |
| `aws secretsmanager get-secret-value --secret-id prod/app/db --query SecretString --output text \| jq .` | Retrieves database credentials stored in AWS Secrets Manager and formats the JSON output with jq. | Secrets, Security |
| `aws route53 list-resource-record-sets --hosted-zone-id Z123456 --query "ResourceRecordSets[?Type=='A']"` | Queries Route 53 DNS zone for all A address records mapping hostnames to IP addresses or CloudFront/ALB aliases. | Route53, Networking |
| `aws elbv2 describe-target-health --target-group-arn <TG-ARN>` | Inspects health status of EC2/container instances registered behind an Application Load Balancer target group. | ALB, High Availability |
