import json
import boto3
import os
import logging
import time

def sns_notification(tunnel_id, report_key):
    """
    This function is for sending notifications by using SNS.
    """
    try:
        sns_client = boto3.client('sns')
        topic_arn = os.environ.get('SNS_TOPIC_ARN')

        cloudfront_url = os.environ.get('CLOUDFRONT_URL')
        present_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        report_url = f"{cloudfront_url}/report/{report_key}"
        
        subject = "[Emergency Maintenance Notification] Tunnel {tunnel_id} System Maintenance"
        message = f"""
Dear User,

We would like to inform you that an emergency maintenance operation has been scheduled for Tunnel XX.
The maintenance details are as follows:

- Start Time: {present_time} (UTC+8)
- Impact: During this period, access to Tunnel {tunnel_id} services may be temporarily interrupted or experience instability.

For more information, please refer to the maintenance status page:
👉 {report_url}

We apologize for any inconvenience and appreciate your understanding.

Best regards,
Operations Team
        """

        # send SNS notification
        response = sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )

        logging.info("SNS Notification sent successfully.")
        logging.info("Response: %s", response)
        logging.info("Message ID: %s", response['MessageId'])
        
        return {
            'statusCode': 200,
            'body': json.dumps('Notification sent successfully!')
        }
    except Exception as e:
        print(f"Error sending notification: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to send notification')
        }

def lambda_handler(event, context):
    """
    Lambda function entry point.
    """
    try:
        tunnel_id = event.get('tunnel_id')
        report_key = event.get('object_key')
        if not tunnel_id or not report_key:
            return {
                'statusCode': 400,
                'body': json.dumps('Missing tunnel_id or object_key in the event')
            }
        # Call the SNS notification function
        return sns_notification(tunnel_id, report_key)
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing the event')
        }