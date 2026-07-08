resource "aws_security_group" "allow_port_80" {
  name        = "allow_port_80"
  description = "Allow TLS inbound traffic"
  vpc_id      = aws_vpc.three_tier_vpc.id

  tags = {
    Name = "allow_port_80"
  }
}


resource "aws_vpc_security_group_ingress_rule" "allow_tls_ipv4" {
  security_group_id = aws_security_group.allow_port_80.id
  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 80
  ip_protocol = "tcp"
  to_port     = 80
}

resource "aws_vpc_security_group_egress_rule" "allow_all_traffic_ipv4" {
  security_group_id = aws_security_group.allow_port_80.id
  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = "-1"    # semantically equals to all ports and all protocols
}

resource "aws_vpc_security_group_egress_rule" "allow_all_traffic_ipv6" {
  security_group_id = aws_security_group.allow_port_80.id
  cidr_ipv6   = "::/0"
  ip_protocol = "-1"    # semantically equals to all ports and all protocols
}