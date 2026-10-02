variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "public_subnet_cidrs" {
  type = list(string)
}

variable "availability_zones" {
  description = "public subnet 使用的 AZ"
  type        = list(string)
}

variable "app_port" {
  description = "後端 API port，EC2 security group 對外開這個 port"
  type        = number
}
