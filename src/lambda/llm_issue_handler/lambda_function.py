import base64
import json
import logging
import os
import time
from decimal import Decimal
from urllib.parse import urlparse

import boto3
import botocore
import requests
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_community.chat_models import BedrockChat
from langchain.prompts import PromptTemplate
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import OpenSearchVectorSearch
from opensearchpy import AWSV4SignerAuth, OpenSearch
from opensearchpy.connection.http_requests import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def download_file_from_s3(bucket, key):
    """
    Download file from S3 bucket
    Parameters:
        bucket: S3 bucket name
        key: S3 object key
    Returns:
        Content of the file
    """
    s3_client = boto3.client('s3')
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read()
        return content
    except botocore.exceptions.ClientError as e:
        logger.error(f"Error downloading file: {e}")
        raise

def parse_json_metadata(json_content):
    """
    Parse JSON metadata to extract specific fields
    Parameters:
        json_content: JSON content as string or bytes
    Returns:
        Formatted string with extracted fields
    """
    try:
        if isinstance(json_content, bytes):
            json_content = json_content.decode('utf-8')
        
        data = json.loads(json_content)
        
        # Extract all relevant fields from metadata JSON
        id = data.get('id', f"issue_{int(time.time())}")
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
        length = data.get('length', 0)
        width = data.get('width', 0)
        position = data.get('position', 'mountain')
        material = data.get('material', 'concrete')
        crack_type = data.get('crack_type', 'Longitudinal')
        crack_location = data.get('crack_location', 'A')
        image_url = data.get('url', '')
    
        #TODO 可能要改
        # Format the metadata string for RAG input
        formatted_metadata = (
            f"Issue ID: {id}, Timestamp: {timestamp}, Location: {position}, Material: {material}, "
            f"Crack Location: {crack_location}, Length (cm): {length}, Width (cm): {width}"
        )
        
        # Return both formatted text for RAG and raw data for DynamoDB
        return {
            'formatted_text': formatted_metadata,
            'raw_data': data
        }
    except Exception as e:
        logger.error(f"Error parsing JSON metadata: {e}")
        raise

def get_image_from_url(image_url):
    """
    Gets image from URL or S3 and converts to base64 for multimodal models
    Parameters:
        image_url: URL or S3 URI of the image
    Returns:
        Base64 encoded image
    """
    try:
        if image_url.startswith('s3://'):
            # Parse S3 URI
            parts = image_url.replace('s3://', '').split('/')
            bucket = parts[0]
            key = '/'.join(parts[1:])
            
            logger.info(f"Accessing S3 object: bucket={bucket}, key={key}")
            
            # Download from S3
            s3_client = boto3.client('s3')
            response = s3_client.get_object(Bucket=bucket, Key=key)
            image_content = response['Body'].read()
        else:
            # For HTTPS URLs
            logger.info(f"Downloading image from URL: {image_url}")
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image_content = response.content
        
        # Convert to base64
        base64_image = base64.b64encode(image_content).decode('utf-8')
        logger.info(f"Successfully converted image to base64 ({len(base64_image)} chars)")
        return base64_image
    except Exception as e:
        logger.error(f"Error getting image from URL {image_url}: {e}")
        return None

