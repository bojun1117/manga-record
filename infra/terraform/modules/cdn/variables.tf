variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "app_port" {
  type = number
}

variable "origin_domain_name" {
  description = "後端 EC2 的 public DNS（反映目前綁定的 Elastic IP）"
  type        = string
}
