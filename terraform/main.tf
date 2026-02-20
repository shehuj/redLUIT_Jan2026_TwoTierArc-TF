# modules are defined in the modules directory, and the main.tf file is used to call those modules and create the infrastructure. The variables.tf file is used to define any variables that are needed for the modules, and the outputs.tf file is used to define any outputs that are needed for the modules. The terraform.yml file is used to define the GitHub Actions workflow for Terraform.
# main.tf file for the Terraform configuration
# This file calls the modules to create the VPC, subnets, Internet Gateway, and route tables.
# Call the VPC module to create a VPC
module "vpc" {
  source = "./modules/vpc"
  name_prefix = var.name_prefix
  cidr_block = var.cidr_block
}

module "subnets" {
  source                = "./modules/subnets"
  name_prefix           = var.name_prefix
  vpc_id                = module.vpc.vpc_id
  availability_zone     = var.availability_zone
  availability_zone_2   = var.availability_zone_2
  public_subnet_cidr    = var.public_subnet_cidr
  private_subnet_cidr   = var.private_subnet_cidr
  public_subnet_cidr_2  = var.public_subnet_cidr_2
  private_subnet_cidr_2 = var.private_subnet_cidr_2
}

module "igw" {
  source      = "./modules/IGW"
  vpc_id      = module.vpc.vpc_id
  name_prefix = var.name_prefix
}

module "route_tables" {
  source              = "./modules/routes-table"
  vpc_id              = module.vpc.vpc_id
  name_prefix         = var.name_prefix
  public_subnet_id    = module.subnets.public_subnet_id
  private_subnet_id   = module.subnets.private_subnet_id
  public_subnet_id_2  = module.subnets.public_subnet_id_2
  private_subnet_id_2 = module.subnets.private_subnet_id_2
  igw_id              = module.igw.igw_id
}
