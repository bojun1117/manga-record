terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # 個人專案先用本機 state（terraform.tfstate 留在這個資料夾）。
  # 之後如果想要更安全的做法（state 存 S3 + DynamoDB lock），
  # 這裡改成 backend "s3" 區塊即可，不影響其他檔案。
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
