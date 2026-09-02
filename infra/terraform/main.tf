module "network" {
  source = "./modules/network"

  project_name         = var.project_name
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
  app_port             = var.app_port
  my_ip_cidr           = var.my_ip_cidr
}

module "database" {
  source = "./modules/database"

  project_name          = var.project_name
  environment           = var.environment
  db_name               = var.db_name
  db_master_username    = var.db_master_username
  db_instance_class     = var.db_instance_class
  db_engine_version     = var.db_engine_version
  private_subnet_ids    = module.network.private_subnet_ids
  rds_security_group_id = module.network.rds_security_group_id
}

module "secrets" {
  source = "./modules/secrets"

  project_name       = var.project_name
  environment        = var.environment
  db_master_username = var.db_master_username
  db_name            = var.db_name
  db_host            = module.database.address
  db_port            = module.database.port
  db_master_password = module.database.master_password
  anthropic_api_key  = var.anthropic_api_key
}

module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
  environment  = var.environment
}

module "backend" {
  source = "./modules/backend"

  project_name         = var.project_name
  environment          = var.environment
  aws_region           = var.aws_region
  ec2_instance_type    = var.ec2_instance_type
  app_port             = var.app_port
  public_subnet_id     = module.network.public_subnet_ids[0]
  security_group_id    = module.network.ec2_security_group_id
  ecr_repository_url   = module.ecr.repository_url
  db_secret_id         = module.secrets.db_secret_id
  db_secret_arn        = module.secrets.db_secret_arn
  jwt_secret_id        = module.secrets.jwt_secret_id
  jwt_secret_arn       = module.secrets.jwt_secret_arn
  anthropic_secret_id  = module.secrets.anthropic_secret_id
  anthropic_secret_arn = module.secrets.anthropic_secret_arn
}

module "cicd" {
  source = "./modules/cicd"

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = var.aws_region
  github_repo        = var.github_repo
  ecr_repository_arn = module.ecr.repository_arn
  ec2_instance_arn   = module.backend.instance_arn
}

module "cdn" {
  source = "./modules/cdn"

  project_name       = var.project_name
  environment        = var.environment
  app_port           = var.app_port
  origin_domain_name = module.backend.public_dns
}
