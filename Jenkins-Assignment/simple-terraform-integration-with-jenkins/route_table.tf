# Create Public Route Table
resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.three_tier_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id     #For igw, we use gateway_id
  } 
  tags = {
    Name = "public-route-table"
  }
}


# Associate Route Table with Public Subnet
resource "aws_route_table_association" "public_rta" {
  subnet_id      = aws_subnet.public_subnet_1.id
  route_table_id = aws_route_table.public_route_table.id
}


# Creating Private Route Table
resource "aws_route_table" "private_route_table" {
  vpc_id = aws_vpc.three_tier_vpc.id


  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gw.id
  }
  tags = {
    Name = "private-route-table"
  }
}


# Route Table Association for Private Subnet
resource "aws_route_table_association" "private_rta" {
  subnet_id      = aws_subnet.private_subnet_1.id
  route_table_id = aws_route_table.private_route_table.id
}
