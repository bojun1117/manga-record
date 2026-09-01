# GitHub Actions CI/CD 用的身份。用 OIDC 讓 workflow 執行當下臨時換一組短效 AWS 憑證，
# 不用把長期 access key 放進 GitHub secrets（外流風險比短效 token 高很多）。
#
# 換到的憑證只能做兩件事(見下面兩個 policy)：
#   1. push image 到 backend 這個 ECR repo
#   2. 對 backend 這台 EC2 送 SSM SendCommand，觸發 /opt/manga-record/deploy.sh
# 換憑證的信任範圍鎖在 var.github_repo 這個 repo 的 main 分支，其他 repo/分支換不到。

variable "github_repo" {
  description = "GitHub repo，格式 owner/repo；只有這個 repo 的 main 分支能透過 OIDC 換到下面這個 role 的憑證"
  type        = string
  default     = "bojun1117/manga-record"
}

# GitHub 的 OIDC provider thumbprint 用 data source 動態抓，不手動寫死
# （AWS 現在其實已經不靠 thumbprint 驗證知名 IdP，但 aws_iam_openid_connect_provider
# 這個 resource 仍然要求填這個欄位）。
data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github.certificates[0].sha1_fingerprint]
}

data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # 限定 main 分支的 workflow run(push 或 workflow_dispatch 都算 ref: refs/heads/main)。
    # PR 之類的其他 ref 換不到這組憑證。
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "${var.project_name}-${var.environment}-github-actions"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json
}

# ECR：只給 push 到這一個 backend repo 需要的 action，鎖 resource 到這個 repo 的 ARN。
# GetAuthorizationToken 例外——這個 action 本來就不支援 resource-level 限制，只能用 "*"。
data "aws_iam_policy_document" "github_actions_ecr" {
  statement {
    sid       = "GetAuthToken"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "PushToBackendRepo"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
    ]
    resources = [aws_ecr_repository.backend.arn]
  }
}

resource "aws_iam_role_policy" "github_actions_ecr" {
  name   = "${var.project_name}-${var.environment}-github-actions-ecr"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_ecr.json
}

# SSM：只能對 backend 這台 instance 送 AWS-RunShellScript 這個 document。
# GetCommandInvocation 用來讓 workflow 輪詢部署結果、印出 log——command id 是每次動態產生的，
# 這個 action 不支援用 resource 限制到單一 command，只能開 "*"（讀取範圍本來就只有這個帳號能查）。
data "aws_iam_policy_document" "github_actions_ssm" {
  statement {
    sid     = "SendCommand"
    actions = ["ssm:SendCommand"]
    resources = [
      aws_instance.backend.arn,
      "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript",
    ]
  }

  statement {
    sid       = "ReadCommandResult"
    actions   = ["ssm:GetCommandInvocation"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_actions_ssm" {
  name   = "${var.project_name}-${var.environment}-github-actions-ssm"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_ssm.json
}

output "github_actions_role_arn" {
  description = "填進 GitHub repo secret AWS_GITHUB_ACTIONS_ROLE_ARN（見 backend/README.md CI/CD 段落）"
  value       = aws_iam_role.github_actions.arn
}
