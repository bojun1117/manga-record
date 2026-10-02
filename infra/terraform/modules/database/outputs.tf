output "master_password" {
  value     = random_password.db_master.result
  sensitive = true
}
