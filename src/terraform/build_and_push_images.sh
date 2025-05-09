#!/bin/bash

# 設置變數
AWS_REGION="us-west-2"
ECR_URL="467392743157.dkr.ecr.us-west-2.amazonaws.com"
LAMBDA_FUNCTIONS=(
  "analyze_with_llm"
  # "doc_process"
  # "util"
  # "sns_handler"
  # "pdf_ingest_handler"
  # "render_frontend"
  # "complete"
  # "presigned_url"
)

# 添加 Lambda 函數名稱到 ECR 儲存庫名稱的映射
declare -A ECR_REPO_MAPPING
ECR_REPO_MAPPING["analyze_with_llm"]="llm_issue_handler"
# 如有更多映射，請按照以下格式添加
# ECR_REPO_MAPPING["lambda_function_name"]="ecr_repo_name"

# 添加 Lambda 函數名稱到本地文件夾名稱的映射
declare -A FOLDER_MAPPING
FOLDER_MAPPING["analyze_with_llm"]="llm_issue_handler"
# 如有更多映射，請按照以下格式添加
# FOLDER_MAPPING["lambda_function_name"]="local_folder_name"

NO_RETRY=${NO_RETRY:-false}  # 新增: 控制是否禁用重試機制的環境變量

# 顯示使用方法
usage() {
  echo "用法: $0 [函數名稱]"
  echo "如果沒有提供函數名稱，將構建並推送所有 Lambda 函數"
  echo "可用的函數:"
  for func in "${LAMBDA_FUNCTIONS[@]}"; do
    echo "  - $func"
  done
  echo ""
  echo "環境變量:"
  echo "  NO_RETRY=true    禁用推送失敗時的重試機制"
  exit 1
}

