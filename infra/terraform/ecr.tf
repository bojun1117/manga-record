# ECR repo 放後端 Docker image。build/push 是手動流程(見 backend/README.md 的 Phase 6 段落),
# 這裡只建 repo 本身。

resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-${var.environment}-backend"
  image_tag_mutability = "MUTABLE" # 個人專案沿用 :latest 覆蓋式部署,不強制 immutable tag

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend"
  }
}

# deploy.sh 每次都 push 覆蓋同一個 :latest tag,所以「舊版」不會留著舊 tag,
# 而是變成 untagged image(tag 被新的一次 push 搶走)。這裡只要清掉這些 untagged
# 的殘留,避免佔儲存空間;不需要「保留最近 N 個 tag」這種規則,因為本來就只有一個 tag。
resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "expire untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      }
    ]
  })
}
