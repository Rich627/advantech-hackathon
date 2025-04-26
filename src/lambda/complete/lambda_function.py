import boto3
import json
import logging
import os
import time
from datetime import datetime

# 配置日誌
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    API Gateway 觸發的 Lambda 函數，用於完成工單處理
    
    Parameters:
        event: API Gateway 事件數據
        context: Lambda 運行時上下文
    
    Returns:
        HTTP 響應
    """
    try:
        logger.info("Received event: %s", json.dumps(event))
        
        # 解析請求體
        body = json.loads(event.get('body', '{}'))
        
        # 獲取工單 ID 和狀態
        task_id = body.get('task_id')
        status = body.get('status')
        comments = body.get('comments', '')
        
        if not task_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                },
                'body': json.dumps({
                    'error': '缺少工單 ID'
                })
            }
        
        # 更新 DynamoDB 中的工單狀態
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ.get('TASK_TABLE', 'equipment_tasks'))
        
        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_attribute_names = {
            '#status': 'status'
        }
        expression_attribute_values = {
            ':status': status,
            ':updated_at': datetime.now().isoformat()
        }
        
        if comments:
            update_expression += ", comments = :comments"
            expression_attribute_values[':comments'] = comments
        
        # 更新 DynamoDB 項目
        response = table.update_item(
            Key={
                'id': task_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW"
        )
        
        # 如果狀態為已完成（completed），則調用通知 Lambda
        if status == 'completed':
            # 使用 boto3 調用 SNS 通知 Lambda
            lambda_client = boto3.client('lambda')
            lambda_client.invoke(
                FunctionName=os.environ.get('SNS_HANDLER_FUNCTION', 'notify_employee'),
                InvocationType='Event',  # 異步調用
                Payload=json.dumps({
                    'task_id': task_id,
                    'status': status,
                    'message': f'工單 {task_id} 已完成處理。'
                })
            )
        
        # 返回成功響應
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'success': True,
                'message': f'工單 {task_id} 已更新',
                'task': response.get('Attributes', {})
            })
        }
        
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'error': f'內部服務器錯誤: {str(e)}'
            })
        } 