import boto3
import botocore
import os
import logging

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def notify_sns(message):
    """
    Send a notification to an SNS topic
    Parameters:
        sns_client: Boto3 SNS client
        message: Message to send
    Returns:
        Response from SNS publish call
    """
    try:
        sns_client = boto3.client('sns')
        response = sns_client.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=message,
            Subject='【警告】設備異常檢測'
        )
        return response
    except botocore.exceptions.ClientError as e:
        logger.error(f"Failed to send SNS notification: {e}")
        raise

def lambda_handler(event, context):
    """
    Main Lambda handler function
    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """
    try:
        # get message from event(send from llm_issue_handler)
        message = event['Records'][0]['Sns']['Message']
        logger.info(f"Received message: {message}")
        # Notify SNS with the message
        response = notify_sns(message)
        logger.info(f"SNS response: {response}")    
        return {
            'statusCode': 200,
            'body': 'Notification sent successfully'
        }
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return {
            'statusCode': 500,
            'body': 'Error processing event'
        }