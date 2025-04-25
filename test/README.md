# 裂縫檢測系統測試環境

這個資料夾包含用於測試裂縫檢測系統的資料上傳和處理流程。

## 元數據格式

裂縫元數據 (metadata.json) 格式如下：

```json
{
  "id": "ISSUE-001", // 問題ID範圍: ISSUE-001 ~ ISSUE-999
  "location": "A1", // 位置代碼
  "crack_type": "Longitudinal", // 裂縫類型: Longitudinal, Transverse, Diagonal, Radial, Annular, Rippled, Network, Turtle-shell patterned
  "length_cm": 150, // 長度範圍: 0 ~ 9999 公分
  "depth_cm": 2, // 深度範圍: 0 ~ 9999 公分
  "date": "2025-05-13", // 日期格式: YYYY-MM-DD
  "image_url": "https://s3.amazonaws.com/xxx/image/ISSUE-001.jpg" // 圖片URL
}
```

## 資料夾結構

```
test/
├── issues/
│   ├── ISSUE-XXX/
│   │   ├── ISSUE-XXX.json     # 裂縫資訊
│   │   └── ISSUE-XXX.jpg     # 圖片檔案
```

## 使用方法

1. 確保您已安裝並配置 AWS CLI
2. 編輯 `upload_test.sh` 腳本，將 `BUCKET_NAME` 變數設置為您的 S3 儲存桶名稱
3. 執行腳本來建立測試檔案並上傳到 S3：

```bash
chmod +x upload_test.sh
./upload_test.sh
```

4. 檢查 Lambda 函數的 CloudWatch 日誌，確認是否成功觸發

## 注意事項

- 確保您的 AWS 憑證有權限上傳檔案到指定的 S3 儲存桶
- 確保您的 Lambda 函數已配置了正確的 S3 事件觸發器 