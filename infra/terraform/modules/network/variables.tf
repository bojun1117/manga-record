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

variable "private_subnet_cidrs" {
  type = list(string)
}

variable "availability_zones" {
  description = "RDS DB subnet group 至少要橫跨 2 個 AZ 才能建立（即使 instance 本身是單 AZ）"
  type        = list(string)
}

variable "app_port" {
  description = "後端 API port，EC2 security group 對外開這個 port"
  type        = number
}

variable "my_ip_cidr" {
  description = "本機公網 IP（CIDR），用來臨時開放 RDS/EC2 SSH 直連除錯。留空（null）就跟平常一樣不開放"
  type        = string
  default     = null
}
