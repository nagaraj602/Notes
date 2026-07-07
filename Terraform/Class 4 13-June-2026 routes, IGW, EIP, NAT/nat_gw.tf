# Creating NAT Gateway
resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public_subnet.id


  # Explicit dependency on the Internet Gateway
  depends_on = [aws_internet_gateway.igw]
}
