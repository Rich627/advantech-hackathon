import boto3
import json
import logging
import os
from decimal import Decimal

# 配置日誌
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # 將 Decimal 轉換為 float
        return super(DecimalEncoder, self).default(obj)


def retrieve_pdf_s3_url(object_key):
    """
    使用 object_key 從 S3 獲取 PDF 文件
    """
    try:
        # s3 = boto3.client('s3')
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'genai-hackthon-20250426-history-report-bucket')
        folder_name = os.environ.get('S3_FOLDER_NAME', 'reports')
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{folder_name}/{object_key}"
        logger.info(f"PDF S3 URL: {s3_url}")
        return s3_url

        # response = s3.get_object(Bucket=bucket_name, Key=f"{folder_name}/{object_key}")
        # pdf_content = response['Body'].read()
        # return pdf_content
    except Exception as e:
        logger.error(f"Error retrieving PDF from S3: {str(e)}")
        return None

def retrieve_history_report(issue_id):
    """
    Use issue_id to get 3 history reports from DynamoDB
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
        
        # 從環境變量獲取表名，如果未設置則使用默認值 'issues'
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'issues')
        logger.info(f"掃描 DynamoDB 表: {table_name}")
        
        # 獲取表引用
        table = dynamodb.Table(table_name)
        
        # 使用 scan 操作獲取所有項目
        response = table.scan()
        items = response.get('Items', [])
        
        # 過濾出符合條件的歷史報告
        issue_metadata = [item for item in items if item['id'] == issue_id]

        # 選取 reference_ids 欄位的資料 ，如 "issue_2025_04_26_09_29_30,issue_2025_04_26_09_28_30,issue_2025_04_26_09_27_30"
        history_report_ids = issue_metadata[0].get('reference_ids', "") if issue_metadata else ""
        logger.info(f"找到的歷史報告 ID: {history_report_ids}")

        history_report_ids_list = history_report_ids.split(",")
        all_history_report_urls = []
        for report_id in history_report_ids_list:
            # 使用 report_id 獲取報告的 PDF 文件
            pdf_url = retrieve_pdf_s3_url(report_id)
            if pdf_url:
                all_history_report_urls.append(pdf_url)
        
        # 返回找到的歷史報告數據
        return all_history_report_urls
    
    except Exception as e:
        logger.error(f"Error in retrieve_history_report: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
            },
            'body': json.dumps({
                'error': f'獲取歷史報告時出錯: {str(e)}'
            })
        }

def get_all_issues_direct():
    """
    直接從 DynamoDB 獲取所有 issues，不通過 util Lambda
    """
    try:
        # 使用 boto3 直接查詢 DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NAME', 'issues'))
        
        # 使用 scan 操作取得所有項目
        response = table.scan()
        items = response.get('Items', [])
        
        # 處理分頁情況（如果結果數據量大）
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        # 返回處理後的數據
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
            },
            'body': json.dumps({
                'issues': items,
                'count': len(items)
            }, cls=DecimalEncoder)
        }
    except Exception as e:
        logger.error(f"Error in get_all_issues_direct: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
            },
            'body': json.dumps({
                'error': f'獲取 issues 列表時出錯: {str(e)}'
            })
        }
    
def get_all_issues():
    """
    從 util Lambda 獲取所有 issues
    """
    try:
        # 調用 util Lambda 獲取數據
        lambda_client = boto3.client('lambda')
        logger.info(f"Invoking util Lambda function: {os.environ.get('UTIL_FUNCTION_NAME', 'equipment_utils')}")
        
        response = lambda_client.invoke(
            FunctionName=os.environ.get('UTIL_FUNCTION_NAME', 'equipment_utils'),
            InvocationType='RequestResponse',
            Payload=json.dumps({})
        )
        
        # 解析 util Lambda 的響應
        payload = json.loads(response['Payload'].read())
        logger.info(f"Received response from util Lambda: {payload}")
        
        # 檢查響應是否成功
        if payload.get('statusCode') == 200:
            # 從 util Lambda 獲取的數據添加 CORS 標頭
            util_body = json.loads(payload.get('body', '{"issues": [], "count": 0}'))
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
                    'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
                },
                'body': json.dumps({
                
                    'issues': util_body.get('issues', [
                        {"id": "issue_2025_04_26_09_29_30", "timestamp": "2025-04-26 09:29:30", "length": 24, "width": 9, "position": "mountain", "material": "concrete", "crack_type": "Longitudinal", "crack_location": "Z", "image_url": "https://genai-hackthon-20250426-image-bucket.s3.us-west-2.amazonaws.com/issue/issue_2025_04_27_09_02_27.jpg/issue_2025_04_27_09_02_27.jpg.jpg"},
                        {"id": "issue_2025_04_26_09_28_30", "timestamp": "2025-04-26 09:29:30", "length": 24, "width": 9, "position": "mountain", "material": "concrete", "crack_type": "Longitudinal", "crack_location": "Z", "image_url": "https://genai-hackthon-20250426-image-bucket.s3.us-west-2.amazonaws.com/issue/issue_2025_04_27_09_02_27.jpg/issue_2025_04_27_09_02_27.jpg.jpg"},
                        {"id": "issue_2025_04_26_09_27_30", "timestamp": "2025-04-26 09:29:30", "length": 24, "width": 9, "position": "mountain", "material": "concrete", "crack_type": "Longitudinal", "crack_location": "Z", "image_url": "https://genai-hackthon-20250426-image-bucket.s3.us-west-2.amazonaws.com/issue/issue_2025_04_27_09_02_27.jpg/issue_2025_04_27_09_02_27.jpg.jpg"},
                        {"id": "issue_2025_04_26_09_26_30", "timestamp": "2025-04-26 09:29:30", "length": 24, "width": 9, "position": "mountain", "material": "concrete", "crack_type": "Longitudinal", "crack_location": "Z", "image_url": "https://genai-hackthon-20250426-image-bucket.s3.us-west-2.amazonaws.com/issue/issue_2025_04_27_09_02_27.jpg/issue_2025_04_27_09_02_27.jpg.jpg"},
                        {"id": "issue_2025_04_26_09_25_30", "timestamp": "2025-04-26 09:29:30", "length": 24, "width": 9, "position": "mountain", "material": "concrete", "crack_type": "Longitudinal", "crack_location": "Z", "image_url": "https://genai-hackthon-20250426-image-bucket.s3.us-west-2.amazonaws.com/issue/issue_2025_04_27_09_02_27.jpg/issue_2025_04_27_09_02_27.jpg.jpg"},
                        {"id": "issue_2025_04_26_09_24_30", "timestamp": "2025-04-26 09:29:30", "length": 24, "width": 9, "position": "mountain", "material": "concrete", "crack_type": "Longitudinal", "crack_location": "Z", "image_url": "https://genai-hackthon-20250426-image-bucket.s3.us-west-2.amazonaws.com/issue/issue_2025_04_27_09_02_27.jpg/issue_2025_04_27_09_02_27.jpg.jpg"},

                    ]),
                    'count': util_body.get('count', 0)
                })
            }
        else:
            logger.error(f"Error from util Lambda: {payload}")
            logger.info("Falling back to direct DynamoDB query")
            return get_all_issues_direct()  # 如果 util Lambda 失敗，嘗試直接查詢
    except Exception as e:
        logger.error(f"Error in get_all_issues: {str(e)}")
        logger.info("Falling back to direct DynamoDB query due to exception")
        return get_all_issues_direct()  # 如果發生錯誤，嘗試直接查詢

def get_issue_detail(issue_id):
    """
    從 DynamoDB 獲取單個 issue 的詳細信息
    """
    try:
        print(f"get_issue_detail: {issue_id}")
        # 使用 boto3 直接查詢 DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NAME', 'issues'))
        
        response = table.get_item(
            Key={'id': issue_id}
        )
        
        item = response.get('Item')
        
        if item:
            return item
        else:
            return None
        
    except Exception as e:
        logger.error(f"Error in get_issue_detail: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
            },
            'body': json.dumps({
                'error': f'獲取 issue 詳情時出錯: {str(e)}'
            })
        }
    
def lambda_handler(event, context):
    """
    API Gateway 觸發的 Lambda 函數，提供前端數據
    
    Parameters:
        event: API Gateway 事件數據
        context: Lambda 運行時上下文
    
    Returns:
        包含 JSON 數據的 HTTP 響應
    """
    try:
        logger.info("Received event: %s", json.dumps(event))
        
        # 獲取 HTTP 方法
        http_method = event.get('httpMethod', '')
        
        # 對於 API Gateway v2
        if 'requestContext' in event and 'http' in event.get('requestContext', {}):
            http_method = event['requestContext']['http'].get('method', '')
        
        # 處理 OPTIONS 預檢請求
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
                    'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth',
                    'Access-Control-Max-Age': '86400'  # 24小時，減少預檢請求
                },
                'body': json.dumps({})
            }
        
        # 取得路徑參數和查詢參數
        path = event.get('path', '')
        path_parameters = event.get('pathParameters', {})
        query_parameters = event.get('queryStringParameters', {})
        # 從事件對象中獲取 run_id 路徑參數
        
        # 對於 API Gateway v2
        if 'requestContext' in event and 'http' in event.get('requestContext', {}):
            path = event['requestContext']['http'].get('path', '')

        print(f"test")
        
        # 處理路由
        if '/render' in path and not path_parameters:
            # 列表頁面 - 優先使用 util Lambda 獲取所有 issues，如失敗則直接查詢
            print(f"現在是 /path: {path}，沒有 path_parameters")
            all_res = get_all_issues()
            return all_res
        elif '/render/' in path or (path_parameters and 'id' in path_parameters):
            # 從路徑提取 ID
            issue_id = event['pathParameters']['run_id']

            print(f"Path: {path}")
            # issue_id = path_parameters.get('id') if path_parameters else path.split('/render/')[-1]

            history_report_url = retrieve_pdf_s3_url(issue_id)
            issue_detail_info = get_issue_detail(issue_id)

            print(f"issue_detail_info: {issue_detail_info}")
            print(type(issue_detail_info))

            print(f"history_report_url: {history_report_url}")
            print(type(history_report_url))

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
                    'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
                },
                'body': json.dumps({
                    'issue_detail_info': issue_detail_info,
                    'history_report_url': history_report_url
                }, cls=DecimalEncoder)
            }


        else:
            # 其他路由 - 返回錯誤
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
                    'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
                },
                'body': json.dumps({
                    'error': '找不到請求的資源'
                })
            }
        
    except Exception as e:
        logger.error(f"Error in render_frontend: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-gateway-auth'
            },
            'body': json.dumps({
                'error': f'內部服務器錯誤: {str(e)}'
            })
        }