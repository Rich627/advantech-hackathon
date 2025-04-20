#!/bin/bash

# 設定 AWS 帳號和區域信息
AWS_ACCOUNT_ID="429555954826"
AWS_REGION="us-east-1"
ECR_REPO_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# 確保已登入 ECR
aws ecr get-login-password --region $AWS_REGION | sudo docker login --username AWS --password-stdin $ECR_REPO_URL

# 獲取腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Script running from: $SCRIPT_DIR"

# 建立並推送每個 Lambda 函數
LAMBDA_DIRS=("daily_report_handler" "llm_issue_handler" "sns_handler")

for DIR in "${LAMBDA_DIRS[@]}"; do
    echo "Processing $DIR..."
    
    # 切換到函數目錄
    cd "$SCRIPT_DIR/$DIR" || { echo "Directory $DIR not found!"; continue; }
    
    # 使用 sudo 運行 Docker 命令
    echo "Building Docker image for $DIR..."
    sudo docker build -t $DIR .
    
    echo "Tagging Docker image for $DIR..."
    sudo docker tag $DIR:latest $ECR_REPO_URL/$DIR:latest
    
    echo "Pushing Docker image for $DIR..."
    sudo docker push $ECR_REPO_URL/$DIR:latest
    
    # 返回腳本目錄
    cd "$SCRIPT_DIR"
    echo "$DIR processed successfully"
done

echo "All Lambda functions built and pushed successfully"