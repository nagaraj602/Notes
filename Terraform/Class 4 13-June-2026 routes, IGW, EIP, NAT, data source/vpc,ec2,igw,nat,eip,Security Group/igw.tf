# Creating Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.three_tier_vpc.id
  tags = {
    Name = "three_tier_igw"
  }
}
