#!/bin/bash

# 設置變數
AWS_REGION=$(aws configure get region)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# 函數列表
LAMBDAS=("render_frontend" "complete" "doc_process")

# 建立並推送 Docker 映像
for lambda in "${LAMBDAS[@]}"; do
  echo "===== 處理 $lambda ====="
  
  # 進入函數目錄
  cd "$(dirname "$0")/$lambda" || { echo "無法進入 $lambda 目錄"; exit 1; }
  
  # 建立映像
  echo "建立 $lambda 映像..."
  docker build -t "$lambda:latest" .
  
  # 標記映像
  echo "標記 $lambda 映像..."
  docker tag "$lambda:latest" "$ECR_REPOSITORY/$lambda:latest"
  
  # 登入 ECR
  echo "登入 ECR..."
  aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REPOSITORY"
  
  # 檢查存儲庫是否存在，如果不存在則創建
  echo "檢查 ECR 存儲庫..."
  if ! aws ecr describe-repositories --repository-names "$lambda" --region "$AWS_REGION" > /dev/null 2>&1; then
    echo "創建 ECR 存儲庫 $lambda..."
    aws ecr create-repository --repository-name "$lambda" --region "$AWS_REGION"
  fi
  
  # 推送映像
  echo "推送 $lambda 映像到 ECR..."
  docker push "$ECR_REPOSITORY/$lambda:latest"
  
  # 返回原目錄
  cd - > /dev/null
  
  echo "===== $lambda 完成 ====="
done

echo "所有 Lambda 函數映像已建立並推送到 ECR"
echo "現在可以運行 terraform apply 來部署基礎設施" 