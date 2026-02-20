# Variable declaration for name_prefix
variable "name_prefix" {
  description = "Prefix for naming resources"
  type        = string
}

# build an Internet Gateway and attach it to the VPC
resource "aws_internet_gateway" "igw" {
  vpc_id = var.vpc_id
  tags = {
    Name = "${var.name_prefix}-igw"
  }
}