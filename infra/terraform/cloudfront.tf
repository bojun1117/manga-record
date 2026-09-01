# Phase 7：CloudFront 加 HTTPS。
#
# 後端在 EC2 上是裸 HTTP(app_port,見 ec2.tf/security_group.tf)。GitHub Pages 之類的
# HTTPS 網頁沒辦法直接呼叫它(mixed content，瀏覽器會擋)，且純 HTTP 本身也不安全。
#
# 沒有自己的網域名稱，所以不走「EC2 裝 Nginx + certbot 簽憑證」那條路，改用 CloudFront
# 免費附贈的 *.cloudfront.net 網址 —— 那個網址自帶合法憑證(viewer_certificate 用
# cloudfront_default_certificate)，不用管憑證續期，個人用量幾乎落在免費額度內。
#
# 這是純轉發，不是拿來加速靜態內容:後端是動態 API，快取整個關掉
# (cache_policy_id = AWS Managed-CachingDisabled)，Authorization/Cookie 等 header
# 原封不動轉給後端(origin_request_policy_id = AWS Managed-AllViewerExceptHostHeader ——
# 特地選「排除 Host header」這個版本，因為 CloudFront 轉發給 custom origin 時,如果把
# viewer 原本的 Host header 也轉過去,uvicorn/FastAPI 那端可能不認得，改用 CloudFront
# 自己算出的 origin host 比較不會出問題)。
#
# EC2↔CloudFront 這段(origin_protocol_policy = "http-only")還是明文，但這段是 AWS 內網，
# 使用者的瀏覽器只會跟 CloudFront 的 HTTPS 端點對話，實際暴露在公開網路上的都是加密的。
resource "aws_cloudfront_distribution" "backend" {
  enabled = true
  comment = "${var.project_name}-${var.environment} backend HTTPS proxy"

  # apply 時不卡著等 CDN 全球節點部署完(通常要 15-20 分鐘)，網址馬上就知道，
  # 但實際能連通前可能還要等一小段時間。
  wait_for_deployment = false

  origin {
    # 用 EC2 的 public DNS(反映目前綁定的 Elastic IP)而不是裸 IP 字串，
    # 是 CloudFront custom origin 官方建議的寫法。
    domain_name = aws_instance.backend.public_dns
    origin_id   = "backend-ec2"

    custom_origin_config {
      http_port                = var.app_port
      https_port                = 443
      origin_protocol_policy    = "http-only"
      origin_ssl_protocols      = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods         = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    target_origin_id         = "backend-ec2"
    viewer_protocol_policy   = "redirect-to-https"

    cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # AWS Managed-CachingDisabled
    origin_request_policy_id = "b689b0a8-53d0-40ab-baf2-68738e2966ac" # AWS Managed-AllViewerExceptHostHeader
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-cf"
  }
}
