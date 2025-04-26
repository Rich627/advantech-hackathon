import boto3
import os
import logging
import json
import uuid
import requests
import time
import base64
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def extract_issue_id_from_json(json_data):
    """
    Extract issue ID from JSON content
    
    Parameters:
        json_data: JSON data as dict or string
    Returns:
        String issue ID or None if not found
    """
    try:
        # 如果輸入是字串，嘗試解析為JSON
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        
        # 從JSON中提取id欄位
        if 'id' in json_data:
            return json_data['id']
        
        return None
    except Exception as e:
        logger.error(f"Error extracting issue ID from JSON: {e}")
        return None

def generate_upload_metadata_url(object_key):
    """
    Generate a presigned URL for uploading metadata to S3.
    
    Parameters:
        object_key: String path where the object will be stored
    Returns:
        Dict containing presigned URL for uploading or error message
    """
    try:
        content_type='application/json'
        s3_client = boto3.client('s3')
        bucket_name = os.environ.get('BUCKET_NAME', 'genai-hackthon-20250426-image-bucket')
        folder_path = f"issue/{object_key}/"
        json_extension = '.json'

        full_object_key = folder_path + object_key + json_extension

        logger.info(f"Generating presigned URL for {full_object_key} with content type {content_type}")

        # Generate presigned URL for uploading to S3
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': full_object_key,
                'ContentType': content_type
            },
            ExpiresIn=300  # URL valid for 5 minutes to allow time for upload
        )
        print(f"presigned url: {presigned_url}")
        logger.info(f"Presigned URL generated: {presigned_url}")
        return presigned_url    
    except Exception as e:
        logger.error(f"Error generating upload presigned URL: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

def generate_upload_image_url(object_key):
    """
    Generate a presigned URL for uploading an object to S3.
    
    Parameters:
        object_key: String path where the object will be stored
        content_type: MIME type of the object being uploaded
        file_content: File content (optional, for JSON files to extract ID)
    Returns:
        Dict containing presigned URL for uploading or error message
    """
    try:
        content_type='image/jpg'
        s3_client = boto3.client('s3')
        bucket_name = os.environ.get('BUCKET_NAME', 'genai-hackthon-20250426-image-bucket')
        folder_path = f"issue/{object_key}/"
        jpg_extension = '.jpg'
      
        # 完整的 S3 物件金鑰
        full_object_key = folder_path + object_key + jpg_extension
        
        logger.info(f"Generating presigned URL for {full_object_key} with content type {content_type}")
        
        # Generate presigned URL for uploading to S3
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': full_object_key,
                'ContentType': content_type
            },
            ExpiresIn=300  # URL valid for 5 minutes to allow time for upload
        )
        print(f"presigned url: {presigned_url}")
        logger.info(f"Presigned URL generated: {presigned_url}")
        
        # 構建標準 S3 URL (不是預簽名的 URL)
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{full_object_key}"
        print(f"standard s3 url: {s3_url}")
        logger.info(f"Standard S3 URL: {s3_url}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'presigned_url': presigned_url,
                'operation': 'put',
                'bucket': bucket_name,
                'key': full_object_key,
                's3_url': s3_url
            })
        }
    except Exception as e:
        logger.error(f"Error generating upload presigned URL: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

def upload_to_s3_via_presigned_url(file_content, presigned_url, content_type='application/json'):
    """
    Upload a file to S3 using a presigned URL.
    Parameters:
        file_content: File content to upload
        presigned_url: Presigned URL for uploading to S3
        content_type: MIME type of the file being uploaded
    Returns:
        Dict containing upload status or error message
    """
    try:
        print(f"Uploading file content to S3 using presigned URL: {presigned_url}")
        print(f"File content: {file_content}")
        # Upload the file content to S3 using the presigned URL
        response = requests.put(
            presigned_url,
            data=file_content,
            headers={'Content-Type': content_type}
        )
        if response.status_code == 200:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({'message': 'File uploaded successfully'})
            }
        else:
            return {
                'statusCode': response.status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': response.text})
            }
    except Exception as e:
        logger.error(f"Error uploading file to S3: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }     
       

def lambda_handler(event, context):
    """
    Lambda function entry point.
    
    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    Returns:
        Dict containing presigned URL or error message
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        print(f"Received event: {event}")
   
        # Handle API Gateway v2 HTTP API requests
        if 'version' in event and event.get('version') == '2.0':
            print("API Gateway v2 request detected")
            logger.info("API Gateway v2 request detected")
            # 處理直接上傳請求 (對 API Gateway v2)
            if event.get('requestContext', {}).get('http', {}).get('method') == 'POST' and 'body' in event:
                # 獲取內容類型
                content_type = event.get('headers', {}).get('content-type', 'image/jpeg')
                
                # 如果是 application/json 類型，檢查是否只包含 object_key
                if 'application/json' in content_type.lower():
                    try:
                        json_body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
                        
                        if 'object_key' in json_body and len(json_body) == 1:
                            object_key = json_body['object_key']
                            print(f"收到 application/json 請求，只包含 object_key: {object_key}")
                            logger.info(f"Received application/json request with object_key: {object_key}")
                            
                            result = generate_upload_image_url(object_key)
                            return result
                    except Exception as e:
                        logger.error(f"Error parsing JSON body: {e}")
                else:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': 'Invalid content type or missing object_key'})
                    }
                
                # 獲取文件內容 (非 object_key 請求的情況)
                file_content = event['body']
                object_key = extract_issue_id_from_json(file_content)
                if not object_key:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': 'Missing required parameter: object_key'})
                    }
                presigned_url = generate_upload_metadata_url(object_key)
                return upload_to_s3_via_presigned_url(file_content, presigned_url, content_type)
            
            
            # 如果處理成功，僅返回 s3_url (不含 presigned_url)
            if result.get('statusCode') == 200:
                response_data = json.loads(result['body'])
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': json.dumps({
                        's3_url': response_data.get('s3_url')
                    })
                }
            
            return result
    
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Invalid request format',
                    'usage': 'For upload: ?action=upload&key=path/to/file.jpg&content_type=image/jpeg'
                })
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }