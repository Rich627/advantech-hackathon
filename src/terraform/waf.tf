resource "aws_wafv2_web_acl" "main" {
  provider = aws.waf
  name        = "equipment-management-waf"
  description = "WAF Web ACL for equipment management application"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  #################################
  ###### Rules settings ###########
  #################################

  # Rule to set custom header for API Gateway
  # Make sure gateway can be accessed only from CloudFront
  rule {
    name     = "RequireCustomHeader"
    priority = 4

    # If the request does not have the custom header, block it
    action {
        block {}
    }

    statement {
        # If the request does not match the custom header, block it
        not_statement {

            # Match the custom header "x-api-gateway-auth" with value "icam-540"
            statement {
                byte_match_statement {
                    field_to_match {
                        single_header {
                        name = "x-api-gateway-auth"
                        }
                    }
                    positional_constraint = "EXACTLY"
                    search_string         = "icam-540"
                    text_transformation {
                      priority = 0
                      type     = "NONE"
                    }
                }
            }
        }
    }

    visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "RequireCustomHeader"
        sampled_requests_enabled   = true
    }
}


  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "equipment-management-waf"
    sampled_requests_enabled   = true
  }

  tags = {
    Project     = "equipment-management"
  }
}