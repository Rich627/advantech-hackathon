import boto3
import json
import os
import logging
from boto3.dynamodb.conditions import Key
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Risk level priority mapping (higher number = higher priority)
RISK_PRIORITY = {
    "High": 3,
    "Medium": 2,
    "Low": 1
}

def parse_timestamp(timestamp_str):
    """
    Parse timestamp string to datetime object for comparison
    
    Parameters:
        timestamp_str: String timestamp in format "YYYY-MM-DD HH:MM:SS"
    Returns:
        datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        # If timestamp is invalid or None, return a very old date for sorting purposes
        logger.warning(f"Invalid timestamp format: {timestamp_str}")
        return datetime(1970, 1, 1)

def retrieve_issues_from_dynamodb():
    """
    Retrieves all issues from DynamoDB.
    """
    try:
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'issues')
        table = dynamodb.Table(table_name)
        
        # Scan the table to get all items
        response = table.scan()
        items = response.get('Items', [])
        
        # Handle pagination if there are more items
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        return items
    except Exception as e:
        logger.error(f"Error retrieving items from DynamoDB: {str(e)}")
        raise

def sort_issues_by_risk_and_time(issues):
    """
    Sorts issues by risk level priority (High > Medium > Low) 
    and then by timestamp (most recent first).
    """
    try:
        # Sort issues based on risk level priority first, then by timestamp
        sorted_issues = sorted(
            issues, 
            key=lambda x: (
                RISK_PRIORITY.get(x.get('risk_level', 'Low'), 0),  # Risk priority
                parse_timestamp(x.get('timestamp', '1970-01-01 00:00:00'))  # Timestamp
            ), 
            reverse=True  # Descending order (highest priority and newest first)
        )
        return sorted_issues
    except Exception as e:
        logger.error(f"Error sorting issues: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Retrieves issues from DynamoDB, sorts them by risk level priority and timestamp,
    and returns the data in a format suitable for frontend rendering.
    """
    try:
        # Get all issues
        all_issues = retrieve_issues_from_dynamodb()
        
        # Filter for valid risk levels only
        valid_risk_levels = ['Low', 'Medium', 'High']
        filtered_issues = [issue for issue in all_issues if issue.get('risk_level') in valid_risk_levels]
        
        # Sort all issues by risk level and timestamp
        sorted_issues = sort_issues_by_risk_and_time(filtered_issues)
        
        # Add CORS headers for frontend access
        headers = {
            'Access-Control-Allow-Origin': '*',  # Update this to match your frontend domain
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        }
        
        # Construct response
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'issues': sorted_issues,
                'count': len(sorted_issues)
            }, default=str)  # Use default=str to handle non-serializable objects
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',  # Update this to match your frontend domain
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Server error',
                'details': str(e)
            })
        }