def initialize_multimodal_rag_chain(image_url=None):
    """
    Initialize both RAG chain for similar case retrieval and Nova Pro for image analysis
    Parameters:
        image_url: Optional URL of the image to analyze
    Returns:
        Tuple containing retriever for similar cases and function to call Nova Pro model
    """
    try:
        # Initialize Bedrock client
        bedrock_client = boto3.client('bedrock-runtime', region_name='us-west-2')
        
        # Initialize Nova Pro model ID
        nova_model_id = os.environ.get('BEDROCK_MODEL_ID', 'amazon.nova-lite-v1:0')
        
        # Initialize Bedrock embeddings
        embeddings = BedrockEmbeddings(
            client=bedrock_client,
            model_id=os.environ.get('BEDROCK_EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v2:0')
        )
        
        # OpenSearch connection settings
        host = "g9eu5n37g2c5goi6ymzh.us-west-2.aoss.amazonaws.com"
        region = "us-west-2"
        service = 'aoss'

        credentials = boto3.Session().get_credentials()

        auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            service,
            session_token=credentials.token  # 一定要加 session token（尤其你是 Lambda）
        )

        client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=auth,  # 這樣就正確
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,  # 這邊不能錯
            pool_maxsize=20,
            timeout=30,
            request_timeout=30
        )
                
        # 建立向量存儲
        vectorstore = OpenSearchVectorSearch(
            opensearch_url=f"https://{host}",
            index_name = "report-vector/vectors",
            embedding_function=embeddings,
            opensearch_client=client
        )
        
        # Get retriever for similar cases
        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 3,  # Return top 3 similar cases
                "return_metadata": True
            }
        )
        
        # Define function to call Nova Pro model
        def call_multimodal_model(text_query, image_url):
            try:
                logger.info(f"Starting multimodal analysis with Nova Pro")
                logger.info(f"Input text query: {text_query}")
                logger.info(f"Input image URL: {image_url}")

                if not image_url:
                    logger.warning("No image URL provided, skipping Nova Pro analysis")
                    return None
                
                # Get base64 encoded image
                logger.info("Converting image to base64")
                base64_image = get_image_from_url(image_url)
                if not base64_image:
                    logger.error("Failed to convert image to base64")
                    return None
                logger.info(f"Successfully converted image to base64 (length: {len(base64_image)})")

                # Prepare Nova Pro prompt
                logger.info("Preparing Nova Pro system prompt and message list")
                system_list = [
                    {
                        "text": """你是一個專門分析混凝土裂縫問題的專家系統。你的任務是仔細觀察提供的圖片和相關資訊，分析裂縫的嚴重程度和特性。

請提供：
1. 風險評估：評估此裂縫的風險等級（請明確標明是 "Low"、"Medium" 或 "High"）。
2. 建議處理方式：提供具體的修復或處理建議。

請專注在風險評估和處理建議上，不需要提供其他分析。"""
                    }
                ]

                message_list = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": f"以下是這個裂縫問題的基本資訊：\n{text_query}",
                                "type": "text"
                            },
                            {
                                "data": base64_image,
                                "type": "image"
                            }
                        ]
                    }
                ]

                # Configure inference parameters
                logger.info("Configuring inference parameters")
                inference_config = {
                    "maxTokens": 2000,
                    "temperature": 0.1,
                    "topP": 0.9,
                    "stopSequences": []
                }

                # Prepare request body
                request_body = {
                    "schemaVersion": "messages-v1",
                    "messages": message_list,
                    "system": system_list,
                    "inferenceConfig": inference_config
                }
                
                logger.info("Prepared request body for Nova Pro")
                
                # Log model ID being used
                nova_model_id = os.environ.get('BEDROCK_MODEL_ID', 'amazon.nova-lite-v1:0')
                logger.info(f"Using Nova Pro model ID: {nova_model_id}")
                
                # Invoke Nova Pro model
                logger.info("Invoking Nova Pro model")
                try:
                    response = bedrock_client.invoke_model(
                        modelId=nova_model_id,
                        body=json.dumps(request_body)
                    )
                    logger.info("Successfully received response from Nova Pro")
                except Exception as e:
                    logger.error(f"Error invoking Nova Pro model: {str(e)}")
                    raise
                
                # Parse response
                try:
                    response_body = json.loads(response.get('body').read())
                    model_response = response_body.get('content')[0].get('text')
                    logger.info(f"Successfully parsed Nova Pro response. Response preview: {model_response[:200]}...")
                    
                    # Log risk level detection
                    if "風險評估" in model_response:
                        risk_matches = {
                            "High": ["High", "高風險", "高"],
                            "Medium": ["Medium", "中風險", "中"],
                            "Low": ["Low", "低風險", "低"]
                        }
                        for level, keywords in risk_matches.items():
                            if any(keyword in model_response for keyword in keywords):
                                logger.info(f"Detected risk level: {level}")
                                break
                    else:
                        logger.warning("Could not detect explicit risk level in response")
                    
                    return model_response
                except Exception as e:
                    logger.error(f"Error parsing Nova Pro response: {str(e)}")
                    logger.error(f"Raw response body: {response.get('body').read()}")
                    raise
                
            except Exception as e:
                logger.error(f"Error in call_multimodal_model: {str(e)}")
                return None
        
        return retriever, call_multimodal_model
    except Exception as e:
        logger.error(f"Error initializing multimodal chain: {e}")
        raise

