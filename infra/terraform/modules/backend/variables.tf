variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "ec2_instance_type" {
  type = string
}

variable "app_port" {
  type = number
}

variable "public_subnet_id" {
  type = string
}

variable "security_group_id" {
  type = string
}

variable "ecr_repository_url" {
  type = string
}

variable "db_secret_id" {
  type = string
}

variable "db_secret_arn" {
  type = string
}

variable "jwt_secret_id" {
  type = string
}

variable "jwt_secret_arn" {
  type = string
}
