module "ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"

  name = "my-ec2-module-instance"

  instance_type = "t3.medium"
  key_name      = "nagaraj"
  monitoring    = true
  availability_zone = "us-east-1a"

  tags = {
    name = "my-ec2-module-instance"
    Terraform   = "true"
    Environment = "dev"
  }
}
