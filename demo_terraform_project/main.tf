resource "aws_instance" "demo" {
  ami = "ami-123456"
  instance_type = "t2.micro"
}
