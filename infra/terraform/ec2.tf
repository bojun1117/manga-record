# EC2 跑後端 Docker container。維運主要走 SSM Session Manager(見 iam.tf 掛的
# AmazonSSMManagedInstanceCore),平常不開 22 port、不用管理 SSH key。
#
# ⚠️ 踩坑記錄:一開始 SSM 連不上、EC2 Instance Connect 也連不上,一度以為是這個帳號/
# 環境本身的限制(AWS 官方 AWSSupport-TroubleshootManagedInstance 診斷跑過,網路/
# security group/NACL/IAM 全部 PASS)。後來用這裡的 SSH key pair 連進去查,才發現真正
# 原因很單純:這個 AMI 實際上**沒有預裝 amazon-ssm-agent**(跟一般認知的「AL2023 內建
# SSM Agent」不一樣),手動裝上去、啟用之後 SSM 立刻就正常連線。真正的修法在
# user_data.sh.tpl(裝 amazon-ssm-agent 那行的註解)。
#
# 這把 SSH key(ec2-ssh-key / ec2-ssh-key.pub,本機產生、.gitignore 排除、不進版控)留著
# 當 SSM 之外的備援連線管道。ingress 只在 var.my_ip_cidr 有值時才開(見 security_group.tf
# 的 aws_security_group_rule.ec2_ssh_debug),平常留空就跟只用 SSM 一樣不開 22 port。

resource "aws_key_pair" "backend" {
  key_name   = "${var.project_name}-${var.environment}-ec2-key"
  public_key = file("${path.module}/ec2-ssh-key.pub")
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
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name
  key_name               = aws_key_pair.backend.key_name

  user_data = templatefile("${path.module}/templates/user_data.sh.tpl", {
    region        = var.aws_region
    ecr_repo_url  = aws_ecr_repository.backend.repository_url
    db_secret_id  = aws_secretsmanager_secret.db_credentials.id
    jwt_secret_id = aws_secretsmanager_secret.jwt_secret.id
    app_port      = var.app_port
  })

  # 沒設這段時吃到 AMI 預設的極小根磁碟(實測只有 2GB),docker pull image 到一半就
  # no space left on device。20GB gp3 一個月大約多 $1.6,足夠跑 OS + docker + image。
  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend"
  }
}

# 固定 public IP,避免 instance 重啟後 IP 換掉(前端 .env 打的 URL 才不用一直換)。
resource "aws_eip" "backend" {
  instance = aws_instance.backend.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-eip"
  }
}
