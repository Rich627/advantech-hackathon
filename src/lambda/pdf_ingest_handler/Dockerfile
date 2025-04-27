FROM --platform=linux/amd64 amazon/aws-lambda-python:3.9
FROM amazon/aws-lambda-python:3.9

# 複製函式碼
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY pdf_utils.py       ${LAMBDA_TASK_ROOT}

# 安裝相依套件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 告訴 Lambda 入口：檔名.函式
CMD ["lambda_function.lambda_handler"]