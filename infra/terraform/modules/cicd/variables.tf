variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "github_repo" {
  description = "GitHub repo，格式 owner/repo；只有這個 repo 的 main 分支能透過 OIDC 換到這個 role 的憑證"
  type        = string
}

variable "ecr_repository_arn" {
  type = string
}

variable "ec2_instance_arn" {
  type = string
}
