output "db_secret_id" {
  value = aws_secretsmanager_secret.db_credentials.id
}

output "db_secret_arn" {
  value = aws_secretsmanager_secret.db_credentials.arn
}

output "jwt_secret_id" {
  value = aws_secretsmanager_secret.jwt_secret.id
}

output "jwt_secret_arn" {
  value = aws_secretsmanager_secret.jwt_secret.arn
}
