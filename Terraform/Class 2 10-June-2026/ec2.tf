resource "aws_instance" "my_Terraform_instance" {
  ami           = "ami-0b6d9d3d33ba97d99"
  instance_type = "t3.micro"
  key_name = "nagaraj"
  security_groups = ["All traffic open"]
  volume_size = 12
  volume_type = "gp3"
  volume_tags = {
    Name = "my_Terraform_instance_volume"
  }

  tags = {
    Name = "my_Terraform_instance_us-east-1"
  }
}