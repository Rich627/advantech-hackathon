resource "aws_s3_bucket" "image_bucket" {
  bucket = "${var.bucket_name}-${random_string.bucket_suffix.result}"
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.image_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.llm_issue_handler.arn
    events             = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

resource "aws_s3_bucket_notification" "pdf_trigger" {
  bucket = aws_s3_bucket.image_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.pdf_ingest.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".pdf"
  }

  depends_on = [aws_lambda_permission.allow_s3_pdf]
}

resource "aws_lambda_permission" "allow_s3_pdf" {
  statement_id  = "AllowExecutionFromS3PDF"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pdf_ingest.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.image_bucket.arn
}

resource "aws_lambda_function" "llm_issue_handler" {
  function_name = "analyze_with_llm"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/llm_issue_handler:latest"
  role          = aws_iam_role.lambda_exec.arn
  description   = "Analyze image with LLM by RAG"

  # 移除 VPC 配置
  # vpc_config {
  #   subnet_ids         = [aws_subnet.private_subnet_1.id, aws_subnet.private_subnet_2.id]
  #   security_group_ids = [aws_security_group.lambda_sg.id]
  # }
  
  environment {
    variables = {
      OPENSEARCH_ENDPOINT = aws_opensearchserverless_collection.vdb_collection.collection_endpoint
      BEDROCK_MODEL_ID = var.bedrock_model_id
    }
  }

  depends_on = [aws_opensearchserverless_security_policy.vdb_encryption_policy]
}

resource "aws_lambda_function" "sns_handler" {
  function_name = "notify_employee"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/sns_handler:latest"
  role          = aws_iam_role.lambda_exec.arn
  description   = "Notify employee via SNS"
  
  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.alert_topic.arn
    }
  }
}

resource "aws_lambda_function" "daily_report_handler" {
  function_name = "ingest_daily_report"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/daily_report_handler:latest"
  role          = aws_iam_role.lambda_exec.arn
  description   = "Ingest daily report to OpenSearch Serverless"
  
  # 移除 VPC 配置
  # vpc_config {
  #   subnet_ids         = [aws_subnet.private_subnet_1.id, aws_subnet.private_subnet_2.id]
  #   security_group_ids = [aws_security_group.lambda_sg.id]
  # }

  environment {
    variables = {
      OPENSEARCH_ENDPOINT = aws_opensearchserverless_collection.vdb_collection.collection_endpoint
      BEDROCK_EMBEDDING_MODEL = var.bedrock_embedding_model
      OPENSEARCH_REGION = var.aws_region
    }
  }
}

resource "aws_lambda_function" "pdf_ingest" {
  function_name = "pdf_ingest_handler"
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}/pdf_ingest_handler:latest"
  role          = aws_iam_role.lambda_exec.arn   # 使用共用執行角色
  timeout       = 60
  memory_size   = 1024

  environment {
    variables = {
      OS_ENDPOINT = aws_opensearchserverless_collection.vdb_collection.collection_endpoint
      AWS_REGION  = var.aws_region
    }
  }

  # 如果 OpenSearch Serverless 在 VPC Subnet，這裡再補 vpc_config
}

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
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_s3_access" {
  name = "lambda_s3_access"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ],
        Resource = [
          aws_s3_bucket.image_bucket.arn,
          "${aws_s3_bucket.image_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_s3_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_s3_access.arn
}

resource "aws_iam_policy" "lambda_sns_publish" {
  name = "lambda_sns_publish"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["sns:Publish"],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sns_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_sns_publish.arn
}

resource "aws_iam_policy" "lambda_bedrock_access" {
  name = "lambda_bedrock_access"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "bedrock:InvokeModel"
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

resource "aws_iam_policy" "lambda_lambda_invoke" {
  name = "lambda_lambda_invoke"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "lambda:InvokeFunction"
        ],
        Resource = [
          aws_lambda_function.sns_handler.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_lambda_invoke_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_lambda_invoke.arn
}

resource "aws_sns_topic" "alert_topic" {
  name = "equipment_alert_topic"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.alert_topic.arn
  protocol  = "email"
  endpoint  = var.email_address
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.llm_issue_handler.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.image_bucket.arn
}

resource "aws_lambda_permission" "allow_s3_pdf" {
  statement_id  = "AllowExecutionFromS3PDF"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pdf_ingest.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.image_bucket.arn
}

data "aws_caller_identity" "current" {}

# 先創建加密策略
resource "aws_opensearchserverless_security_policy" "vdb_encryption_policy" {
  name        = "icam-vdb-encryption"
  type        = "encryption"
  policy      = jsonencode({
    Rules = [{
      ResourceType = "collection",
      Resource = ["collection/icam-vectors"]
    }],
    AWSOwnedKey = true
  })
}

# 添加 OpenSearch Serverless 訪問策略
resource "aws_iam_policy" "lambda_opensearch_access" {
  name        = "lambda_opensearch_access"
  description = "Allow Lambda to access OpenSearch Serverless"
  
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "aoss:APIAccessAll",
          "aoss:DashboardsAccessAll",
          "aoss:BatchGetCollection",
          "aoss:CreateCollection",
          "aoss:GetAccessPolicy",
          "aoss:UpdateAccessPolicy",
          "aoss:CreateCollectionItems",
          "aoss:DeleteCollectionItems",
          "aoss:UpdateCollectionItems",
          "aoss:DescribeCollectionItems"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_opensearch_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_opensearch_access.arn
}

# 然後創建集合
resource "aws_opensearchserverless_collection" "vdb_collection" {
  name        = "icam-vectors"
  type        = "VECTORSEARCH"
  description = "向量知識庫 for ICAM 判斷"
  
  depends_on = [aws_opensearchserverless_security_policy.vdb_encryption_policy]
}

# 資料訪問策略
resource "aws_opensearchserverless_access_policy" "vdb_data_access_policy" {
  name        = "icam-vdb-data-access"
  type        = "data"
  policy      = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection",
          Resource    = ["collection/icam-vectors"],
          Permission  = ["aoss:CreateCollectionItems", "aoss:DeleteCollectionItems", "aoss:UpdateCollectionItems", "aoss:DescribeCollectionItems"]
        }
      ],
      Principal = [
        # 使用 Lambda 執行角色和根帳戶
        aws_iam_role.lambda_exec.arn,
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ]
    }
  ])

  depends_on = [aws_opensearchserverless_collection.vdb_collection]
}

# 網絡策略 - 允許公共訪問但限制為 Lambda 服務
resource "aws_opensearchserverless_security_policy" "vdb_network_policy" {
  name   = "icam-vdb-network"
  type   = "network"
  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection",
          Resource    = ["collection/icam-vectors"]
        }
      ],
      # 允許公共訪問，但只有通過其他策略有權限的服務/角色才能訪問
      AllowFromPublic = true
    }
  ])

  depends_on = [aws_opensearchserverless_collection.vdb_collection]
}