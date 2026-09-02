terraform {
  required_providers {
    random = {
      source = "hashicorp/random"
    }
  }
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.project_name}/${var.environment}/db-credentials"
  description = "PostgreSQL master credentials for ${var.project_name} (${var.environment})"

  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_master_username
    password = var.db_master_password
    host     = var.db_host
    port     = var.db_port
    dbname   = var.db_name
  })
}

resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name        = "${var.project_name}/${var.environment}/jwt-secret"
  description = "JWT signing secret for ${var.project_name} (${var.environment})"

  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}
