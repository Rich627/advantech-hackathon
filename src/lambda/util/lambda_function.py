import boto3
import json
import os
import logging
from datetime import datetime

# 配置日誌
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 風險級別優先級映射（數字越大優先級越高）
RISK_PRIORITY = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MEDIUM": 3,
    "LOW": 2,
    "NEGLIGIBLE": 1
}

def retrieve_all_issues_from_dynamodb():
    """
    使用 scan 操作從 DynamoDB 獲取所有 issues
    """
    try:
        # 初始化 DynamoDB 資源，明確指定區域
        region = os.environ.get('AWS_REGION', 'us-west-2')
        dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # 從環境變量獲取表名，如果未設置則使用默認值 'issues'
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'issues')
        logger.info(f"掃描 DynamoDB 表: {table_name}")
        
        # 獲取表引用
        table = dynamodb.Table(table_name)
        
        # 使用 scan 操作獲取所有項目
        response = table.scan()
        items = response.get('Items', [])
        logger.info(f"初次掃描獲得 {len(items)} 項")
        
        # 處理分頁情況（如果結果數量很大）
        while 'LastEvaluatedKey' in response:
            logger.info("檢測到分頁，繼續掃描...")
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            new_items = response.get('Items', [])
            logger.info(f"獲取額外的 {len(new_items)} 項")
            items.extend(new_items)
        
        logger.info(f"總共獲取 {len(items)} 項")
        return items
    except Exception as e:
        logger.error(f"獲取 DynamoDB 項目時出錯: {str(e)}")
        # 返回空列表而不是抛出異常
        return []

def sort_issues_by_risk_level(issues):
    """
    按風險級別優先級排序 issues，然後按日期排序（最新的優先）
    """
    try:
        # 按風險級別優先級和日期排序
        sorted_issues = sorted(
            issues, 
            key=lambda x: (
                RISK_PRIORITY.get(x.get('risk_level', ''), 0),  # 風險優先級
                x.get('date', '') or x.get('timestamp', '')     # 日期或時間戳
            ), 
            reverse=True  # 降序排列（高優先級和最新的優先）
        )
        return sorted_issues
    except Exception as e:
        logger.error(f"排序 issues 時出錯: {str(e)}")
        # 如果排序失敗，返回原始列表
        return issues

def lambda_handler(event, context):
    """
    從 DynamoDB 獲取 issues，按風險級別優先級排序，
    並返回適合前端渲染的格式數據
    """
    try:
        logger.info("開始執行 Lambda 獲取 issues")
        
        # 使用成功的 scan 方法獲取所有 issues
        all_issues = retrieve_all_issues_from_dynamodb()
        print(f"util get_all_issues: {all_issues}")
        
        if not all_issues:
            logger.warning("未獲取到 issues 或發生錯誤")
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
        
        # 按風險級別和日期排序所有 issues
        sorted_issues = sort_issues_by_risk_level(all_issues)
        logger.info(f"成功排序 {len(sorted_issues)} 項 issues")
        
        # 構建響應，只需包含必要的標頭
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
        logger.error(f"意外錯誤: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': '服務器錯誤',
                'details': str(e)
            })
        }