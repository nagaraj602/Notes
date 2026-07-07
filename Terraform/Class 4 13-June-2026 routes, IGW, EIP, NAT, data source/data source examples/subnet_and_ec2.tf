data "aws_subnet" "subnet_details" {
  tags = {
    Name = "us-east-1c"
  }
}


resource "aws_instance" "data_source_instance" {
  ami               = "ami-0521cb2d60cfbb1a6"
  instance_type     = "t3.medium"
  availability_zone = "us-east-1c"
 
  # Referencing the ID from the data source
  subnet_id         = data.aws_subnet.subnet_details.id
}
