# Public Subnet
resource "aws_subnet" "public_subnet_1" {
  vpc_id     = aws_vpc.three_tier_vpc.id
  cidr_block = "10.0.1.0/24"


  tags = {
    Name = "public-subnet-1"
  }
}




# Private Subnet
resource "aws_subnet" "private_subnet_1" {
  vpc_id     = aws_vpc.three_tier_vpc.id
  cidr_block = "10.0.2.0/24"


  tags = {
    Name = "private-subnet-1"
  }
}
