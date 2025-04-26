# 建立所有需要的 ECR 儲存庫
resource "aws_ecr_repository" "lambda_repos" {
  for_each = toset([
    "llm_advise_handler",
    "doc_process",
    "util",
    "sns_notfication",
    "ingest_data",
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

# 自動化建置和推送 Docker 映像的邏輯
resource "null_resource" "docker_build_push" {
  for_each = toset([
    "llm_advise_handler",
    "doc_process", 
    "util",
    "sns_handler", 
    "pdf_ingest_data", 
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
      # 取得 ECR 登入令牌並登入
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.ecr_repository_url}
      
      # 切換到 Lambda 函數的目錄
      cd ../lambda/${each.key}
      
      # 建置 Docker 映像
      docker build -t ${each.key}:latest .
      
      # 標記映像
      docker tag ${each.key}:latest ${var.ecr_repository_url}/${each.key}:latest
      
      # 推送到 ECR
      docker push ${var.ecr_repository_url}/${each.key}:latest
      
      echo "Successfully built and pushed ${each.key} image to ECR"
    EOT
  }
}
