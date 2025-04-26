#!/bin/bash

# 設定變數
BUCKET_NAME="your-bucket-name"  # 請替換成您的S3儲存桶名稱
CURRENT_TIMESTAMP=$(date "+%Y_%m_%d_%H_%M_%S")
ISSUE_ID="issue_${CURRENT_TIMESTAMP}"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
ISSUE_FOLDER="issues/${ISSUE_ID}"
CLOUDFRONT_URL="https://d3hi3054wpq3c0.cloudfront.net"

# 建立測試資料夾結構
mkdir -p "test/${ISSUE_FOLDER}"

# 建立metadata.json檔案
cat > "test/${ISSUE_FOLDER}/${ISSUE_ID}.json" << EOF
{
  "id": "${ISSUE_ID}",
  "timestamp": "${TIMESTAMP}",
  "length": "15.5",
  "width": "10.2",
  "position": "mountain",
  "material": "concrete",
  "crack_type": "Longitudinal",
  "crack_location": "A",
  "image_url": "https://s3.amazonaws.com/${BUCKET_NAME}/image/${ISSUE_ID}.jpg"
}
EOF

# 建立一個測試用的空白圖片檔案
touch "test/${ISSUE_FOLDER}/${ISSUE_ID}.jpg"
# 或者使用:
# convert -size 100x100 xc:white "test/${ISSUE_FOLDER}/${ISSUE_ID}.jpg"  # 需要ImageMagick

echo "測試檔案已建立在 test/${ISSUE_FOLDER} 資料夾中"

echo "開始上傳檔案..."

# 取得JSON檔案的presigned URL
echo "取得metadata.json的presigned URL..."
JSON_PRESIGNED_URL=$(curl -s -X GET "${CLOUDFRONT_URL}" | grep -o '"url": "[^"]*"' | cut -d'"' -f4)

if [ -z "$JSON_PRESIGNED_URL" ]; then
    echo "無法獲取metadata.json的presigned URL，請檢查API是否正常運作"
    exit 1
fi

# 上傳metadata.json
echo "上傳metadata.json..."
curl -X PUT -T "test/${ISSUE_FOLDER}/${ISSUE_ID}.json" -H "Content-Type: application/json" "${JSON_PRESIGNED_URL}"

# 取得圖片檔案的presigned URL
echo "取得圖片檔案的presigned URL..."
IMAGE_PRESIGNED_URL=$(curl -s -X GET "${CLOUDFRONT_URL}" | grep -o '"url": "[^"]*"' | cut -d'"' -f4)

if [ -z "$IMAGE_PRESIGNED_URL" ]; then
    echo "無法獲取圖片檔案的presigned URL，請檢查API是否正常運作"
    exit 1
fi

# 上傳圖片檔案
echo "上傳圖片檔案..."
curl -X PUT -T "test/${ISSUE_FOLDER}/${ISSUE_ID}.jpg" -H "Content-Type: image/jpeg" "${IMAGE_PRESIGNED_URL}"

echo "上傳完成！"
echo "請檢查 Lambda 函數日誌來確認是否正確觸發及執行" 