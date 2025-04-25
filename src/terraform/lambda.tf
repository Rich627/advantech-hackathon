################################################
####### LLM Advise Handler Lambda Function ######
################################################
resource "aws_lambda_function" "llm_advise_handler" {
  function_name = "analyze_with_llm"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/llm_advise_handler:latest"
  role          = aws_iam_role.lambda_exec.arn
  description   = "Analyze image with LLM by RAG"

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = aws_opensearchserverless_collection.vdb_collection.collection_endpoint
      BEDROCK_MODEL_ID = var.bedrock_model_id
    }
  }

  depends_on = [aws_opensearchserverless_security_policy.vdb_encryption_policy]
}


################################################
####### Document Processing Lambda Function ####
################################################
resource "aws_lambda_function" "doc_process" {
  function_name = "doc_process"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/doc_process:latest"
  role          = aws_iam_role.lambda_exec.arn
  description   = "Process equipment documents"
}

################################################
####### Utility Lambda Function ################
################################################
resource "aws_lambda_function" "util" {
  function_name = "equipment_utils"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/util:latest"
  role          = aws_iam_role.lambda_exec.arn
  description   = "Utility functions for equipment management"
}

################################################
####### SNS Notification Lambda Function #######
################################################
resource "aws_lambda_function" "sns_notfication" {
  function_name = "notify_employee"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/sns_notfication:latest"
  role          = aws_iam_role.lambda_exec.arn
  description   = "Notify employee via SNS"
  
  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.alert_topic.arn
    }
  }
}

################################################
### Ingest Embedding Data Lambda Function ######
################################################
resource "aws_lambda_function" "ingest_data" {
  function_name = "ingest_daily_report"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/ingest_data:latest"
  role          = aws_iam_role.lambda_exec.arn
  description   = "Ingest daily report to OpenSearch Serverless"

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = aws_opensearchserverless_collection.vdb_collection.collection_endpoint
      BEDROCK_EMBEDDING_MODEL = var.bedrock_embedding_model
      OPENSEARCH_REGION = var.aws_region
    }
  }
}


###############################################
####### Render Frontend Lambda Function #######
###############################################
resource "aws_lambda_function" "render_frontend" {
  function_name = "render_frontend"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/render_frontend:latest"
  role          = aws_iam_role.lambda_exec.arn
  description   = "Render frontend for equipment management"
}

################################################
##### Complete Processing Lambda Function ######
################################################
resource "aws_lambda_function" "complete" {
  function_name = "complete_process"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/complete:latest"
  role          = aws_iam_role.lambda_exec.arn
  description   = "Complete processing workflow"
}

################################################
####### Presigned URL Lambda Function ###########
################################################
resource "aws_lambda_function" "presigned_url" {
  function_name = "presigned_url_generator"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/presigned_url:latest"
  role          = aws_iam_role.lambda_exec.arn
  description   = "Generate presigned URLs for S3 uploads"
  
  environment {
    variables = {
      IMAGE_BUCKET_NAME = aws_s3_bucket.image_bucket.bucket
    }
  }
}
