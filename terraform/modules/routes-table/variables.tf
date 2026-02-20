# routes-table module variables
variable "vpc_id" {
  description = "The ID of the VPC to create the route tables in"
  type        = string
}

variable "public_subnet_id" {
  description = "The ID of the public subnet to associate with the public route table"
  type        = string
}

variable "private_subnet_id" {
  description = "The ID of the private subnet to associate with the private route table"
  type        = string
}

variable "igw_id" {
  description = "The ID of the Internet Gateway to attach to the public route table"
  type        = string
}                               