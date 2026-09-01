# EC2 的 IAM role,讓 deploy.sh(跑在 instance 上)能:
#   1. 用 SSM Session Manager 被連進去(不用開 22 port、不用管理 SSH key)
#   2. pull ECR 上的 image
#   3. 讀 Secrets Manager 拿 DB 連線字串 / JWT secret

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

# 讀 secret 限定這兩個 ARN,不用萬用字元——比照 secrets.tf 已經在用的最小權限精神。
data "aws_iam_policy_document" "ec2_secrets_read" {
  statement {
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      aws_secretsmanager_secret.db_credentials.arn,
      aws_secretsmanager_secret.jwt_secret.arn,
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
