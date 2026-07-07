resource "aws_security_group" "allow_port_80" {
  name        = "allow_port_80"
  description = "Allow TLS inbound traffic"
  vpc_id      = aws_vpc.three_tier_vpc.id


  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }


  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1" # -1 stands for all traffic/protocols
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}
