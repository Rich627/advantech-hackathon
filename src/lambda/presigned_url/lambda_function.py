import boto3
import os
import logging
import json

def presigned_url_handler(object_key):
    """
    Lambda function to handle presigned URL generation for S3 objects.
    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    Returns:
        Dict containing presigned URL or error message
    """
    try:
        s3_client = boto3.client('s3')
        bucket_name = os.environ.get('BUCKET_NAME', 'your-bucket-name')
        
        # Generate presigned URL for the S3 object
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=60  # URL valid for 60 seconds
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'presigned_url': presigned_url})
        }
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
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
        # Extract object key from the event
        object_key = event['Records'][0]['s3']['object']['key']
        
        # Call the presigned URL handler function
        return presigned_url_handler(object_key)
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }