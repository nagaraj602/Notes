# STEP 1: The Data Source 
# We are asking AWS to find the latest Ubuntu 26.04 AMI.
data "aws_ami" "latest_ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical (the company that makes Ubuntu)

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-resolute-26.04-amd64-server-*"]    # For future image change, change the version number and also the image name from: "resolute" to new one.
  }
}

# STEP 2: Creating the Instance
resource "aws_instance" "my_server" {
 ami           = data.aws_ami.latest_ubuntu.id 
  
 instance_type = "t2.micro"

 tags = {
   Name = "MyTerraformServer"
 }
}


# Accessing the fetched AMI ID
output "ami_id" {
  value = data.aws_ami.latest_ubuntu.id
}

output "ami_name" {
  value = data.aws_ami.latest_ubuntu.name
}

output "ami_description" {
  value = data.aws_ami.latest_ubuntu.description
}