# 構建和推送單個函數的 Docker 映像
build_and_push() {
  local function_name=$1
  
  # 獲取本地文件夾名稱，如果映射中存在則使用映射的名稱，否則使用函數名稱
  local folder_name=${FOLDER_MAPPING[$function_name]:-$function_name}
  local lambda_path="../lambda/$folder_name"
  
  # 獲取 ECR 儲存庫名稱，如果映射中存在則使用映射的名稱，否則使用函數名稱
  local ecr_repo_name=${ECR_REPO_MAPPING[$function_name]:-$function_name}
  
  echo "==== 處理 $function_name ===="
  echo "本地文件夾: $folder_name"
  echo "ECR 儲存庫名稱: $ecr_repo_name"
  
  # 檢查 Lambda 函數目錄是否存在
  if [ ! -d "$lambda_path" ]; then
    echo "錯誤: 目錄 $lambda_path 不存在"
    return 1
  fi
  
  # 切換到 Lambda 函數目錄
  cd "$lambda_path" || { echo "無法切換到目錄 $lambda_path"; return 1; }
  
  # 檢查 Dockerfile 是否存在
  if [ ! -f "./Dockerfile" ]; then
    echo "錯誤: 在 $lambda_path 中找不到 Dockerfile"
    return 1
  fi
  
  # 備份原始 Dockerfile
  cp Dockerfile Dockerfile.bak
  
  # 修改基礎映像以確保平台兼容性
  if grep -q "FROM public.ecr.aws/lambda/python" Dockerfile; then
    echo "更新基礎映像以確保平台兼容性..."
    echo "FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.9" > Dockerfile.new
    tail -n +2 Dockerfile >> Dockerfile.new
    mv Dockerfile.new Dockerfile
  elif grep -q "FROM amazon/aws-lambda-python" Dockerfile; then
    echo "更新 Amazon 基礎映像以確保平台兼容性..."
    echo "FROM --platform=linux/amd64 amazon/aws-lambda-python:3.9" > Dockerfile.new
    tail -n +2 Dockerfile >> Dockerfile.new
    mv Dockerfile.new Dockerfile
  fi
  
  # 確保 requirements.txt 存在
  if [ ! -f "./requirements.txt" ]; then
    echo "創建空的 requirements.txt"
    touch "./requirements.txt"
  fi
  
  # 構建 Docker 映像
  echo "為 $function_name 構建 Docker 映像..."
  if ! DOCKER_BUILDKIT=1 docker build --platform=linux/amd64 -t "$ecr_repo_name:latest" .; then
    echo "為 $function_name 構建 Docker 映像失敗"
    # 恢復原始 Dockerfile
    mv Dockerfile.bak Dockerfile
    return 1
  fi
  
  # 標記映像
  echo "為 $function_name 標記映像..."
  if ! docker tag "$ecr_repo_name:latest" "$ECR_URL/$ecr_repo_name:latest"; then
    echo "為 $function_name 標記映像失敗"
    mv Dockerfile.bak Dockerfile
    return 1
  fi
  
  # 推送到 ECR，帶重試機制
  echo "將 $function_name 推送到 ECR..."
  
  if [ "$NO_RETRY" = "true" ]; then
    # 不使用重試機制
    if docker push "$ECR_URL/$ecr_repo_name:latest"; then
      echo "成功將 $function_name 推送到 ECR"
      # 更新 Lambda function
      echo "更新 Lambda function $function_name 使用最新 ECR image..."
      aws lambda update-function-code \
        --function-name "$function_name" \
        --image-uri "$ECR_URL/$ecr_repo_name:latest" \
        --region "$AWS_REGION" | cat
    else
      echo "推送 $function_name 失敗"
      mv Dockerfile.bak Dockerfile
      return 1
    fi
  else
    # 使用重試機制
    max_retries=3
    retry_count=0
    push_success=false
    
    while [ $retry_count -lt $max_retries ] && [ "$push_success" = false ]; do
      retry_count=$((retry_count + 1))
      echo "推送嘗試 $retry_count / $max_retries..."
      
      if docker push "$ECR_URL/$ecr_repo_name:latest"; then
        echo "成功將 $function_name 推送到 ECR"
        push_success=true
        # 更新 Lambda function
        echo "更新 Lambda function $function_name 使用最新 ECR image..."
        aws lambda update-function-code \
          --function-name "$function_name" \
          --image-uri "$ECR_URL/$ecr_repo_name:latest" \
          --region "$AWS_REGION" | cat
      else
        echo "推送嘗試 $retry_count 失敗"
        if [ $retry_count -lt $max_retries ]; then
          echo "等待 10 秒後重試..."
          sleep 10
          # 重新登錄 ECR 後重試
          aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL
        fi
      fi
    done
    
    if [ "$push_success" = false ]; then
      echo "所有推送嘗試都失敗了，請檢查網絡連接和 AWS 憑證"
      mv Dockerfile.bak Dockerfile
      return 1
    fi
  fi
  
  # 恢復原始 Dockerfile
  mv Dockerfile.bak Dockerfile
  
  # 返回到原始目錄
  cd - > /dev/null
  echo "成功構建並推送 $function_name"
  return 0
}

# 主程序
echo "=== AWS Lambda Docker 映像構建和推送工具 ==="
echo "重試機制: $([ "$NO_RETRY" = "true" ] && echo "已禁用" || echo "已啟用")"

# 登錄到 ECR
echo "登錄到 ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

# 處理參數
if [ $# -eq 0 ]; then
  # 沒有指定函數，構建所有函數
  echo "將構建和推送所有 Lambda 函數"
  for func in "${LAMBDA_FUNCTIONS[@]}"; do
    echo "==== 開始處理 $func ===="
    if ! build_and_push "$func"; then
      echo "處理 $func 時出錯，繼續處理下一個函數"
      # 清除任何可能的錯誤輸出
      clear
    fi
  done
elif [ $# -eq 1 ]; then
  # 檢查提供的函數名稱是否有效
  found=false
  for func in "${LAMBDA_FUNCTIONS[@]}"; do
    if [ "$func" = "$1" ]; then
      found=true
      break
    fi
  done
  
  if [ "$found" = true ]; then
    if ! build_and_push "$1"; then
      echo "處理 $1 時出錯"
      exit 1
    fi
  else
    echo "錯誤: 不認識的函數名稱 '$1'"
    usage
  fi
else
  usage
fi

echo "完成!"
