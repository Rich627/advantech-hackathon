#!/bin/bash

# 設定變數
BUCKET_NAME="your-bucket-name"  # 請替換成您的S3儲存桶名稱
ISSUE_ID="ISSUE-001"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
ISSUE_FOLDER="issues/${ISSUE_ID}"

# 建立測試資料夾結構
mkdir -p "test/${ISSUE_FOLDER}"

# 建立metadata.json檔案
cat > "test/${ISSUE_FOLDER}/${ISSUE_ID}.json" << EOF
{
  "id": "${ISSUE_ID}",
  "timestamp": "${TIMESTAMP}",
  "length_cm": 150,
  "depth_cm": 2,
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

# 上傳檔案到S3
echo "開始上傳檔案到S3..."

# 上傳metadata.json
aws s3 cp "test/${ISSUE_FOLDER}/${ISSUE_ID}.json" "s3://${BUCKET_NAME}/${ISSUE_FOLDER}/${ISSUE_ID}.json"

# 上傳圖片檔案
aws s3 cp "test/${ISSUE_FOLDER}/${ISSUE_ID}.jpg" "s3://${BUCKET_NAME}/image/${ISSUE_ID}.jpg"

echo "上傳完成！"
echo "已上傳檔案到: s3://${BUCKET_NAME}/${ISSUE_FOLDER}/ 和 s3://${BUCKET_NAME}/image/"
echo "請檢查 Lambda 函數日誌來確認是否正確觸發及執行" 