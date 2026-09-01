# AWS Secrets Manager：DB 連線資訊 + JWT signing secret。
# Backend（FastAPI/EC2）之後用 IAM instance profile 權限讀取，不寫死在程式碼或 Terraform 檔案裡。

resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.project_name}/${var.environment}/db-credentials"
  description = "PostgreSQL master credentials for ${var.project_name} (${var.environment})"

  # 個人開發環境：destroy 後要能馬上用同名字重建，不需要 AWS 預設的 30 天緩衝期。
  # 正式環境不建議設 0（誤刪就真的沒機會救回來了）。
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_master_username
    password = random_password.db_master.result
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
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

  recovery_window_in_days = 0 # 同上，開發環境不需要緩衝期
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}
