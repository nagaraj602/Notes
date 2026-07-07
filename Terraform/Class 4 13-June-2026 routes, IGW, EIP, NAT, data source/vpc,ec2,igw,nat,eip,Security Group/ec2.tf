resource "aws_instance" "web_instance" {
  ami                    = "ami-0b6d9d3d33ba97d99" # Specify appropriate AMI
  instance_type          = "t3.medium"
  availability_zone      = "us-east-1a"
  subnet_id              = aws_subnet.public_subnet_1.id
 
  # Security groups are passed as a list of IDs
  vpc_security_group_ids = [aws_security_group.allow_port_80.id]
}
