# S3 Lambda 觸發測試環境

這個資料夾包含用於測試 S3 事件觸發 Lambda 函數的腳本和結構。

## 資料夾結構

測試環境模擬了 S3 儲存桶的結構：

```
test/
├── issues/
│   ├── issue_{timestamp}/
│   │   ├── metadata.json     # 裂縫資訊
│   │   └── image.jpg         # 圖片檔案
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