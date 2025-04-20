# 過程
## 創建 ECR 儲存庫
```
aws ecr create-repository --repository-name daily_report_handler --region us-east-1
aws ecr create-repository --repository-name llm_issue_handler --region us-east-1
aws ecr create-repository --repository-name sns_handler --region us-east-1
```

## 部署流程
```
cd <lambda_function_directory>

docker build -t <image_name> .

docker tag <image_name>:latest <your-account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:latest

docker push <your-account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:latest
```