terraform {
  required_providers {
    random = {
      source = "hashicorp/random"
    }
  }
}

# 資料庫密碼。資料庫本身是 EC2 上的 Postgres 容器（infra/ec2/compose.yml），
# 密碼經 Secrets Manager 由 deploy.sh 讀取。
# 注意：這個資源若被重建會產生新密碼，但既有的 Postgres 不會跟著改 → 後端連不上。
resource "random_password" "db_master" {
  length  = 24
  special = false
}
