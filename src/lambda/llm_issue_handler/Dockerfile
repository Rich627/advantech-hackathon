FROM --platform=linux/amd64 amazon/aws-lambda-python:3.9

# 複製函數程式碼
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# 安裝依賴項
COPY requirements.txt .
RUN pip install -r requirements.txt

# 設定 Lambda 處理程序
CMD [ "lambda_function.lambda_handler" ]