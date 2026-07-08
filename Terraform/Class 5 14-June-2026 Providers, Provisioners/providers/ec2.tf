

resource "aws_instance" "virginia_instance" {
  ami           = "ami-0b6d9d3d33ba97d99"
  instance_type = "t3.micro"
  key_name      = "nagaraj"


  tags = {
    Name = "Virginia-EC2"
  }
}


resource "aws_instance" "mumbai_instance" {
  provider = aws.mumbai


  ami           = "ami-01a00762f46d584a1"
  instance_type = "t3.micro"
  key_name      = "nagaraj"


  tags = {
    Name = "Mumbai-EC2"
  }
}
