# Add your variable declarations here

variable "availability_zone" {
  description = "The availability zone for the subnets"
  type        = string
}

variable "public_subnet_cidr" {
  description = "The CIDR block for the public subnet"
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC where the subnets will be created"
  type        = string
}

# create two subnets, one public and one private
resource "aws_subnet" "public_subnet" {
  vpc_id            = var.vpc_id
  cidr_block        = var.public_subnet_cidr
  availability_zone = var.availability_zone
  tags = {
    Name = "${var.name_prefix}-public-subnet"
  }
}

variable "name_prefix" {
  description = "The prefix for naming resources"
  type        = string
}

variable "private_subnet_cidr" {
  description = "The CIDR block for the private subnet"
  type        = string
}

resource "aws_subnet" "private_subnet" {
  vpc_id            = var.vpc_id
  cidr_block        = var.private_subnet_cidr
  availability_zone = var.availability_zone
  tags = {
    Name = "${var.name_prefix}-private-subnet"
  }
}