# modules are defined in the modules directory, and the main.tf file is used to call those modules and create the infrastructure. The variables.tf file is used to define any variables that are needed for the modules, and the outputs.tf file is used to define any outputs that are needed for the modules. The terraform.yml file is used to define the GitHub Actions workflow for Terraform.
# main.tf file for the Terraform configuration
# This file calls the modules to create the VPC, subnets, Internet Gateway, and route tables.
# Call the VPC module to create a VPC
module "vpc" {
  source = "./modules/vpc"
}   

module "subnets" {
  source = "./modules/subnets"
  name_prefix = var.name_prefix
  vpc_id = module.vpc.vpc_id
  availability_zone = var.availability_zone
  public_subnet_cidr = var.public_subnet_cidr
  private_subnet_cidr = var.private_subnet_cidr 
  
}

module "igw" {
  source = "./modules/IGW"
  vpc_id = module.vpc.vpc_id
  name_prefix = var.name_prefix
}

module "route_tables" {
  source = "./modules/routes-table"
  vpc_id = module.vpc.vpc_id
  name_prefix = var.name_prefix
  # public_subnet_ids attribute removed as it is not expected
  # private_subnet_id is not expected here and has been removed
}

module "name_prefix" {
  source = "./modules/name-prefix"
  name_prefix = var.name_prefix 
  
}