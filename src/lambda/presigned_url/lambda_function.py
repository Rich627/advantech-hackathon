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


def is_image_content_type(content_type):
    """
    Determine if the content type is an image type
    
    Parameters:
        content_type: MIME type string
    Returns:
        Boolean indicating whether content type is an image
    """
    image_types = ['image/jpg', 'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/tiff', 'image/bmp']
    return content_type.lower() in image_types

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

def extract_filename_from_path(file_path):
    """
    Extract filename from a path
    
    Parameters:
        file_path: File path or URL
    Returns:
        Filename without extension
    """
    try:
        # 從路徑中提取檔名
        filename = os.path.basename(file_path)
        # 移除副檔名
        filename = os.path.splitext(filename)[0]
        return filename
    except Exception as e:
        logger.error(f"Error extracting filename: {e}")
        return None

def get_target_folder(content_type, object_key, file_content=None):
    """
    Determine the target folder based on content type and file content
    
    Parameters:
        content_type: MIME type string
        object_key: Original object key or filename
        file_content: File content (for JSON files to extract ID)
    Returns:
        String folder path ('issue/<file_name>/' or 'issue/<json_id>/')
    """
    try:
        # 如果是圖片類型
        if is_image_content_type(content_type):
            # 從檔名中提取主檔名
            filename = extract_filename_from_path(object_key)
            if not filename:
                # 如果無法提取有效檔名，使用時間戳作為資料夾名稱
                filename = f"image_{int(time.time())}"
            
            return f"issue/{filename}/"
        
        # 如果是JSON類型
        elif content_type.lower() == 'application/json':
            # 嘗試從JSON內容中提取id
            if file_content:
                try:
                    # 如果file_content是二進位資料，先轉為字串
                    if isinstance(file_content, bytes):
                        json_str = file_content.decode('utf-8')
                    else:
                        json_str = file_content
                    
                    json_data = json.loads(json_str)
                    issue_id = extract_issue_id_from_json(json_data)
                    
                    if issue_id:
                        return f"issue/{issue_id}/"
                except Exception as e:
                    logger.error(f"Error parsing JSON content: {e}")
            
            # 如果無法從JSON提取ID，則使用檔名
            filename = extract_filename_from_path(object_key)
            if not filename:
                # 如果無法提取有效檔名，使用時間戳作為資料夾名稱
                filename = f"json_{int(time.time())}"
            
            return f"issue/{filename}/"
        
        # 預設情況
        else:
            return "issue/default/"
            
    except Exception as e:
        logger.error(f"Error determining target folder: {e}")
        # 發生錯誤時的預設資料夾
        return "issue/default/"
      