def validate_and_format_data(issue_data, solution, multimodal_solution=None):
    """
    Validate and format data according to the specified constraints
    Parameters:
        issue_data: Dict containing issue data
        solution: Solution generated by the text-based model
        multimodal_solution: Solution generated by the multimodal model (if available)
    Returns:
        Formatted and validated data
    """
    try:
        # Use multimodal solution if available, otherwise fall back to text-based solution
        solution_text = multimodal_solution if multimodal_solution else solution
        if isinstance(solution_text, str) is False:
            solution_text = json.dumps(solution_text)
        
        # Extract risk level from AI response
        ai_risk_level = None
        if "風險評估" in solution_text:
            if "High" in solution_text or "高風險" in solution_text or "高" in solution_text and "風險" in solution_text:
                ai_risk_level = "High"
            elif "Medium" in solution_text or "中風險" in solution_text or "中" in solution_text and "風險" in solution_text:
                ai_risk_level = "Medium"
            elif "Low" in solution_text or "低風險" in solution_text or "低" in solution_text and "風險" in solution_text:
                ai_risk_level = "Low"
        
        # 從AI回應中提取處理建議
        action = "待處理"
        if "建議處理方式" in solution_text:
            # 直接提取建議處理方式部分
            parts = solution_text.split("建議處理方式")
            if len(parts) > 1:
                action_text = parts[1].strip()
                # 移除可能的標點符號開頭
                if action_text.startswith("：") or action_text.startswith(":"):
                    action_text = action_text[1:].strip()
                # 取第一個句子或段落
                for delimiter in ["。", ".", "\n"]:
                    if delimiter in action_text:
                        action_text = action_text.split(delimiter)[0].strip()
                        break
                action = action_text[:200] if action_text else "待處理"
        
        # 使用 S3 key作為issue_id的基礎 或使用提供的id
        issue_id = issue_data.get('id', '')
        if not issue_id:
            issue_id = issue_data.get('s3_key', '')
            if not issue_id:
                # 生成隨機ID
                timestamp = time.strftime('%Y_%m_%d_%H_%M_%S')
                issue_id = f"issue_{timestamp}"
        
        # 獲取或生成時間戳
        timestamp = issue_data.get('timestamp')
        if not timestamp:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # 取得長度和寬度
        try:
            length = str(float(issue_data.get('length', 0)))
        except (ValueError, TypeError):
            length = "0"
            
        try:
            width = str(float(issue_data.get('width', 0)))
        except (ValueError, TypeError):
            width = "0"
        
        # 獲取位置和材料
        position = issue_data.get('position', 'mountain')
        material = issue_data.get('material', 'concrete')
        
        # 獲取裂縫位置
        crack_location = issue_data.get('crack_location', issue_data.get('location', 'A'))
        
        # 設定風險等級 - 優先使用多模態模型的評估結果
        risk_level = ai_risk_level if ai_risk_level else "Low"
        
        # 獲取圖片URL
        image_url = issue_data.get('image_url', '')
        # 檢查 JSON 中是否有 url 欄位
        if not image_url and 'url' in issue_data:
            image_url = issue_data.get('url', '')
            logger.info(f"使用 JSON 中的 url 欄位作為圖片 URL: {image_url}")
        
        # 獲取工程師
        engineer = issue_data.get('engineer', '張工程師')
        
        # 返回符合要求格式的資料 - 完全對應 sample_metadata.json 的結構
        return {
            'id': issue_id,
            'timestamp': timestamp,
            'length': length,
            'width': width,
            'position': position,
            'material': material,
            'crack_location': crack_location,
            'image_url': image_url,
            'engineer': engineer,
            'risk_level': risk_level,
            'action': action,
        }
    except Exception as e:
        logger.error(f"Error in validate_and_format_data: {e}")
        # 發生錯誤時返回最小有效項目
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        error_id = f"ERROR-{int(time.time())}"
        return {
            'id': error_id,
            'timestamp': timestamp,
            'length': "0",
            'width': "0",
            'position': 'mountain',
            'material': 'concrete',
            'crack_location': 'A',
            'image_url': '',
            'engineer': '張工程師',
            'risk_level': 'Low',
            'action': '待處理'
        }

