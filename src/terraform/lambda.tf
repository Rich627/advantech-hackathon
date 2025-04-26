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


#######################################
######### Lambda role #################
#######################################

# For Lambda functions to access AWS services, we need to create an IAM role with the necessary permissions.
resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Effect = "Allow"
      Sid    = ""
    }]
  })

  tags = {
    Name = "lambda-exec-role"
    Project = "equipment-management"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# for invoke sns topic
resource "aws_iam_policy" "lambda_sns_publish" {
  name        = "lambda_sns_publish"
  description = "Allow Lambda functions to publish messages to SNS"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "sns:Publish",
          "sns:Subscribe",
          "sns:ListSubscriptionsByTopic"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sns_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_sns_publish.arn
}

# for invoke bedrock
resource "aws_iam_policy" "lambda_bedrock_access" {
  name        = "lambda_bedrock_access"
  description = "Allow Lambda functions to access Bedrock models"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:GetModelCustomizationJob",
          "bedrock:CreateModelCustomizationJob"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_bedrock_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_bedrock_access.arn
}

# for invoke lambda
resource "aws_iam_policy" "lambda_invoke_policy" {
  name        = "lambda_invoke_policy"
  description = "Allow Lambda functions to invoke each other"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "lambda:InvokeFunction",
          "lambda:InvokeAsync"
        ],
        Resource = [
          aws_lambda_function.llm_advise_handler.arn,
          aws_lambda_function.doc_process.arn,
          aws_lambda_function.util.arn,
          aws_lambda_function.sns_notfication.arn,
          aws_lambda_function.ingest_data.arn,
          aws_lambda_function.render_frontend.arn,
          aws_lambda_function.complete.arn,
          aws_lambda_function.presigned_url.arn
        ]
      }
    ]
  })

  depends_on = [
    aws_lambda_function.llm_advise_handler,
    aws_lambda_function.doc_process,
    aws_lambda_function.util,
    aws_lambda_function.sns_notfication,
    aws_lambda_function.ingest_data,
    aws_lambda_function.render_frontend,
    aws_lambda_function.complete,
    aws_lambda_function.presigned_url
  ]
}

resource "aws_iam_role_policy_attachment" "lambda_invoke_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_invoke_policy.arn
}

# for cloudwatch logs
resource "aws_iam_role_policy_attachment" "lambda_logs_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}