output "api_gateway_url" {
  value = aws_apigatewayv2_api.main.api_endpoint
}

output "image_bucket_name" {
  description = "Name of the S3 bucket for images"
  value       = aws_s3_bucket.image_bucket.bucket
}

output "history_bucket_name" {
  description = "Name of the S3 bucket for history reports"
  value       = aws_s3_bucket.history_report_bucket.bucket
}

output "opensearch_endpoint" {
  description = "Endpoint of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.vdb_collection.collection_endpoint
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "waf_web_acl_id" {
  description = "WAF Web ACL ID"
  value       = aws_wafv2_web_acl.main.id
}

output "website_url" {
  description = "Website URL"
  value       = "https://${var.domain_name}"
}