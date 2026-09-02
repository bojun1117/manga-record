resource "aws_cloudfront_distribution" "backend" {
  enabled = true
  comment = "${var.project_name}-${var.environment} backend HTTPS proxy"

  wait_for_deployment = false

  origin {
    domain_name = var.origin_domain_name
    origin_id   = "backend-ec2"

    custom_origin_config {
      http_port              = var.app_port
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "backend-ec2"
    viewer_protocol_policy = "redirect-to-https"

    cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    origin_request_policy_id = "b689b0a8-53d0-40ab-baf2-68738e2966ac"
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
