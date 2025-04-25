import boto3
import botocore
import os
import logging
import json
import requests

def download_file_from_s3(bucket, key):
    """
    Download file from S3 bucket
    Parameters:
        bucket: S3 bucket name
        key: S3 object key
    Returns:
        Content of the file
    """
    s3_client = boto3.client('s3')
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read()
        return content
    except botocore.exceptions.ClientError as e:
        print(f"Error downloading file: {e}")
        raise

def get_embedding(content):
    """
    Get embedding for the provided content
    Parameters:
        content: Content to get embedding for
    Returns:
        List of floats representing the embedding
    """
    # Placeholder for actual embedding logic
    # This should be replaced with the actual implementation
    return [0.0] * 768  # Example: 768-dimensional embedding

def vdb_query(metadata):
    """
    Query VDB with the provided metadata
    Parameters:
        metadata: Metadata to query VDB
    Returns:
        Response from VDB query
    """
    try:
        # 取得 embedding（此處假設你有 embedding function）
        embedding = get_embedding(metadata)  # List[float] 長度需與 index 維度相符
        
        try:
            opensearch_url = os.environ['OPENSEARCH_ENDPOINT']
            headers = {"Content-Type": "application/json"}
            query_body = {
                "size": 1,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": embedding,
                            "k": 1
                        }
                    }
                }
            }

            vdb_resp = requests.post(
                f"{opensearch_url}/icam-vectors/_search",
                headers=headers,
                data=json.dumps(query_body)
            )

            if vdb_resp.status_code == 200:
                hits = vdb_resp.json().get("hits", {}).get("hits", [])
                kb_result = hits[0]['_source']['description'] if hits else "無相關紀錄"
                return kb_result
        except requests.exceptions.RequestException as e:
            print(f"Error querying VDB: {e}")
            return "Search failed in VDB"
    except Exception as e:
        print(f"Error in getting embeddings: {e}")
        return "Could not get embedding"

def call_bedrock_model(metadata):
    """
    Call Bedrock model with the provided metadata
    Parameters:
        metadata: Metadata to send to the Bedrock model
    Returns:
        Response from the Bedrock model
    """
    # Retrieve related knowledge base from VDB
    kb_result = vdb_query(metadata)
    
    # Call Bedrock model with the knowledge base
    try:
        bedrock_client = boto3.client('bedrock')
        response = bedrock_client.invoke_model(
            modelId=os.environ['BEDROCK_MODEL_ID'],
            contentType='application/json',
            accept='application/json',
            body=json.dumps({"input": metadata, "knowledge_base": kb_result})
        )
        return response['body'].read()
    except botocore.exceptions.ClientError as e:
        print(f"Error calling Bedrock model: {e}")
        return "Model invocation failed"

def lambda_handler(event, context):
    """
    When new image & icam metadata stored in s3, this lambda will be triggered to call bedrock model for generating solution with knowledge base.
    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """
    try:
        # get message from event trigger by s3
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        metadata = download_file_from_s3(bucket, key)
        solution = call_bedrock_model(metadata)
        
        # Notify SNS with the solution by invoking another lambda function
        lambda_client = boto3.client('lambda')
        payload = {
            'solution': solution,
            'metadata': metadata.decode('utf-8') if isinstance(metadata, bytes) else metadata,
            'source': {
                'bucket': bucket,
                'key': key
            }
        }
        
        lambda_client.invoke(
            FunctionName='notification_lambda_function_name',  # 替換為目標 Lambda 函數的名稱
            InvocationType='Event',  # 'Event'為非同步呼叫，'RequestResponse'為同步呼叫
            Payload=json.dumps(payload)
        )
        
        return {
            'statusCode': 200,
            'body': 'Notification sent successfully'
        }
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': f"Error processing event: {str(e)}"
        }