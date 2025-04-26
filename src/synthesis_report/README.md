# 隧道裂縫資料生成工具

這個工具使用 Amazon Bedrock Foundation Models 來生成合成資料，用於隧道裂縫維修報告系統。它可以根據提供的範例資料，生成具有變化性的新資料。

## 功能特點

- 使用 Amazon Bedrock 的大型語言模型生成合成資料
- 批次處理，有效處理 API 回應限制
- 完整的資料驗證和修復機制
- 可自訂生成參數和資料格式

## 安裝需求

```
pip install boto3
```

確保你有適當的 AWS 憑證設定，並具有訪問 Amazon Bedrock 的權限。

## 使用方法

1. 準備範例資料在 `metadata/sample_metadata.json`
2. 執行程式:

```bash
python synthesis.py
```

3. 生成的資料將保存在 `metadata/generated_metadata.json`

## 自訂生成

你可以透過修改 `main()` 函數來自訂生成過程:

```python
# 初始化合成器
synthesizer = BedrockDataSynthesizer(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",  # 指定模型 ID
    batch_size=3,  # 每次 API 調用生成的資料筆數
    temperature=0.7  # 模型創造力（較高值 = 更多變化）
)

# 生成資料
total_to_generate = 20  # 要生成的總資料筆數
start_id = 10  # 起始 ID 編號
generated_data = synthesizer.generate_data(samples, total_to_generate, start_id)
```

## 資料格式

生成的資料遵循以下格式:

```json
{
  "issue_id": "ISSUE-001",
  "location": "A1",
  "crack_type": "Longitudinal",
  "length_cm": 150,
  "depth_cm": 2,
  "engineer": "張工程師",
  "risk_level": "High",
  "date": "2025-05-13",
  "action": "灌漿修補",
  "status": "Done",
  "description": "發現縱向裂縫，立即進行灌漿修補。修補後進行強度測試，確認修復效果良好。",
  "image_url": "https://s3.amazonaws.com/xxx/image/ISSUE-001.jpg"
}
```

## 欄位限制

- issue_id: 格式為 ISSUE-XXX，XXX為三位數字，範圍001-999
- location: 範圍 A1 ~ C3
- crack_type: 必須是以下其中之一: Longitudinal, Transverse, Diagonal, Radial, Annular, Rippled, Network, Turtle-shell patterned
- length_cm: 範圍 0 ~ 9999
- depth_cm: 範圍 0 ~ 9999
- risk_level: 必須是以下其中之一: Low, Medium, High
- status: 必須是以下其中之一: Done, In Progress, Not Started 