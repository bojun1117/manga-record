variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "db_master_username" {
  type = string
}

variable "db_name" {
  type = string
}

variable "db_host" {
  type = string
}

variable "db_port" {
  type = number
}

variable "db_master_password" {
  type      = string
  sensitive = true
}
