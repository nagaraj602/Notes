data "aws_vpc" "three_tier_vpc" {
  tags = {
    Name = "default"
  }
}


# Accessing the fetched VPC ID
output "vpc_id" {
  value = data.aws_vpc.three_tier_vpc.id
}
