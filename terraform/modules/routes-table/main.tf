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

resource "aws_route_table" "private_rt" {
  vpc_id = var.vpc_id
  tags = {
    Name = "${var.name_prefix}-private-rt"
  }
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public_rt.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = var.igw_id
}

resource "aws_route_table_association" "public" {
  subnet_id      = var.public_subnet_id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "private" {
  subnet_id      = var.private_subnet_id
  route_table_id = aws_route_table.private_rt.id
}