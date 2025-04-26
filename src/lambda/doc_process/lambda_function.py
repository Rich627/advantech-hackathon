import base64
import json
import logging
import os
from uuid import uuid4

import boto3

# 配置日誌
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def upload_to_s3(pdf_data, report_id):
    """
    上傳 PDF 到 S3
    """
    bucket_name = os.environ.get("REPORT_BUCKET", None)
    if not bucket_name:
        raise ValueError("Missing S3 bucket configuration")

    key = f"reports/{report_id}.pdf"

    s3_client.put_object(
        Body=pdf_data,
        Bucket=bucket_name,
        Key=key,
        ContentType="application/pdf",
    )

    region = os.environ.get("AWS_REGION", "us-east-1")
    s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{key}"

    return s3_url


def lambda_handler(event, context):
    """
    處理 API Gateway 呼叫，接收 PDF 上傳 S3
    """
    try:
        logger.info("Received event: %s", json.dumps(event))

        # 解析 body
        body = event.get("body", None)
        if not body:
            raise ValueError("No body found in request")

        # is_base64_encoded = event.get("isBase64Encoded", False)
        # if not is_base64_encoded:
        #     raise ValueError("Expected body to be base64 encoded")

        # base64 decode 拿到 PDF bytes
        pdf_data = (
            event["body"].encode("utf-8")
            if isinstance(event["body"], str)
            else event["body"]
        )

        # 產生一個新的 report_id
        # report_id = str(uuid4())
        filename = event.get("headers", {}).get("x-filename")
        if not filename:
            raise ValueError("Missing x-filename header")

        # 上傳到 S3
        pdf_url = upload_to_s3(pdf_data, filename)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(
                {
                    "success": True,
                    "report_id": filename,
                    "pdf_url": pdf_url,
                    "message": "PDF 上傳成功",
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(
                {
                    "error": f"內部服務器錯誤: {str(e)}",
                }
            ),
        }
