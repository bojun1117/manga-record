# RDS PostgreSQL。
#
# Phase 6 起收緊：放在 private subnet、關掉 publicly_accessible,只有 EC2(見 ec2.tf)
# 能透過 security_group.tf 的 aws_security_group.rds 連進來。
#
# ⚠️ 這個 instance 是 Phase 6 重新建的(踩過一個 AWS 的坑寫在下面),Phase 1-5 期間累積的
# 測試資料(手動 insert 的那筆、前端測試註冊的帳號/收藏)已經清空,是全新的空資料庫,
# 需要重新跑一次 migration(alembic upgrade head,deploy.sh 會自動做這件事)。
#
# 踩坑記錄:AWS RDS 不支援把一個已存在的 instance 從一個 subnet group 直接換到「同一個
# VPC 裡的另一個」subnet group——ModifyDBInstance 的 db_subnet_group_name 參數只能用在
# 跨 VPC 搬遷,同 VPC 內換 group 一律回 InvalidVPCNetworkStateFault("choose a subnet group
# in a different VPC"),這是 AWS API 本身的限制,不是 Terraform 或設定寫錯
# (見 https://github.com/hashicorp/terraform-provider-aws/issues/512)。
# 因為這是個人專案的 dev 資料庫、資料本來就是測試用,選擇直接砍掉重建成在 private
# subnet 的新 instance,而不是做 snapshot + restore 到新 instance 保留資料。

resource "random_password" "db_master" {
  length  = 24
  special = false # 避免特殊字元在連線字串裡需要額外跳脫，个人專案不需要那麼複雜
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-${var.environment}-db"
  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 50 # storage autoscaling 上限，避免手動調整
  storage_type          = "gp3"

  db_name  = var.db_name
  username = var.db_master_username
  password = random_password.db_master.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  publicly_accessible = false
  apply_immediately   = true # 安全性相關設定,不想排到下次 maintenance window 才生效

  multi_az                = false # 個人專案不需要高可用，省錢
  backup_retention_period = 1
  skip_final_snapshot     = true # 開發環境接受銷毀時不留 snapshot；正式環境不建議這樣設
  deletion_protection     = false

  tags = {
    Name = "${var.project_name}-${var.environment}-db"
  }
}
