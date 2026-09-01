# EC2 security group(Phase 6)。後端 API 要能被外部打到,所以 app port 對 0.0.0.0/0 開放;
# 22 port 平常不開,維運走 SSM。只在 var.my_ip_cidr 有值時才臨時開 22 port 當備援
# (見下面 ec2_ssh_debug)——踩坑記錄見 ec2.tf。
resource "aws_security_group" "ec2" {
  name        = "${var.project_name}-${var.environment}-ec2-sg"
  description = "Allow public access to the backend API"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Backend API"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ec2-sg"
  }
}

# RDS security group。
#
# Phase 6 起只信任 EC2 的 security group,Phase 1-5 那條「允許本機 IP 直連」的暫時規則已經拿掉。
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Allow Postgres access to RDS"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Backend EC2"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-rds-sg"
  }
}

# 平常不開這個口。哪天真的需要用 psql 直連 RDS 除錯,在 terraform.tfvars 臨時填上
# my_ip_cidr 再 apply,用完拿掉再 apply 關掉——預設關閉,但保留這個逃生門。
resource "aws_security_group_rule" "rds_debug" {
  count = var.my_ip_cidr != null ? 1 : 0

  description       = "TEMPORARY debug access from developer IP"
  type              = "ingress"
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = [var.my_ip_cidr]
  security_group_id = aws_security_group.rds.id
}

# 同樣的逃生門模式,給 EC2 SSH 用(SSM/EC2 Instance Connect 連不上,見 ec2.tf 的踩坑記錄)。
resource "aws_security_group_rule" "ec2_ssh_debug" {
  count = var.my_ip_cidr != null ? 1 : 0

  description       = "TEMPORARY SSH debug access from developer IP"
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = [var.my_ip_cidr]
  security_group_id = aws_security_group.ec2.id
}
