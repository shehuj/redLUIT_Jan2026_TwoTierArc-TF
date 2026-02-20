## Build a VPC with the following attributes:
# - CIDR block: 
# - Tenancy: default
# - Enable DNS support: true
# - Enable DNS hostnames: true
variable "cidr_block" {
  description = "The CIDR block for the VPC"
  type        = string
}

variable "name_prefix" {
  description = "The prefix for naming resources"
  type        = string
  default = "myapp-dev"
}

resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true
  # Removed invalid attribute "vpc_id"
  tags = {
    Name = "${var.name_prefix}-vpc"
  }
}