def store_in_dynamodb(issue_data, solution):
    """
    Store issue data and solution in DynamoDB
    Parameters:
        issue_data: Dict containing issue data
        solution: Solution generated by the model
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'issues'))
        
        # Validate and format data according to constraints
        item = validate_and_format_data(issue_data, solution)
        
        # Convert numeric values to Decimal for DynamoDB compatibility
        if 'length' in item:
            item['length'] = Decimal(str(item['length']))
        if 'width' in item:
            item['width'] = Decimal(str(item['width']))
            
        # Store item in DynamoDB
        table.put_item(Item=item)
        
        logger.info(f"Successfully stored data in DynamoDB: {item['issue_id']}")
        return True
    except Exception as e:
        logger.error(f"Error storing data in DynamoDB: {e}")
        return False


def lambda_handler(event, context):
    """
    When new folder with image & JSON metadata is created in S3, this lambda will be triggered
    to call Nova Pro model for analyzing concrete cracks and find similar cases using RAG.
    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Get message from event triggered by S3
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        logger.info(f"Processing S3 object: bucket={bucket}, key={key}")
        
        # Process the metadata file
        logger.info(f"Downloading and parsing metadata from S3")
        
        # Download and parse JSON metadata
        json_content = download_file_from_s3(bucket, key)
        parsed_data = parse_json_metadata(json_content)
        formatted_metadata = parsed_data['formatted_text']
        raw_data = parsed_data['raw_data']
        
        # 將完整S3 key添加到raw_data中
        raw_data['s3_key'] = key
        logger.info(f"Added S3 key to raw_data: {key}")
        
        logger.info(f"Metadata parsed: {formatted_metadata}")
        
        # Get image URL
        image_url = raw_data.get('url', '')
        if not image_url:
            image_url = raw_data.get('image_url', '')
            
        logger.info(f"Original image URL from JSON: {image_url}")
        
        # 驗證 URL 是否有效
        if not image_url:
            logger.warning("JSON 中沒有提供 image_url 或 url 字段")
        elif not (image_url.startswith('http://') or image_url.startswith('https://') or image_url.startswith('s3://')):
            logger.warning(f"提供的 URL 格式無效: {image_url}")
        
        # 處理 HTTPS S3 URL，將其轉換為 S3 URI 格式
        if image_url.startswith('https://') and 's3.amazonaws.com' in image_url:
            # 針對特定的 bucket 進行處理
            bucket_name = "genai-hackthon-20250426-image-bucket"
            
            # 處理不同格式的 S3 URL
            try:
                # 移除 URL 前面的協議部分
                url_without_protocol = image_url.replace('https://', '')
                
                if f"{bucket_name}.s3.amazonaws.com/" in image_url:
                    # 格式: https://bucket-name.s3.amazonaws.com/key
                    object_key = url_without_protocol.split(f"{bucket_name}.s3.amazonaws.com/")[1]
                elif f"s3.amazonaws.com/{bucket_name}/" in image_url:
                    # 格式: https://s3.amazonaws.com/bucket-name/key
                    object_key = url_without_protocol.split(f"s3.amazonaws.com/{bucket_name}/")[1]
                else:
                    # 嘗試從 URL 中獲取路徑部分
                    parsed_url = urlparse(image_url)
                    path_parts = parsed_url.path.strip('/').split('/')
                    
                    # 檢查路徑中是否包含 bucket_name
                    if bucket_name in path_parts:
                        bucket_index = path_parts.index(bucket_name)
                        if bucket_index < len(path_parts) - 1:
                            # 獲取 bucket 之後的所有路徑作為 object_key
                            object_key = '/'.join(path_parts[bucket_index + 1:])
                        else:
                            object_key = None
                    else:
                        object_key = None
                
                # 如果成功提取了 key，就構建 S3 URI
                if object_key:
                    image_url = f"s3://{bucket_name}/{object_key}"
                    logger.info(f"將 HTTP URL 轉換為 S3 URI 格式: {image_url}")
                else:
                    logger.warning(f"無法從 URL 解析出 object key: {image_url}")
            except Exception as e:
                logger.error(f"解析 S3 URL 時發生錯誤: {e}")
                logger.warning(f"無法解析 URL: {image_url}, 保留原始 URL")
        
        if image_url:
            logger.info(f"最終使用的圖片URL: {image_url}")
        else:
            logger.warning("未找到有效的圖片URL")
        
        # Initialize Nova Pro model and RAG retriever
        logger.info("Initializing Nova Pro model and RAG retriever")
        retriever, call_multimodal_model = initialize_multimodal_rag_chain()
        
        # Find similar cases using RAG
        logger.info("Finding similar cases using RAG")
        try:
            similar_docs = retriever.invoke(formatted_metadata)
            logger.info(f"Successfully retrieved {len(similar_docs)} similar documents")
        except Exception as e:
            logger.error(f"Error retrieving similar documents: {str(e)}")
            similar_docs = []
        
        reference_ids = []
        
        for doc in similar_docs:
            if hasattr(doc, "metadata"):
                # 優先使用 report_id
                if "report_id" in doc.metadata:
                    reference_ids.append(doc.metadata["report_id"])
                    logger.info(f"Found reference report_id: {doc.metadata['report_id']}")
                # 如果沒有 report_id，則嘗試使用 id
                elif "id" in doc.metadata:
                    reference_ids.append(doc.metadata["id"])
                    logger.info(f"Found reference id: {doc.metadata['id']}")
        
        if reference_ids:
            logger.info(f"Found {len(reference_ids)} similar cases with reference IDs: {reference_ids}")
        else:
            logger.warning("No reference IDs found in similar documents")
        
        # Run analysis with Nova Pro
        logger.info("Running analysis with Nova Pro")
        solution = None
        
        if image_url:
            logger.info(f"Analyzing image and metadata with Nova Pro: {image_url}")
            solution = call_multimodal_model(formatted_metadata, image_url)
            if solution:
                logger.info(f"Nova Pro analysis completed: {solution[:100]}...")
            else:
                logger.warning("Failed to generate solution with Nova Pro, using default values")
                solution = "無法分析圖片。建議處理方式：請專業工程師進行現場檢查。風險評估：Medium"
        else:
            logger.warning("No image URL provided, cannot perform analysis")
            solution = "無圖片提供。建議處理方式：請專業工程師進行現場檢查。風險評估：Medium"
        
        # Store in DynamoDB using the raw data and Nova Pro solution
        logger.info("Storing data in DynamoDB")
        
        # Validate and format data
        formatted_data = validate_and_format_data(raw_data, "", solution)
        
        # Add reference IDs to the formatted data
        if reference_ids:
            formatted_data['reference_ids'] = reference_ids
        
        # Convert numeric values to Decimal for DynamoDB compatibility
        if 'length' in formatted_data:
            formatted_data['length'] = Decimal(str(formatted_data['length']))
        if 'width' in formatted_data:
            formatted_data['width'] = Decimal(str(formatted_data['width']))
        
        # Store in DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'issues'))
        table.put_item(Item=formatted_data)
        
        logger.info(f"Data successfully stored in DynamoDB with issue_id: {formatted_data['id']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Analysis completed and data stored successfully',
                'issue_id': formatted_data['id'],
                'reference_ids': reference_ids
            })
        }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Error processing event: {str(e)}"
            })
        }