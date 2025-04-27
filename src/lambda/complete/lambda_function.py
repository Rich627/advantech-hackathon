import boto3
import json
import logging
import os
from datetime import datetime

# 配置日誌
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def delete_issue_from_dynamodb(issue_id):
    """
    使用 DynamoDB 的 delete_item 方法刪除指定 ID 的 issue
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ.get('ISSUES_TABLE', 'issues'))
    
    logger.info(f"嘗試刪除 ID 為 {issue_id} 的 issue")
    
    # 刪除 DynamoDB 中的項目
    response = table.delete_item(
        Key={
            'id': issue_id
        },
        ReturnValues="ALL_OLD"  # 返回被刪除的項目
    )
    
    # 檢查是否成功刪除項目
    deleted_item = response.get('Attributes')
    return deleted_item

def lambda_handler(event, context):
    """
    API Gateway 觸發的 Lambda 函數，用於從 DynamoDB 刪除指定 ID 的 issue
    
    Parameters:
        event: API Gateway 事件數據，包含要刪除的 issue ID
        context: Lambda 運行時上下文
    
    Returns:
        HTTP 響應
    """
    try:
        logger.info("Received event: %s", json.dumps(event))
        
        # 解析請求體
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event.get('body', '{}'))
            except json.JSONDecodeError:
                logger.error("Invalid JSON in request body")
                body = {}
        
        # 嘗試從多個可能的來源獲取 issue ID
        issue_id = None
        
        # 1. 從請求體的 id 或 issue_id 字段獲取
        if 'id' in body:
            issue_id = body.get('id')
        elif 'issue_id' in body:
            issue_id = body.get('issue_id')
        
        # 2. 從路徑參數獲取
        if not issue_id and event.get('pathParameters') and 'id' in event.get('pathParameters', {}):
            issue_id = event['pathParameters']['id']
        
        # 3. 從查詢字符串參數獲取
        if not issue_id and event.get('queryStringParameters') and 'id' in event.get('queryStringParameters', {}):
            issue_id = event['queryStringParameters']['id']
        
        if not issue_id:
            logger.error("Missing issue ID in request")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,DELETE',
                    'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
                },
                'body': json.dumps({
                    'error': '缺少 issue ID',
                    'message': '請提供要刪除的 issue ID'
                })
            }
        
        del_result = delete_issue_from_dynamodb(issue_id)
        logger.info(f"刪除結果: {del_result}")
        
        if del_result:
            logger.info(f"成功刪除 ID 為 {issue_id} 的 issue")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,DELETE',
                    'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
                },
                'body': json.dumps({
                    'success': True,
                    'message': f'ID 為 {issue_id} 的 issue 已成功刪除',
                    'deleted_issue': del_result  # 返回被刪除的項目
                })
            }
        else:
            logger.warning(f"未找到 ID 為 {issue_id} 的 issue")
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,DELETE',
                    'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
                },
                'body': json.dumps({
                    'error': '資源未找到',
                    'message': f'未找到 ID 為 {issue_id} 的 issue'
                })
            }
        
    except Exception as e:
        logger.error(f"刪除 issue 時發生錯誤: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,DELETE',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
            },
            'body': json.dumps({
                'error': '內部服務器錯誤',
                'message': f'刪除 issue 時發生錯誤: {str(e)}'
            })
        }