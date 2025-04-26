# 裂縫檢測系統測試環境

這個資料夾包含用於測試裂縫檢測系統的資料上傳和處理流程。

## 元數據格式

裂縫元數據 (metadata.json) 格式如下：

```json
{
  "id": "issue_2023_10_27_10_00_00", //issue id range: ISSUE-001 ~ ISSUE-999
  "timestamp": "2023-10-27  10:00:00",
  "length_cm": 150, //length range: 0 ~ 9999
  "depth_cm": 2, //depth range: 0 ~ 9999
  "position": "mountain",
  "material": "concrete",
  "crack_type": "Longitudinal", //crack type range: Longitudinal, Transverse, Diagonal, Radial, Annular, Rippled, Network, Turtle-shell patterned
  "crack_location": "A", //crack location range: A to Z
  "image_url": "https://s3.amazonaws.com/xxx/image/ISSUE-001.jpg"
}
```

欄位說明：
- `id`: 問題ID，格式為 issue_YYYY_MM_DD_HH_MM_SS，範圍 ISSUE-001 ~ ISSUE-999
- `timestamp`: 時間戳記，格式為 YYYY-MM-DD HH:MM:SS
- `length_cm`: 裂縫長度（公分），範圍 0 ~ 9999
- `depth_cm`: 裂縫深度（公分），範圍 0 ~ 9999
- `position`: 位置描述
- `material`: 材質描述
- `crack_type`: 裂縫類型，可選值：Longitudinal, Transverse, Diagonal, Radial, Annular, Rippled, Network, Turtle-shell patterned
- `crack_location`: 裂縫位置代碼，範圍 A 到 Z
- `image_url`: 圖片URL

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