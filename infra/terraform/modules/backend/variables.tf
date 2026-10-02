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

variable "anthropic_secret_id" {
  type = string
}

variable "anthropic_secret_arn" {
  type = string
}

variable "db_backup_retention_days" {
  type    = number
  default = 14
}

variable "ec2_schedule_timezone" {
  type    = string
  default = "Asia/Taipei"
}

variable "ec2_stop_schedule" {
  description = "每天關機時間（EventBridge Scheduler cron，時區見 ec2_schedule_timezone）"
  type        = string
  default     = "cron(0 2 * * ? *)"
}

variable "ec2_start_schedule" {
  description = "每天開機時間（EventBridge Scheduler cron，時區見 ec2_schedule_timezone）"
  type        = string
  default     = "cron(0 16 * * ? *)"
}
