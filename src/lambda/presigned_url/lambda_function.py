import boto3
import os
import logging
import json

def get_presigned_url(object_key):
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
        print(f"Error generating download presigned URL: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def generate_upload_url(object_key, content_type='image/jpeg'):
    """
    Generate a presigned URL for uploading an object to S3.
    
    Parameters:
        object_key: String path where the object will be stored
        content_type: MIME type of the object being uploaded
    Returns:
        Dict containing presigned URL for uploading or error message
    """
    try:
        s3_client = boto3.client('s3')
        bucket_name = os.environ.get('BUCKET_NAME', 'genai-hackthon-20250426-image-bucket')
        
        # Generate presigned URL for uploading to S3
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_key,
                'ContentType': content_type
            },
            ExpiresIn=300  # URL valid for 5 minutes to allow time for upload
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'presigned_url': presigned_url,
                'operation': 'put',
                'bucket': bucket_name,
                'key': object_key
            })
        }
    except Exception as e:
        print(f"Error generating upload presigned URL: {e}")
        return {
            'statusCode': 500,
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
        # Handle API Gateway requests
        if 'httpMethod' in event or 'queryStringParameters' in event:
            # Get query parameters
            params = event.get('queryStringParameters', {}) or {}
            
            # Required parameter: action (upload or download)
            action = params.get('action', '').lower()
            
            # If action is upload, generate upload URL
            if action == 'upload':
                object_key = params.get('key')
                content_type = params.get('content_type', 'image/jpeg')
                
                if not object_key:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Missing required parameter: key'})
                    }
                
                return generate_upload_url(object_key, content_type)
            
            # For download or other actions, expect object_key
            else:
                object_key = params.get('key')
                
                if not object_key:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Missing required parameter: key'})
                    }
                    
                return get_presigned_url(object_key)
        
        # Handle S3 event triggers
        elif 'Records' in event and len(event['Records']) > 0 and 's3' in event['Records'][0]:
            object_key = event['Records'][0]['s3']['object']['key']
            return get_presigned_url(object_key)
        
        # Invalid request format
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid request format',
                    'usage': 'For upload: ?action=upload&key=path/to/file.jpg&content_type=image/jpeg'
                })
            }
            
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }