# Define lambda functions as a local variable to avoid repetition
locals {
  lambda_functions = [
    "llm_issue_handler",
    "doc_process", 
    "util",
    "sns_handler", 
    "pdf_ingest_handler", 
    "render_frontend", 
    "complete", 
    "presigned_url"
  ]
}

# Create ECR repositories for each Lambda function
resource "aws_ecr_repository" "lambda_repos" {
  for_each = toset(local.lambda_functions)
  
  name = each.key
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}

# Add permissions to each ECR repository
resource "aws_ecr_repository_policy" "lambda_repos_policy" {
  for_each = aws_ecr_repository.lambda_repos

  repository = each.value.name
  policy     = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "Statement1",
        Effect = "Allow",
        Principal = {
          AWS = [
            # Current account's root user (for deployment)
            "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root",
            "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/wsuser"
          ]
        },
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:CompleteLayerUpload",
          "ecr:GetDownloadUrlForLayer",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart"
        ]
      }
    ]
  })
}

# Create output for ECR repository URLs
output "ecr_repository_urls" {
  value = {
    for name, repo in aws_ecr_repository.lambda_repos : name => "${var.ecr_repository_url}/${repo.name}"
  }
  description = "The URLs of the created ECR repositories"
}