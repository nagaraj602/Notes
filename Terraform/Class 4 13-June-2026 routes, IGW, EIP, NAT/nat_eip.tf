# Creating Elastic IP for NAT Gateway
resource "aws_eip" "nat_eip" {
  domain = "vpc"
}
