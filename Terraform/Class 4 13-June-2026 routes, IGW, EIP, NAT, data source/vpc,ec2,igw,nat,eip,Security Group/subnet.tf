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
