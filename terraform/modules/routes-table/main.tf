# Declare the name_prefix variable
variable "name_prefix" {
  description = "Prefix for naming resources"
  type        = string
}

# create 2 route tables, one for public subnets and one for private subnets
resource "aws_route_table" "public_rt" {
  vpc_id = var.vpc_id
  tags = {
    Name = "${var.name_prefix}-public-rt"
  }
}