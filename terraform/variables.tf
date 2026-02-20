 # variables for the VPC module
variable "name_prefix" {
  description = "The prefix for naming resources"
  type        = string
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default = "10.0.0.0/16"
}

# variable for the region
variable "region" {
  description = "The AWS region to create resources in"
  type        = string
}

# variable for the availability zone
variable "availability_zone" {
  description = "The availability zone for the subnets"
  type        = string
}

# variable for the public subnet CIDR block
variable "public_subnet_cidr" {
  description = "The CIDR block for the public subnet"
  type        = string
}

# variable for the private subnet CIDR block
variable "private_subnet_cidr" {
  description = "The CIDR block for the private subnet"
  type        = string
}   

# variable for the number of availability zones to use
variable "num_azs" {
  description = "The number of availability zones to use for the subnets"
  type        = number
  default     = 1
}   

# variable for the number of public subnets to create
variable "num_public_subnets" {
  description = "The number of public subnets to create"
  type        = number
  default     = 2
}

# variable for the number of private subnets to create
variable "num_private_subnets" {
  description = "The number of private subnets to create"
  type        = number
  default     = 2
}   

# variable for the number of route tables to create
variable "num_route_tables" {
  description = "The number of route tables to create"
  type        = number
  default     = 2
}

# variable for the number of Internet Gateways to create
variable "num_igws" {
  description = "The number of Internet Gateways to create"
  type        = number
  default     = 1
}   