variable "ecr_repository_url" {
  description = "ECR repository URL (e.g., 12345678.dkr.ecr.us-east-1.amazonaws.com)"
  type        = string
  default     = "467392743157.dkr.ecr.us-west-2.amazonaws.com"
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "bedrock_model_id" {
  description = "Bedrock Model ID for LLM processing"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "bedrock_embedding_model" {
  description = "Bedrock Model ID for embedding generation"
  type        = string
  default     = "amazon.titan-embed-text-v1"
}

variable "email_address" {
  description = "Email address for SNS notifications"
  type        = string
}
