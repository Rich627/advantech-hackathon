#!/bin/bash

# 設定變數
BUCKET_NAME="your-bucket-name"  # 請替換成您的S3儲存桶名稱
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
ISSUE_ID="issue_001"
ISSUE_FOLDER="issues/issue_${TIMESTAMP}"

# 建立測試資料夾結構
mkdir -p "test/${ISSUE_FOLDER}"

# 建立metadata.json檔案
cat > "test/${ISSUE_FOLDER}/metadata.json" << EOF
{
  "id": "${ISSUE_ID}",
  "timestamp": "${TIMESTAMP}",
  "length": "15.5",
  "width": "10.2",
  "position": "mountain",
  "Material": "cement",
  "crack_location": "A"
}
EOF

# 建立一個測試用的空白圖片檔案
# 如果您有真實的圖片，請將此部分替換為複製您的圖片的指令
touch "test/${ISSUE_FOLDER}/image.jpg"
# 或者使用:
# convert -size 100x100 xc:white "test/${ISSUE_FOLDER}/image.jpg"  # 需要ImageMagick

echo "測試檔案已建立在 test/${ISSUE_FOLDER} 資料夾中"

# 上傳檔案到S3
echo "開始上傳檔案到S3..."

# 上傳metadata.json (先上傳，因為它會觸發Lambda函數)
aws s3 cp "test/${ISSUE_FOLDER}/metadata.json" "s3://${BUCKET_NAME}/${ISSUE_FOLDER}/metadata.json"

# 上傳image.jpg
aws s3 cp "test/${ISSUE_FOLDER}/image.jpg" "s3://${BUCKET_NAME}/${ISSUE_FOLDER}/image.jpg"

echo "上傳完成！"
echo "已上傳檔案到: s3://${BUCKET_NAME}/${ISSUE_FOLDER}/"
echo "請檢查Lambda函數日誌來確認是否正確觸發及執行" 