def generate_download_url(object_key):
    """
    Generate a presigned URL for downloading an S3 object.
    
    Parameters:
        object_key: String path to the S3 object
    Returns:
        Dict containing presigned URL for downloading or error message
    """
    try:
        s3_client = boto3.client('s3')
        bucket_name = os.environ.get('BUCKET_NAME', 'genai-hackthon-20250426-image-bucket')
        
        # Generate presigned URL for downloading the S3 object
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=60  # URL valid for 60 seconds
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'presigned_url': presigned_url, 'operation': 'get'})
        }
    except Exception as e:
        logger.error(f"Error generating download presigned URL: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
  
def generate_upload_url(object_key, content_type='image/jpeg', file_content=None):
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
        s3_client = boto3.client('s3')
        bucket_name = os.environ.get('BUCKET_NAME', 'genai-hackthon-20250426-image-bucket')
        
        # 取得檔案名稱（不含路徑）
        filename = os.path.basename(object_key)
        
        # 決定目標資料夾路徑
        target_folder = get_target_folder(content_type, object_key, file_content)
        
        # 完整的 S3 物件金鑰
        full_object_key = f"{target_folder}{filename}"
        
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
        
        # 構建標準 S3 URL (不是預簽名的 URL)
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{full_object_key}"
        
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
    
def upload_to_s3_via_presigned_url(file_content, content_type='image/jpeg'):
    """
    Generate a presigned URL and use it to upload a file to S3
    
    Parameters:
        file_content: Binary content of the file to upload
        content_type: MIME type of the file being uploaded
    Returns:
        Dict containing the result of the upload operation
    """
    try:
        # 1. 生成唯一的檔案名
        unique_id = str(uuid.uuid4())
        timestamp = str(int(time.time()))
        
        # 根據內容類型決定檔案副檔名
        file_ext = '.jpg'  # 預設
        if content_type == 'application/json':
            file_ext = '.json'
        elif 'image/' in content_type:
            ext = content_type.split('/')[-1]
            if ext in ['jpeg', 'png', 'gif', 'webp', 'tiff', 'bmp']:
                file_ext = f'.{ext}'
        
        # 生成物件鍵名（檔名部分）
        filename = f"{timestamp}_{unique_id}{file_ext}"
        
        # 2. 獲取 presigned URL（傳遞檔案內容以便JSON檔案提取ID）
        result = generate_upload_url(filename, content_type, file_content)
        
        if result['statusCode'] != 200:
            return result
        
        response_data = json.loads(result['body'])
        presigned_url = response_data['presigned_url']
        s3_url = response_data['s3_url']
        
        # 3. 使用 presigned URL 上傳文件到 S3
        upload_response = requests.put(
            presigned_url,
            data=file_content,
            headers={'Content-Type': content_type}
        )
        
        # 4. 檢查上傳結果
        if upload_response.status_code >= 200 and upload_response.status_code < 300:
            logger.info(f"File uploaded successfully to {s3_url}")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'message': 'File uploaded successfully',
                    'bucket': response_data['bucket'],
                    'key': response_data['key'],
                    's3_url': s3_url
                })
            }
        else:
            logger.error(f"Error uploading file. Status code: {upload_response.status_code}, Response: {upload_response.text}")
            return {
                'statusCode': upload_response.status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f"Failed to upload file. Status code: {upload_response.status_code}",
                    'details': upload_response.text
                })
            }
    except Exception as e:
        logger.error(f"Error in upload_to_s3_via_presigned_url: {str(e)}")
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
        
        # 處理直接上傳請求 (POST 方法含有文件内容)
        if 'httpMethod' in event and event['httpMethod'] == 'POST' and 'body' in event:
            # 獲取內容類型
            content_type = event.get('headers', {}).get('content-type', 'image/jpeg')
            
            # 獲取文件內容
            file_content = event['body']
            
            # 如果主體是 base64 編碼的，先解碼
            if event.get('isBase64Encoded', False):
                file_content = base64.b64decode(file_content)
            
            # 使用 presigned URL 上傳文件
            return upload_to_s3_via_presigned_url(file_content, content_type)
        
        # Handle API Gateway v2 HTTP API requests
        elif 'version' in event and event.get('version') == '2.0':
            # 處理直接上傳請求 (對 API Gateway v2)
            if event.get('requestContext', {}).get('http', {}).get('method') == 'POST' and 'body' in event:
                # 獲取內容類型
                content_type = event.get('headers', {}).get('content-type', 'image/jpeg')
                
                # 獲取文件內容
                file_content = event['body']
                
                # 如果主體是 base64 編碼的，先解碼
                if event.get('isBase64Encoded', False):
                    file_content = base64.b64decode(file_content)
                
                # 使用 presigned URL 上傳文件
                return upload_to_s3_via_presigned_url(file_content, content_type)
            
            # 處理一般請求 (獲取 presigned URL)
            query_params = event.get('queryStringParameters', {}) or {}            
            content_type = query_params.get('content_type', 'image/jpeg')
            
            # 生成唯一的檔案名稱，如果未提供
            object_key = query_params.get('key')
            if not object_key:
                # 生成唯一檔案名
                unique_id = str(uuid.uuid4())
                timestamp = event.get('requestContext', {}).get('timeEpoch', '') or int(time.time())
                
                # 根據內容類型決定檔案副檔名
                file_ext = '.jpg'  # 預設
                if content_type == 'application/json':
                    file_ext = '.json'
                elif 'image/' in content_type:
                    file_ext = '.' + content_type.split('/')[-1]
                
                # 僅生成檔名部分，不包含路徑
                object_key = f"{timestamp}_{unique_id}{file_ext}"
            
            # 生成上傳 URL
            result = generate_upload_url(object_key, content_type)
            
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
            
        # 處理常規 API Gateway 請求
        elif 'httpMethod' in event or 'queryStringParameters' in event:
            params = event.get('queryStringParameters', {}) or {}
            
            # 必需參數：動作（上傳或下載）
            action = params.get('action', '').lower()
            
            if action == 'upload':
                object_key = params.get('key')
                content_type = params.get('content_type', 'image/jpeg')
                
                if not object_key:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': 'Missing required parameter: key'})
                    }
                
                result = generate_upload_url(object_key, content_type)
                
                # 如果處理成功，僅返回 s3_url
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
                object_key = params.get('key')
                
                if not object_key:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': 'Missing required parameter: key'})
                    }
                    
                return generate_download_url(object_key)
        
        elif 'Records' in event and len(event['Records']) > 0 and 's3' in event['Records'][0]:
            object_key = event['Records'][0]['s3']['object']['key']
            return generate_download_url(object_key)
        
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