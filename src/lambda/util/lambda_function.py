import boto3
import json
import os
import logging
from datetime import datetime

# 配置日誌
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 初始化 DynamoDB 資源，明確指定區域
region = os.environ.get('AWS_REGION', 'us-west-2')
dynamodb = boto3.resource('dynamodb', region_name=region)

# 風險級別優先級映射（數值越大優先級越高）
RISK_PRIORITY = {
    "High": 3,
    "Medium": 2,
    "Low": 1
}

def parse_timestamp(timestamp_str):
    """
    解析時間戳字符串為 datetime 對象以進行比較
    
    Parameters:
        timestamp_str: 格式為 "YYYY-MM-DD HH:MM:SS" 的時間戳字符串
    Returns:
        datetime 對象，如果解析失敗則返回 None
    """
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        # 如果時間戳無效或為 None，則返回一個很早的日期用於排序
        logger.warning(f"無效的時間戳格式: {timestamp_str}")
        return datetime(1970, 1, 1)

def retrieve_issues_from_dynamodb():
    """
    從 DynamoDB 獲取所有 issues
    """
    try:
        # 從環境變數獲取表名，如果未設置則使用默認值 'issues'
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'issues')
        logger.info(f"Scanning DynamoDB table: {table_name} in region: {region}")
        
        # 獲取表引用
        table = dynamodb.Table(table_name)
        
        # 掃描表以獲取所有項目
        response = table.scan()
        items = response.get('Items', [])
        logger.info(f"Retrieved {len(items)} items from initial scan")
        
        # 處理分頁（如果有更多項目）
        while 'LastEvaluatedKey' in response:
            logger.info("Pagination detected, continuing scan...")
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            batch = response.get('Items', [])
            logger.info(f"Retrieved {len(batch)} additional items")
            items.extend(batch)
        
        logger.info(f"Total items retrieved: {len(items)}")
        return items
    except Exception as e:
        logger.error(f"Error retrieving items from DynamoDB: {str(e)}")
        # 返回空列表而不是抛出異常
        return []

def sort_issues_by_risk_and_time(issues):
    """
    按風險級別優先級（High > Medium > Low）
    然後按時間戳（最近的優先）對 issues 排序
    """
    try:
        # 首先按風險級別優先級，然後按時間戳對 issues 排序
        sorted_issues = sorted(
            issues, 
            key=lambda x: (
                RISK_PRIORITY.get(x.get('risk_level', 'Low'), 0),  # 風險優先級
                parse_timestamp(x.get('timestamp', '1970-01-01 00:00:00'))  # 時間戳
            ), 
            reverse=True  # 降序（最高優先級和最新的優先）
        )
        return sorted_issues
    except Exception as e:
        logger.error(f"Error sorting issues: {str(e)}")
        # 如果排序出錯，返回原始列表
        return issues

def lambda_handler(event, context):
    """
    從 DynamoDB 獲取 issues，按風險級別優先級和時間戳排序，
    並返回適合前端渲染的格式數據
    """
    try:
        logger.info("Starting lambda execution to retrieve issues")
        
        # 獲取所有 issues
        all_issues = retrieve_issues_from_dynamodb()
        
        if not all_issues:
            logger.warning("No issues retrieved or error occurred")
            # 如果沒有找到 issues，返回空列表
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'issues': [],
                    'count': 0
                })
            }
        
        # 過濾有效的風險級別
        valid_risk_levels = ['Low', 'Medium', 'High']
        filtered_issues = [issue for issue in all_issues if issue.get('risk_level') in valid_risk_levels]
        logger.info(f"Filtered to {len(filtered_issues)} issues with valid risk levels")
        
        # 按風險級別和時間戳排序
        sorted_issues = sort_issues_by_risk_and_time(filtered_issues)
        logger.info(f"Successfully sorted {len(sorted_issues)} issues")
        
        # 構建響應
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'issues': sorted_issues,
                'count': len(sorted_issues)
            }, default=str)  # 使用 default=str 處理不可序列化的對象
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Server error',
                'details': str(e)
            })
        }