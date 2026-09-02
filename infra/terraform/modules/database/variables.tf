variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "db_name" {
  type = string
}

variable "db_master_username" {
  description = "RDS master 帳號（應用程式本身之後會用另一組權限較小的帳號，這組只給 migration/管理用）"
  type        = string
}

variable "db_instance_class" {
  type = string
}

variable "db_engine_version" {
  description = "PostgreSQL 版本；apply 前建議用 `aws rds describe-db-engine-versions --engine postgres --region <region>` 確認這個版本在你的 region 還可用"
  type        = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "rds_security_group_id" {
  type = string
}
