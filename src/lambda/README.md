# 部署流程
```
cd <lambda_function_directory>

docker build -t <image_name> .

docker tag <image_name>:latest <your-account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:latest

docker push <your-account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:latest
```