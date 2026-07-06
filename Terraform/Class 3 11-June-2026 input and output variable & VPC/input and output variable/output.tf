output "public-ip" {
  value = aws_instance.terraform_first_instance.public_ip
}


output "instance-id" {
  value = aws_instance.terraform_first_instance.id
}

