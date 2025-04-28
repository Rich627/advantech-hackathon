# 智慧基礎設施巡檢 ICAM-540 + GenAI 端雲協同方案
# Smart Infrastructure Inspection: ICAM-540 + GenAI Edge-Cloud Collaboration Solution

## 專案概述

本專案為2025雲湧智生：臺灣生成式AI應用黑客松競賽的參賽作品，由 Ambassador Avengers Assembly 團隊開發。

![專案簡報 | Project Presentation](/assets/F_研華科技_Ambassador Avengers Assembly.pdf)

### 背景與痛點

台灣擁有：
- 超過3萬座橋樑
- 300多條隧道
- 每日承載數百萬車流量

這些重要的基礎設施是維持日常生活運作的關鍵，但面臨以下挑戰：
1. 高昂的維護成本
2. 人工巡檢的時間成本
3. 潛在的安全風險
4. 檢測數據的即時性與準確性問題

### 解決方案

我們的解決方案結合了：
- Advantech ICAM-540 智能相機
- 生成式AI技術
- AWS雲端服務
- 端雲協同運算

提供：
- 自動化巡檢
- 即時異常檢測
- AI輔助決策
- 預測性維護

### 系統架構
![System Architecture](/assets/Advantech_hackathon.drawio.png)

#### 邊緣端
- ICAM-540 進行即時影像擷取
- Edge AI 進行初步的物件偵測與分類 (YOLOv11)
- 異常事件即時通報

#### 雲端架構

##### 核心服務
- Amazon S3: 影像資料儲存
- Amazon Bedrock: 進階AI分析
- AWS Lambda: 事件處理與業務邏輯
- Amazon OpenSearch: 資料索引與搜尋
- Amazon DynamoDB: 結構化資料儲存

##### 網路與安全
- Amazon CloudFront: 全球內容分發
- Amazon API Gateway: RESTful API 介面
- AWS WAF: Web 應用程式防火牆
- Amazon SNS: 事件通知

##### AI 技術
- Amazon Bedrock: 風險分析與處理方式建議

### 系統功能

1. 即時影像分析
   - 物件偵測
   - 異常識別
   - 即時警報

2. 文件處理
   - PDF 文件解析
   - 結構化資料提取
   - 報告生成

3. 資料管理
   - 影像儲存
   - 資料索引
   - 快速檢索

4. 安全防護
   - WAF 防護
   - 存取控制
   - 資料加密

### 開發與部署 

本專案使用以下工具進行開發與部署：
- Terraform 進行基礎設施即代碼 (IaC)
- AWS Lambda 實現無伺服器架構
- Docker 容器化部署
