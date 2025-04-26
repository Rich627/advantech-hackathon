import boto3
import json
import os
import logging
from boto3.dynamodb.conditions import Key

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Risk level priority mapping (higher number = higher priority)
RISK_PRIORITY = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MEDIUM": 3,
    "LOW": 2,
    "NEGLIGIBLE": 1
}

def retrieve_issues_from_dynamodb(risk_level):
    """
    Retrieves issues from DynamoDB based on the risk level.
    """
    try:
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'issues')
        table = dynamodb.Table(table_name)
        
        # get dynamodb items based on risk level, it will not be sorted by risk level
        # but we will sort it in the next step
        response = table.query(
            IndexName='RiskLevelIndex',
            KeyConditionExpression=Key('risk_level').eq(risk_level)
        )
        
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

def sort_issues_by_risk_level(issues):
    """
    Sorts issues by risk level priority and then by date (most recent first).
    """
    try:
        # Sort issues based on the risk level priority first, then by date
        sorted_issues = sorted(issues, 
                              key=lambda x: (RISK_PRIORITY.get(x['risk_level'], 0), x.get('date', '')), 
                              reverse=True)
        return sorted_issues
    except Exception as e:
        logger.error(f"Error sorting issues: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Retrieves issues from DynamoDB, sorts them by risk level priority,
    and returns the data in a format suitable for frontend rendering.
    """
    try:
        # Collect all issues from different risk levels
        all_issues = []
        for risk_level in RISK_PRIORITY.keys():
            issues = retrieve_issues_from_dynamodb(risk_level)
            all_issues.extend(issues)
        
        # Sort all issues by risk level and date
        sorted_issues = sort_issues_by_risk_level(all_issues)
        
        # Add CORS headers for frontend access
        headers = {
            'Access-Control-Allow-Origin': 'http://localhost:5173',
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
            })
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': 'http://localhost:5173',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Server error',
                'details': str(e)
            })
        }