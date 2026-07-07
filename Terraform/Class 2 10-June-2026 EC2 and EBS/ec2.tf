resource "aws_instance" "my_Terraform_instance" {
  ami             = "ami-0b6d9d3d33ba97d99"
  instance_type   = "t3.micro"
  key_name        = "nagaraj"
  security_groups = ["All traffic open"] # Security Groups expects list. For writing multiple Security Group, we can add like this: security_groups = ["All traffic open","endpoint_sg"]

  # The volume configurations must go inside a block device
  root_block_device {
    volume_size = 12
    volume_type = "gp3"
    
  # Note: Inside this block, the argument is just called 'tags'
    tags = {
      Name = "my_Terraform_instance_volume"
    }
  }

  # These tags apply to the EC2 instance itself
  tags = {
    Name = "my_Terraform_instance_us-east-1"
  }
}