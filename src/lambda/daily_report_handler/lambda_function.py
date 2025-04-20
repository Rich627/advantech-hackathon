import json
import os
import requests
import boto3
import botocore

def get_text_embedding(text):
    # use bedrock embedding model api
    bedrock_client = boto3.client("bedrock")
    response = bedrock_client.invoke_model(
        modelId=os.environ["BEDROCK_EMBEDDING_MODEL"],
        contentType="text/plain",
        accept="application/json",
        body=text
    )
    embedding = json.loads(response["body"].read().decode("utf-8"))["embedding"]
    return embedding

def ingest_report_to_opensearch(report, embedded_report):
    # use opensearch api to ingest report
    try:
        opensearch_url = os.environ["OPENSEARCH_ENDPOINT"]
        headers = {"Content-Type": "application/json"}
        doc = {
            "embedding": embedded_report,
            "description": report["description"],
            "report_id": report["report_id"],
            "timestamp": report["timestamp"]
        }
        response = requests.post(
            f"{opensearch_url}/icam-vectors/_doc",
            headers=headers,
            data=json.dumps(doc)
        )
        if response.status_code == 201:
            return {"statusCode": 200, "body": json.dumps({"msg": "Report ingested successfully"})}
        else:
            return {"statusCode": response.status_code, "body": json.dumps({"msg": "Failed to ingest report"})}
    except requests.exceptions.RequestException as e:
        return {"statusCode": 500, "body": json.dumps({"msg": f"Error: {str(e)}"})}
        

def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        report = body.get("report", {})
        description = report.get("description", "")

        if not description:
            return {"statusCode": 400, "body": json.dumps({"msg": "description is required"})}

        embedding = get_text_embedding(description)
        report["content"] = description
        ingest_report_to_opensearch(report, embedding)

        return {
            "statusCode": 200,
            "body": json.dumps({"msg": "Report processed successfully"})
        }
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"msg": "Invalid JSON format"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"msg": f"Internal server error: {str(e)}"})
        }
