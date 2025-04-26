resource "aws_ecr_repository" "lambda_repos" {
  for_each = toset([
    "llm_issue_handler",
    "doc_process", 
    "util",
    "sns_handler", 
    "pdf_ingest_handler", 
    "render_frontend", 
    "complete", 
    "presigned_url"
  ])
  
  name = each.key
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}

# 為每個 ECR 儲存庫添加權限
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
            # 當前帳戶的 root 使用者 (用於部署)
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

# 自動化建置和推送 Docker 映像的邏輯
resource "null_resource" "docker_build_push" {
  for_each = toset([
    "llm_issue_handler",
    "doc_process", 
    "util",
    "sns_handler", 
    "pdf_ingest_handler", 
    "render_frontend", 
    "complete", 
    "presigned_url"
  ])
  
  # 確保 ECR 儲存庫先被創建
  depends_on = [aws_ecr_repository.lambda_repos]
  
  # 每次這些檔案變更時重新執行
  triggers = {
    docker_file = filemd5("../lambda/${each.key}/Dockerfile")
    lambda_code = filemd5("../lambda/${each.key}/lambda_function.py")
    requirements = fileexists("../lambda/${each.key}/requirements.txt") ? filemd5("../lambda/${each.key}/requirements.txt") : "no-requirements"
  }

  # 執行 Docker 建置與推送的命令
  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
      $maxRetries = 3
      $retryCount = 0
      $success = $false
      
      while (-not $success -and $retryCount -lt $maxRetries) {
        try {
          # 取得 ECR 登入令牌並登入
          Write-Host "Logging in to ECR (Attempt $($retryCount + 1)/$maxRetries)..."
          aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.ecr_repository_url}
          
          # 切換到 Lambda 函數的目錄
          $lambdaPath = Resolve-Path -Path "../lambda/${each.key}"
          Write-Host "Changing to directory: $lambdaPath"
          cd $lambdaPath
          
          # 檢查是否有 requirements.txt，如果有則確保它存在
          if (Test-Path -Path "./requirements.txt") {
            Write-Host "requirements.txt found"
          } else {
            Write-Host "No requirements.txt found, creating empty file"
            "" | Out-File -FilePath "./requirements.txt" -Encoding utf8
          }
          
          # 建置 Docker 映像
          Write-Host "Building Docker image..."
          docker build -t ${each.key}:latest .
          
          # 標記映像
          Write-Host "Tagging image..."
          docker tag ${each.key}:latest ${var.ecr_repository_url}/${each.key}:latest
          
          # 推送到 ECR
          Write-Host "Pushing to ECR..."
          docker push ${var.ecr_repository_url}/${each.key}:latest
          
          Write-Host "Successfully built and pushed ${each.key} image to ECR"
          $success = $true
        }
        catch {
          $retryCount++
          Write-Host "Error occurred: $_"
          
          if ($retryCount -lt $maxRetries) {
            Write-Host "Retrying in 10 seconds..."
            Start-Sleep -Seconds 10
          }
          else {
            Write-Host "Maximum retries reached. Failing."
            throw
          }
        }
      }
    EOT
  }
}