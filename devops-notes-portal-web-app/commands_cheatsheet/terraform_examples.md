# Terraform YAML & HCL Examples

> Production-grade Terraform module definitions, remote state backends, VPC architectures, and cloud-init integrations.

## 1. Production AWS VPC with Public/Private Subnets and NAT Gateways
**Description**: Complete multi-AZ Virtual Private Cloud (VPC) with public subnets, private subnets, Internet Gateway, and redundant NAT Gateways.

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "prod-terraform-state-lock-bucket"
    key            = "networking/vpc/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Environment = "Production"
      ManagedBy   = "Terraform"
      Project     = "CoreInfrastructure"
    }
  }
}

variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "prod-main-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "prod-main-igw" }
}

# Public Subnets (AZ-a & AZ-b)
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
  tags = { Name = "prod-public-subnet-1a" }
}

# NAT Gateway for Outbound Internet in Private Subnets
resource "aws_eip" "nat" {
  domain = "vpc"
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_a.id
  tags          = { Name = "prod-nat-gateway-1a" }
}
```

## 2. Cloud-Init User-Data YAML Integration with Terraform
**Description**: Injecting structured YAML user-data templates into EC2 instances to provision Docker and Node Exporter on boot.

```hcl
data "cloudinit_config" "server_config" {
  gzip          = false
  base64_encode = true

  part {
    content_type = "text/cloud-config"
    content = <<-EOF
      #cloud-config
      package_update: true
      packages:
        - apt-transport-https
        - ca-certificates
        - curl
        - docker.io
      
      write_files:
        - path: /etc/systemd/system/node_exporter.service
          permissions: '0644'
          content: |
            [Unit]
            Description=Node Exporter
            After=network.target
            [Service]
            ExecStart=/usr/local/bin/node_exporter
            Restart=always
            [Install]
            WantedBy=multi-user.target
      
      runcmd:
        - systemctl enable --now docker
        - systemctl enable --now node_exporter
    EOF
  }
}

resource "aws_instance" "app_server" {
  ami           = "ami-0c7217cdde317cfec"
  instance_type = "t3.medium"
  user_data     = data.cloudinit_config.server_config.rendered
  tags = {
    Name = "prod-app-server"
  }
}
```
