# Terraform: Create a Jenkins pipeline that integrates with Terraform. With the click of a build button in Jenkins, the pipeline should trigger Terraform to provision infrastructure resources on a cloud provider. Practice this and capture screenshots of the successful build.

## Table of Contents

1. [Install Jenkins and Terraform](#1-install-jenkins-and-terraform)
2. [Create Jenkinsfile and Terraform Configuration](#2-create-jenkinsfile-and-terraform-configuration)
   - [Jenkinsfile](#jenkinsfile)
   - [provider.tf](#providertf)
   - [vpc.tf](#vpctf)
   - [subnet.tf](#subnettf)
   - [route_table.tf](#route_tabletf)
   - [igw.tf](#igwtf)
   - [nat_eip.tf](#nat_eiptf)
   - [nat_gw.tf](#nat_gwtf)
   - [security_group.tf](#security_grouptf)
   - [ec2.tf](#ec2tf)
   - [s3-bucket.tf](#s3-buckettf)
3. [Provision the S3 Remote Backend](#3-provision-the-s3-remote-backend)
4. [Configure Jenkins](#4-configure-jenkins)
5. [Run the Jenkins Pipeline](#5-run-the-jenkins-pipeline)
6. [Destroy the Infrastructure](#6-destroy-the-infrastructure)
7. [Screenshots](#7-screenshots)

   
Ans:

* Install Jenkins and terraform on your ubuntu server.  
  * Create Jenkinsfile and terraform configuration files on github. The files are configured here: [https://github.com/nagaraj602/Notes/tree/main/Jenkins-Assignment/simple-terraform-integration-with-jenkins](https://github.com/nagaraj602/Notes/tree/main/Jenkins-Assignment/simple-terraform-integration-with-jenkins) 

  Here is the each and every file content:

-->  vi Jenkinsfile
```
pipeline {  
    agent any

    environment {  
        AWS_ACCESS_KEY_ID     = credentials('AWS_ACCESS_KEY_ID')  
        AWS_SECRET_ACCESS_KEY = credentials('AWS_SECRET_ACCESS_KEY')  
        AWS_DEFAULT_REGION    = 'us-east-1'  
    }

    stages {

        stage('Terraform Init') {  
            steps {  
                dir('Jenkins-Assignment/simple-terraform-integration-with-jenkins') {  
                    sh 'terraform init'  
                }  
            }  
        }

        stage('Terraform Plan') {  
            steps {  
                dir('Jenkins-Assignment/simple-terraform-integration-with-jenkins') {  
                    // Output the plan to a file so the exact same plan is applied later  
                    sh 'terraform plan -out=tfplan'  
                }  
            }  
        }

        stage('Manual Approval') {  
            steps {  
                input message: 'Review the Terraform Plan output above. Do you want to provision this infrastructure?',  
                      ok: 'Yes, Apply'  
            }  
        }

        stage('Terraform Apply') {  
            steps {  
                dir('Jenkins-Assignment/simple-terraform-integration-with-jenkins') {  
                    // Apply the exact plan generated in the previous stage  
                    sh 'terraform apply --auto-approve tfplan'  
                }  
            }  
        }  
    }

    post {  
        always {  
            cleanWs()  
        }  
    }  
}
```
--> :wq  
--> vi provider.tf


```  
terraform {  
  required_version = ">= 1.15.0"

  required_providers {  
    aws = {  
      source  = "hashicorp/aws"  
      version = ">= 6.51.0"  
    }  
  }  
  backend "s3" {  
    bucket = "remote-backend-s3-jan2026-Nagaraj"  
    key    = "simple-terraform-Jenkins-pipeline/terraform.tfstate"  
    region = "us-east-1"  
    use_lockfile = true  
  }  
}

provider "aws" {  
  region = "us-east-1"  
}
```
--> :wq


--> vi vpc.tf
```
resource "aws_vpc" "three_tier_vpc" {  
  cidr_block = "10.0.0.0/16"  
  enable_dns_support = true  
  enable_dns_hostnames = true

  tags = {  
    Name = "three-tier-vpc"  
  }  
}
```
--> :wq


--> vi subnet.tf
```
# Public Subnet  
resource "aws_subnet" "public_subnet_1" {  
  vpc_id     = aws_vpc.three_tier_vpc.id  
  cidr_block = "10.0.1.0/24"  
  availability_zone      = "us-east-1a"  
  map_public_ip_on_launch = true

  tags = {  
    Name = "public-subnet-1"  
  }  
}

# Private Subnet  
resource "aws_subnet" "private_subnet_1" {  
  vpc_id     = aws_vpc.three_tier_vpc.id  
  cidr_block = "10.0.2.0/24"  
  availability_zone      = "us-east-1a"

  tags = {  
    Name = "private-subnet-1"  
  }  
}
```
--> :wq


--> vi route_table.tf
```
# Create Public Route Table  
resource "aws_route_table" "public_route_table" {  
  vpc_id = aws_vpc.three_tier_vpc.id  
  route {  
    cidr_block = "0.0.0.0/0"  
    gateway_id = aws_internet_gateway.igw.id     #For igw, we use gateway_id  
  }  
  tags = {  
    Name = "public-route-table"  
  }  
}

# Associate Route Table with Public Subnet  
resource "aws_route_table_association" "public_rta" {  
  subnet_id      = aws_subnet.public_subnet_1.id  
  route_table_id = aws_route_table.public_route_table.id  
}

# Creating Private Route Table  
resource "aws_route_table" "private_route_table" {  
  vpc_id = aws_vpc.three_tier_vpc.id

  route {  
    cidr_block     = "0.0.0.0/0"  
    nat_gateway_id = aws_nat_gateway.nat_gw.id  
  }  
  tags = {  
    Name = "private-route-table"  
  }  
}

# Route Table Association for Private Subnet  
resource "aws_route_table_association" "private_rta" {  
  subnet_id      = aws_subnet.private_subnet_1.id  
  route_table_id = aws_route_table.private_route_table.id  
}
```
--> :wq


--> vi igw.tf
```
# Creating Internet Gateway  
resource "aws_internet_gateway" "igw" {  
  vpc_id = aws_vpc.three_tier_vpc.id  
  tags = {  
    Name = "three_tier_igw"  
  }  
}
```
--> :wq

--> vi nat_eip.tf
```
# Creating Elastic IP for NAT Gateway  
resource "aws_eip" "nat_eip" {  
  domain = "vpc"  
}
```
--> :wq

--> vi nat_gw.tf
```
# Creating NAT Gateway  
resource "aws_nat_gateway" "nat_gw" {  
  allocation_id = aws_eip.nat_eip.id  
  subnet_id     = aws_subnet.public_subnet_1.id

  # Explicit dependency on the Internet Gateway  
  depends_on = [aws_internet_gateway.igw]  
}
```
--> :wq

--> vi security_group.tf
```
resource "aws_security_group" "allow_port_80_and_22" {  
  name        = "allow_port_80_and_22"  
  description = "Allow TLS inbound traffic"  
  vpc_id      = aws_vpc.three_tier_vpc.id

  tags = {  
    Name = "allow_port_80_and_22"  
  }  
}

resource "aws_vpc_security_group_ingress_rule" "allow_tls_ipv4" {  
  security_group_id = aws_security_group.allow_port_80_and_22.id  
  cidr_ipv4   = "0.0.0.0/0"  
  from_port   = 80  
  ip_protocol = "tcp"  
  to_port     = 80  
}

resource "aws_vpc_security_group_ingress_rule" "allow_ssh_ipv4" {  
  security_group_id = aws_security_group.allow_port_80_and_22.id  
  cidr_ipv4   = "0.0.0.0/0"  
  from_port   = 22  
  ip_protocol = "tcp"  
  to_port     = 22  
}

resource "aws_vpc_security_group_egress_rule" "allow_all_traffic_ipv4" {  
  security_group_id = aws_security_group.allow_port_80_and_22.id  
  cidr_ipv4   = "0.0.0.0/0"  
  ip_protocol = "-1"    # semantically equals to all ports and all protocols  
}

resource "aws_vpc_security_group_egress_rule" "allow_all_traffic_ipv6" {  
  security_group_id = aws_security_group.allow_port_80_and_22.id  
  cidr_ipv6   = "::/0"  
  ip_protocol = "-1"    # semantically equals to all ports and all protocols  
}
```
--> :wq

--> vi ec2.tf
```
resource "aws_instance" "web_instance" {  
  ami                    = "ami-0b6d9d3d33ba97d99" # Specify appropriate AMI  
  instance_type          = "t3.medium"  
  availability_zone      = "us-east-1a"  
  subnet_id              = aws_subnet.public_subnet_1.id  
   
  # Security groups are passed as a list of IDs  
  vpc_security_group_ids = [aws_security_group.allow_port_80_and_22.id]

  tags = {  
    Name = "terraform_EC2"  
  }  
}
```
--> :wq  
    
--> vi s3-bucket.tf        (# Don't include this in github, as this needs to be created first separately, then you can run the rest of the configuration as terraform needs s3 bucket to store state when terraform plan command is run)


```
terraform {  
  required_version = ">= 1.15.0"  
  required_providers {  
    aws = {  
      source  = "hashicorp/aws"  
      version = ">= 6.51.0"  
    }  
  }  
}

provider "aws" {  
  region = "us-east-1"  
}

resource "aws_s3_bucket" "remote_backend_s3" {  
  bucket        = "remote-backend-s3-jan2026-Nagaraj-29-07-2026"  
  force_destroy = true    # only if you're planning to delete bucket in future  
}

resource "aws_s3_bucket_versioning" "versioning_bucket" {  
  bucket = aws_s3_bucket.remote_backend_s3.id  
  versioning_configuration {  
    status = "Enabled"  
  }  
}
```
--> :wq  
    
* All the above files are saved at github except s3-bucket.tf.  
* Now, I will provision the s3 bucket for the remote backend by just using: s3-bucket.tf file.  
    
```
terraform init;terraform plan;terraform apply –auto-approve
```
    
  Once done, you can configure the rest of the things in Jenkins dashboard.  
    
  * Configure AWS CLI credentials in Jenkins Credentials section: Manage Jenkins >> Credentials >> Add Credentials >> Secret text >> Secret: * >> ID: AWS_ACCESS_KEY_ID >> Create >> Add Credentials >> Secret text >> Secret: * >> ID: AWS_SECRET_ACCESS_KEY   
  * Go to Jenkins dashboard >> Add new Item >> Pipeline >> Name: simple-terraform-Jenkins-pipeline >> Ok >> Scroll down >> Select: Pipeline script from SCM >> SCM: Git >> Repository URL: [https://github.com/nagaraj602/Notes.git](https://github.com/nagaraj602/Notes.git) >> Branch Specifier (blank for 'any'): */main >> Script Path: Jenkins-Assignment/simple-terraform-integration-with-jenkins/Jenkinsfile  >> Save.  
  * Build Now >> Go to Console output >> Review the changes and approve.

  * If you want to destroy the above infra, then clone the repo and run the
    ```
    git clone https://github.com/nagaraj602/Notes.git
    cd Notes/Jenkins-Assignment/simple-terraform-integration-with-jenkins/
    terraform init
    terraform plan
    terraform destroy --auto-approve
    ```
    
<img width="2048" height="1224" alt="1" src="https://github.com/user-attachments/assets/972f3225-d53b-45eb-9fe3-9056fd80d8ec" />
<img width="2048" height="1221" alt="2" src="https://github.com/user-attachments/assets/037af922-01d3-4d73-b237-3cb75a1959ca" />
<img width="2041" height="1214" alt="3" src="https://github.com/user-attachments/assets/cff847f1-f158-452a-b722-d7624b0b5dc4" />
<img width="2041" height="1217" alt="4" src="https://github.com/user-attachments/assets/4ba1b81a-a98f-405a-b722-d7624b0b5dc4" />
<img width="2041" height="1217" alt="5" src="https://github.com/user-attachments/assets/09357727-6526-4bad-ad44-237509c1d630" />
<img width="2041" height="1217" alt="6" src="https://github.com/user-attachments/assets/7e1c4fd6-a0b0-497d-8c5b-caab651e7378" />
<img width="2041" height="1217" alt="7" src="https://github.com/user-attachments/assets/d17b012f-f9c2-4f99-ac4c-2dd89db995b3" />
<img width="2048" height="1221" alt="8" src="https://github.com/user-attachments/assets/54eb20c1-07b2-4c1b-9d3e-aec11a4241a1" />
<img width="2048" height="1221" alt="9" src="https://github.com/user-attachments/assets/758d09d3-6cac-4826-a5d8-8b7b137eff73" />
<img width="2041" height="1214" alt="a1" src="https://github.com/user-attachments/assets/7a9aa90d-10c0-479d-bc75-4474d90e2aeb" />
<img width="2041" height="1217" alt="a2" src="https://github.com/user-attachments/assets/769eeb8e-1f13-43cb-af5d-e5cf4291c51d" />
