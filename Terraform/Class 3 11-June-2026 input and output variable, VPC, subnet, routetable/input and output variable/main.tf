resource "aws_instance" "terraform_first_instance" {
  ami = "ami-0521cb2d60cfbb1a6"    #(ubuntu AMI) Example AMI ID, ensure it matches the region
  instance_type = "t3.micro"
  key_name = "nagaraj"  #Key pair name specified in your aws: public_key name
  
  tags = {
    Name = "terraform_EC2"
  }
}
