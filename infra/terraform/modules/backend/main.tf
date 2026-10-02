data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2" {
  name               = "${var.project_name}-${var.environment}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ec2_ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "ec2_ecr_read" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

data "aws_iam_policy_document" "ec2_secrets_read" {
  statement {
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      var.db_secret_arn,
      var.jwt_secret_arn,
      var.anthropic_secret_arn,
    ]
  }
}

resource "aws_iam_role_policy" "ec2_secrets_read" {
  name   = "${var.project_name}-${var.environment}-ec2-secrets-read"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.ec2_secrets_read.json
}

data "aws_caller_identity" "current" {}

# 資料庫每日備份（EC2 上的 cron 跑 pg_dump 上傳到這裡），超過 14 天自動刪除
resource "aws_s3_bucket" "db_backups" {
  bucket = "${var.project_name}-${var.environment}-db-backups-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-${var.environment}-db-backups"
  }
}

resource "aws_s3_bucket_public_access_block" "db_backups" {
  bucket = aws_s3_bucket.db_backups.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "db_backups" {
  bucket = aws_s3_bucket.db_backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "db_backups" {
  bucket = aws_s3_bucket.db_backups.id

  rule {
    id     = "expire-old-backups"
    status = "Enabled"

    filter {}

    expiration {
      days = var.db_backup_retention_days
    }
  }
}

data "aws_iam_policy_document" "ec2_db_backups" {
  statement {
    actions   = ["s3:PutObject", "s3:GetObject"]
    resources = ["${aws_s3_bucket.db_backups.arn}/*"]
  }

  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.db_backups.arn]
  }
}

resource "aws_iam_role_policy" "ec2_db_backups" {
  name   = "${var.project_name}-${var.environment}-ec2-db-backups"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.ec2_db_backups.json
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project_name}-${var.environment}-ec2-profile"
  role = aws_iam_role.ec2.name
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "backend" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.ec2_instance_type
  subnet_id              = var.public_subnet_id
  vpc_security_group_ids = [var.security_group_id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  user_data = templatefile("${path.module}/templates/user_data.sh.tpl", {
    region              = var.aws_region
    ecr_repo_url        = var.ecr_repository_url
    db_secret_id        = var.db_secret_id
    jwt_secret_id       = var.jwt_secret_id
    anthropic_secret_id = var.anthropic_secret_id
    app_port            = var.app_port
    backup_bucket       = aws_s3_bucket.db_backups.bucket
    setup_host_sh       = filebase64("${path.root}/../ec2/setup-host.sh")
    deploy_sh           = filebase64("${path.root}/../ec2/deploy.sh")
    backup_sh           = filebase64("${path.root}/../ec2/backup.sh")
    compose_yml         = filebase64("${path.root}/../ec2/compose.yml")
  })

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  # al2023 data source 每次都抓最新 AMI；AWS 發新版時不要因此重建機器（會中斷服務）。
  # user_data 只在第一次開機執行，改了也不會套用到既有機器，反而會觸發 stop/start，所以一併忽略。
  # key_name：現有機器建立時綁了舊的 SSH key pair（已移除，維運改走 Session Manager），
  # key_name 無法就地修改，不忽略的話會重建機器、連帶丟掉 root volume 上的 Postgres 資料。
  lifecycle {
    ignore_changes = [ami, user_data, key_name]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend"
  }
}

resource "aws_eip" "backend" {
  instance = aws_instance.backend.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-eip"
  }
}

# 夜間關機省錢：每天台灣時間 02:00 關機、16:00 開機（備份在關機前的 01:00，見 infra/ec2/setup-host.sh）
data "aws_iam_policy_document" "scheduler_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "${var.project_name}-${var.environment}-ec2-scheduler"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json
}

data "aws_iam_policy_document" "scheduler_start_stop" {
  statement {
    actions   = ["ec2:StartInstances", "ec2:StopInstances"]
    resources = [aws_instance.backend.arn]
  }
}

resource "aws_iam_role_policy" "scheduler_start_stop" {
  name   = "${var.project_name}-${var.environment}-ec2-start-stop"
  role   = aws_iam_role.scheduler.id
  policy = data.aws_iam_policy_document.scheduler_start_stop.json
}

resource "aws_scheduler_schedule" "ec2_stop" {
  name                         = "${var.project_name}-${var.environment}-ec2-stop"
  schedule_expression          = var.ec2_stop_schedule
  schedule_expression_timezone = var.ec2_schedule_timezone

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = "arn:aws:scheduler:::aws-sdk:ec2:stopInstances"
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ InstanceIds = [aws_instance.backend.id] })
  }
}

resource "aws_scheduler_schedule" "ec2_start" {
  name                         = "${var.project_name}-${var.environment}-ec2-start"
  schedule_expression          = var.ec2_start_schedule
  schedule_expression_timezone = var.ec2_schedule_timezone

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = "arn:aws:scheduler:::aws-sdk:ec2:startInstances"
    role_arn = aws_iam_role.scheduler.arn
    input    = jsonencode({ InstanceIds = [aws_instance.backend.id] })
  }
}
