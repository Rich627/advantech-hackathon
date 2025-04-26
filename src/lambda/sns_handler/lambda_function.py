import json
import boto3
import os
import logging
import time

def sns_notification(crack_location, report_key):
    """
    This function is for sending notifications by using SNS.
    """
    try:
        sns_client = boto3.client('sns')
        topic_arn = os.environ.get('SNS_TOPIC_ARN')

        cloudfront_url = os.environ.get('CLOUDFRONT_URL')
        present_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        report_url = f"{cloudfront_url}/report/{report_key}"
        
        
        subject = f"[MAINTENANCE NOTIFICATION] Tunnel {crack_location}  Maintenance"
        message = f"""
Dear User,

This is to inform you that our automated monitoring systems have detected a structural anomaly (crack formation) in Tunnel {crack_location}. An emergency maintenance operation has been scheduled to address this issue.

MAINTENANCE DETAILS:
• Issue: Structural crack detected
• Location: Section {crack_location}, west-facing wall
• Severity: Requiring immediate attention
• Maintenance Start: {present_time} (UTC+8)
• Expected Duration: 4-6 hours
• Service Impact: Access to affected tunnel section will be restricted; expect detours and delays

SAFETY MEASURES:
Our engineering team has implemented temporary reinforcement measures while a permanent repair solution is being deployed. All safety protocols have been activated.

DETAILED REPORT:
For comprehensive information including structural assessment and repair methodology, please access the full technical report:
→ {report_url}

We appreciate your understanding as we prioritize safety and structural integrity. Please plan your routes accordingly.

Regards,
Infrastructure Safety & Maintenance Division
Emergency Response Team
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