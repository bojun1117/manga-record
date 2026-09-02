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
    ]
  }
}

resource "aws_iam_role_policy" "ec2_secrets_read" {
  name   = "${var.project_name}-${var.environment}-ec2-secrets-read"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.ec2_secrets_read.json
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project_name}-${var.environment}-ec2-profile"
  role = aws_iam_role.ec2.name
}

resource "aws_key_pair" "backend" {
  key_name   = "${var.project_name}-${var.environment}-ec2-key"
  public_key = file("${path.root}/ec2-ssh-key.pub")
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
  key_name               = aws_key_pair.backend.key_name

  user_data = templatefile("${path.module}/templates/user_data.sh.tpl", {
    region        = var.aws_region
    ecr_repo_url  = var.ecr_repository_url
    db_secret_id  = var.db_secret_id
    jwt_secret_id = var.jwt_secret_id
    app_port      = var.app_port
  })

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
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
