variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "本地 AWS CLI profile 名稱，terraform apply 時用這組憑證"
  type        = string
  default     = "terraform-deploy"
}

variable "project_name" {
  description = "資源命名前綴"
  type        = string
  default     = "manga-record"
}

variable "environment" {
  description = "部署環境（dev/prod）"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDR，放 EC2(見 ec2.tf)"
  type        = list(string)
  default     = ["10.20.1.0/24", "10.20.2.0/24"]
}

variable "availability_zones" {
  description = "public subnet 使用的 AZ"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "db_name" {
  description = "PostgreSQL 資料庫名稱"
  type        = string
  default     = "manga_record"
}

variable "db_master_username" {
  description = "Postgres 帳號（EC2 上的 Postgres 容器與後端共用）"
  type        = string
  default     = "manga_record_admin"
}

variable "ec2_instance_type" {
  description = "跑後端 Docker container 的 EC2 instance type，個人專案用 free-tier 等級足夠"
  type        = string
  default     = "t3.micro"
}

variable "app_port" {
  description = "後端 FastAPI container 對外服務的 port，EC2 security group 和 docker run -p 都用這個值"
  type        = number
  default     = 8000
}

variable "github_repo" {
  description = "GitHub repo，格式 owner/repo；只有這個 repo 的 main 分支能透過 OIDC 換到 CI/CD role 的憑證"
  type        = string
  default     = "bojun1117/manga-record"
}

variable "anthropic_api_key" {
  description = "Anthropic API key，AI 助理功能用，存進 Secrets Manager；在 terraform.tfvars 填入真的值，不進版控"
  type        = string
  sensitive   = true
}
