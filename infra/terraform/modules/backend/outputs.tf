output "instance_id" {
  value = aws_instance.backend.id
}

output "instance_arn" {
  value = aws_instance.backend.arn
}

output "public_ip" {
  value = aws_eip.backend.public_ip
}

# 用 EIP 的 DNS 而不是 instance 的：重建機器時 instance 剛建好的 public_dns 是 EIP 綁上前的臨時 IP，
# CloudFront origin 會指到失效位址
output "public_dns" {
  value = aws_eip.backend.public_dns
}

output "db_backup_bucket" {
  value = aws_s3_bucket.db_backups.bucket
}
