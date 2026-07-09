provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "virginia_instance" {
  ami           = "ami-0b6d9d3d33ba97d99"
  instance_type = "t3.micro"
  key_name      = "nagaraj"

  tags = {
    Name = "Terraform-EC2"
  }


}

