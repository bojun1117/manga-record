output "role_arn" {
  description = "填進 GitHub repo secret AWS_GITHUB_ACTIONS_ROLE_ARN（見 backend/README.md CI/CD 段落）"
  value       = aws_iam_role.github_actions.arn
}
