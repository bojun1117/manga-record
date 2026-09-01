output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "db_endpoint" {
  description = "RDS 連線位址（不含 port）"
  value       = aws_db_instance.main.address
}

output "db_port" {
  value = aws_db_instance.main.port
}

output "db_secret_arn" {
  description = "Secrets Manager 裡 DB 連線資訊的 ARN"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "jwt_secret_arn" {
  value = aws_secretsmanager_secret.jwt_secret.arn
}

output "psql_connect_hint" {
  description = "驗收用：本機測試連線指令（密碼另外用 aws secretsmanager get-secret-value 拿）。Phase 6 起 RDS 預設不對外開放，這組指令只有在 my_ip_cidr 有臨時填值時才連得上"
  value       = "psql \"host=${aws_db_instance.main.address} port=${aws_db_instance.main.port} dbname=${var.db_name} user=${var.db_master_username} sslmode=require\""
}

output "ecr_repository_url" {
  description = "docker build/push 後端 image 的目標 repo"
  value       = aws_ecr_repository.backend.repository_url
}

output "ec2_instance_id" {
  description = "SSM Session Manager 連線用的 instance id"
  value       = aws_instance.backend.id
}

output "backend_public_ip" {
  description = "後端 API 的固定 public IP，走裸 HTTP，只用來 debug；正式串接請用 backend_https_url"
  value       = aws_eip.backend.public_ip
}

output "backend_https_url" {
  description = "後端 API 的 HTTPS 網址(透過 CloudFront)。前端 GitHub Pages 要接這個，不是裸 IP"
  value       = "https://${aws_cloudfront_distribution.backend.domain_name}"
}
