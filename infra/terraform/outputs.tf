output "vpc_id" {
  value = module.network.vpc_id
}

output "public_subnet_ids" {
  value = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.network.private_subnet_ids
}

output "db_endpoint" {
  description = "RDS 連線位址（不含 port）"
  value       = module.database.address
}

output "db_port" {
  value = module.database.port
}

output "db_secret_arn" {
  description = "Secrets Manager 裡 DB 連線資訊的 ARN"
  value       = module.secrets.db_secret_arn
}

output "jwt_secret_arn" {
  value = module.secrets.jwt_secret_arn
}

output "psql_connect_hint" {
  description = "驗收用：本機測試連線指令（密碼另外用 aws secretsmanager get-secret-value 拿）。RDS 預設不對外開放，這組指令只有在 my_ip_cidr 有臨時填值時才連得上"
  value       = "psql \"host=${module.database.address} port=${module.database.port} dbname=${var.db_name} user=${var.db_master_username} sslmode=require\""
}

output "ecr_repository_url" {
  description = "docker build/push 後端 image 的目標 repo"
  value       = module.ecr.repository_url
}

output "ec2_instance_id" {
  description = "SSM Session Manager 連線用的 instance id"
  value       = module.backend.instance_id
}

output "backend_public_ip" {
  description = "後端 API 的固定 public IP，走裸 HTTP，只用來 debug；正式串接請用 backend_https_url"
  value       = module.backend.public_ip
}

output "backend_https_url" {
  description = "後端 API 的 HTTPS 網址(透過 CloudFront)。前端 GitHub Pages 要接這個，不是裸 IP"
  value       = "https://${module.cdn.domain_name}"
}

output "github_actions_role_arn" {
  description = "填進 GitHub repo secret AWS_GITHUB_ACTIONS_ROLE_ARN（見 backend/README.md CI/CD 段落）"
  value       = module.cicd.role_arn
}
