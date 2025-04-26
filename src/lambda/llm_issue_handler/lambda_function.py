import base64
import json
import logging
import os
import time
from decimal import Decimal

import boto3
import botocore
import requests
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.embeddings import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate
from langchain.vectorstores import OpenSearchVectorSearch

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
        image_url = data.get('image_url', '')
    
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
            
            # Download from S3
            s3_client = boto3.client('s3')
            response = s3_client.get_object(Bucket=bucket, Key=key)
            image_content = response['Body'].read()
        else:
            # Download from HTTP URL
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image_content = response.content
        
        # Convert to base64
        base64_image = base64.b64encode(image_content).decode('utf-8')
        return base64_image
    except Exception as e:
        logger.error(f"Error getting image from URL {image_url}: {e}")
        return None

def initialize_multimodal_rag_chain(image_url=None):
    """
    Initialize the RAG chain using Langchain with Bedrock multimodal components
    Parameters:
        image_url: Optional URL of the image to analyze
    Returns:
        Configured RAG chain and functions to call multimodal model
    """
    try:
        # Initialize Bedrock client
        bedrock_client = boto3.client('bedrock-runtime')
        
        # Initialize Claude LLM
        llm = Bedrock(
            client=bedrock_client,
            model_id=os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0'),
            model_kwargs={"temperature": 0.1, "max_tokens_to_sample": 2000}
        )
        
        # Initialize Bedrock embeddings
        embeddings = BedrockEmbeddings(
            client=bedrock_client,
            model_id=os.environ.get('BEDROCK_EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v2:0')
        )
        
        # Initialize OpenSearch vector store
        opensearch_url = os.environ.get('OPENSEARCH_ENDPOINT')
        vectorstore = OpenSearchVectorSearch(
            opensearch_url=opensearch_url,
            index_name="icam-vectors",
            embedding_function=embeddings,
            vectorstore_kwargs={
                "engine": "faiss",
                "mapping": {
                    "properties": {
                        "report_id": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "vectors": {"type": "knn_vector", "dimension": 1024}
                    }
                }
            }
        )
        
        # Create prompt template with focus on risk assessment and recommended action
        prompt_template = """
        你是一個專門分析混凝土裂縫問題的專家系統。

        以下是從知識庫中找到的相關資訊：
        {context}

        現在請分析這個問題：{question}

        請只提供以下兩項資訊：
        1. 風險評估：評估此裂縫的風險等級（請明確標明是 "Low"、"Medium" 或 "High"），並簡短解釋評估理由。
        2. 建議處理方式：提供具體的修復或處理建議。

        請根據裂縫類型、位置、長度和寬度，並參考知識庫資訊進行專業判斷。
        """
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(
                search_kwargs={
                    "k": 3,
                    "return_metadata": True,
                    "filter": None  # Can be used later for filtering by report_id
                }
            ),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True  # This allows you to access the source documents with metadata
        )
        
        # Define function to call multimodal model if image is available
        def call_multimodal_model(text_query, image_url):
            try:
                if not image_url:
                    return None
                
                # Get base64 encoded image
                base64_image = get_image_from_url(image_url)
                if not base64_image:
                    return None
                
                # Define multimodal prompt
                multimodal_prompt = f"""
                你是一個專門分析混凝土裂縫問題的專家系統。你有能力分析圖片中的裂縫狀況。

                請仔細觀察提供的圖片，分析裂縫的嚴重程度和特性。

                以下是這個裂縫問題的基本資訊：
                {text_query}

                根據以上資訊和圖片中裂縫的實際情況，請提供：

                1. 風險評估：評估此裂縫的風險等級（請明確標明是 "Low"、"Medium" 或 "High"）。
                2. 建議處理方式：提供具體的修復或處理建議。

                請專注在風險評估和處理建議上，不需要提供其他分析。
                """
                
                # Prepare request payload for Claude 3.5 Sonnet Vision
                payload = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": multimodal_prompt
                                },
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": base64_image
                                    }
                                }
                            ]
                        }
                    ]
                }
                
                # Claude 3 Sonnet Vision model
                vision_model_id = os.environ.get('BEDROCK_VISION_MODEL_ID', 'amazon.nova-pro-v1:0')
                
                # Call Bedrock Runtime
                response = bedrock_client.invoke_model(
                    modelId=vision_model_id,
                    body=json.dumps(payload)
                )
                
                # Parse response
                response_body = json.loads(response.get('body').read())
                return response_body.get('content')[0].get('text')
            except Exception as e:
                logger.error(f"Error calling multimodal model: {e}")
                return None
        
        return qa_chain, call_multimodal_model
    except Exception as e:
        logger.error(f"Error initializing RAG chain: {e}")
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
    to call Bedrock model for generating solution with knowledge base using Langchain RAG.
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
        image_url = raw_data.get('image_url', '')
        
        # Initialize and run RAG chain with multimodal capability
        logger.info("Initializing RAG chain with multimodal support")
        rag_chain, call_multimodal_model = initialize_multimodal_rag_chain()
        
        # Run text-based RAG with metadata handling
        logger.info("Running query through text-based RAG chain")
        
        # Use run_manager to access source documents with metadata
        rag_result = rag_chain({"query": formatted_metadata})
        text_solution = rag_result.get("result", "")
        
        # Extract source documents and their metadata (including report_ids)
        source_docs = rag_result.get("source_documents", [])
        source_report_ids = []
        
        for doc in source_docs:
            if hasattr(doc, "metadata") and "report_id" in doc.metadata:
                source_report_ids.append(doc.metadata["report_id"])
        
        logger.info(f"Retrieved documents with report_ids: {source_report_ids}")
        
        # Add source report IDs to raw_data for future reference 
        raw_data['reference_report_ids'] = source_report_ids
        
        logger.info(f"Text-based RAG solution generated: {text_solution[:100]}...")
        
        # Run multimodal analysis if image is available
        multimodal_solution = None
        if image_url:
            logger.info(f"Running multimodal analysis on image: {image_url}")
            multimodal_solution = call_multimodal_model(formatted_metadata, image_url)
            if multimodal_solution:
                logger.info(f"Multimodal solution generated: {multimodal_solution[:100]}...")
            else:
                logger.warning("Failed to generate multimodal solution, falling back to text-based solution")
        
        # Store in DynamoDB using the raw data extracted from JSON
        logger.info("Storing data in DynamoDB")
        
        # Validate and format data with both solutions
        formatted_data = validate_and_format_data(raw_data, text_solution, multimodal_solution)
        
        # Add reference_report_ids to the formatted data for DynamoDB
        if source_report_ids:
            formatted_data['reference_report_ids'] = source_report_ids
        
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
                'reference_report_ids': source_report_ids
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