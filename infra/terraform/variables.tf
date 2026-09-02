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

variable "private_subnet_cidrs" {
  description = "Private subnet CIDR，放 RDS，關閉對外連線"
  type        = list(string)
  default     = ["10.20.11.0/24", "10.20.12.0/24"]
}

variable "availability_zones" {
  description = "使用的 AZ；RDS DB subnet group 至少要橫跨 2 個 AZ 才能建立（即使 instance 本身是單 AZ）"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "db_name" {
  description = "PostgreSQL 資料庫名稱"
  type        = string
  default     = "manga_record"
}

variable "db_master_username" {
  description = "RDS master 帳號（應用程式本身之後會用另一組權限較小的帳號，這組只給 migration/管理用）"
  type        = string
  default     = "manga_record_admin"
}

variable "db_instance_class" {
  description = "RDS instance class，個人專案用最小規格"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_engine_version" {
  description = "PostgreSQL 版本；apply 前建議用 `aws rds describe-db-engine-versions --engine postgres --region <region>` 確認這個版本在你的 region 還可用"
  type        = string
  default     = "16.4"
}

variable "my_ip_cidr" {
  description = <<-EOT
    你本機的公網 IP（CIDR 格式，例如 "1.2.3.4/32"），用來臨時允許本機直連 RDS 除錯。
    查詢方式：終端機跑 `curl -s https://checkip.amazonaws.com`，拿到的 IP 後面加上 /32。

    Phase 6 起預設留空（null）——RDS 平常只信任 EC2 的 security group，不對外開放。
    只有真的需要用 psql 直連除錯時才臨時填這個值、apply，用完再清空、apply 關掉
    （見 security_group.tf 的 aws_security_group_rule.rds_debug）。
  EOT
  type        = string
  default     = null
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
