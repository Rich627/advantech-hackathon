import boto3
import json
import logging
import os
import base64
import io
from datetime import datetime
from uuid import uuid4
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

# 配置日誌
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_pdf_report(data):
    """
    創建 PDF 報告
    
    Parameters:
        data: 包含報告數據的字典
    
    Returns:
        PDF 文件的字節數據
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # 建立內容數組
    elements = []
    
    # 添加標題
    title = Paragraph("設備問題分析報告", styles['Heading1'])
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # 添加報告信息
    report_id = data.get('report_id', str(uuid4()))
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    # 報告基本信息表格
    basic_info = [
        ['報告 ID:', report_id],
        ['日期:', timestamp],
        ['設備:', data.get('equipment', 'N/A')],
        ['部門:', data.get('department', 'N/A')]
    ]
    
    basic_table = Table(basic_info, colWidths=[100, 400])
    basic_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 6)
    ]))
    elements.append(basic_table)
    elements.append(Spacer(1, 20))
    
    # 添加問題描述
    elements.append(Paragraph("問題描述", styles['Heading2']))
    elements.append(Spacer(1, 10))
    issue_text = data.get('issue', 'N/A')
    elements.append(Paragraph(issue_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # 如果有圖片，添加圖片
    if 'image_data' in data:
        try:
            image_data = base64.b64decode(data['image_data'])
            img = Image(io.BytesIO(image_data), width=400, height=300)
            elements.append(Paragraph("設備問題圖片", styles['Heading2']))
            elements.append(Spacer(1, 10))
            elements.append(img)
            elements.append(Spacer(1, 20))
        except Exception as e:
            logger.error(f"Error processing image: {e}")
    
    # 添加分析結果
    elements.append(Paragraph("分析結果", styles['Heading2']))
    elements.append(Spacer(1, 10))
    analysis = data.get('analysis', 'N/A')
    elements.append(Paragraph(analysis, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # 添加建議解決方案
    elements.append(Paragraph("建議解決方案", styles['Heading2']))
    elements.append(Spacer(1, 10))
    solution = data.get('solution', 'N/A')
    elements.append(Paragraph(solution, styles['Normal']))
    
    # 建立 PDF 文件
    doc.build(elements)
    
    # 獲取 PDF 數據
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def upload_to_s3(pdf_data, report_id):
    """
    上傳 PDF 到 S3
    
    Parameters:
        pdf_data: PDF 文件的字節數據
        report_id: 報告 ID
    
    Returns:
        S3 URL
    """
    bucket_name = os.environ.get('REPORT_BUCKET', None)
    if not bucket_name:
        raise ValueError("Missing S3 bucket configuration")
    
    key = f"reports/{report_id}.pdf"
    
    s3_client = boto3.client('s3')
    s3_client.put_object(
        Body=pdf_data,
        Bucket=bucket_name,
        Key=key,
        ContentType='application/pdf'
    )
    
    region = os.environ.get('AWS_REGION', 'us-east-1')
    s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{key}"
    
    return s3_url

def lambda_handler(event, context):
    """
    API Gateway 觸發的 Lambda 函數，用於處理文檔請求並生成報告
    
    Parameters:
        event: API Gateway 事件數據
        context: Lambda 運行時上下文
    
    Returns:
        HTTP 響應
    """
    try:
        logger.info("Received event: %s", json.dumps(event))
        
        # 解析請求體
        # 注意：API Gateway 可能會將 multipart/form-data 請求轉換為 base64 編碼的字符串
        body = event.get('body', '{}')
        is_base64_encoded = event.get('isBase64Encoded', False)
        
        if is_base64_encoded:
            # 如果是 base64 編碼，先解碼
            body = base64.b64decode(body).decode('utf-8')
        
        # 簡單解析 - 注意：在生產環境中，應該使用專門的 multipart/form-data 解析器
        # 這裡假設數據是 JSON 格式
        try:
            data = json.loads(body)
        except:
            # 如果不是 JSON，嘗試解析表單數據
            data = {}
            # 示例處理 - 在實際場景中需要專門的處理邏輯
            if 'equipment' in event.get('multiValueQueryStringParameters', {}):
                data['equipment'] = event['multiValueQueryStringParameters']['equipment'][0]
            if 'issue' in event.get('multiValueQueryStringParameters', {}):
                data['issue'] = event['multiValueQueryStringParameters']['issue'][0]
        
        # 生成報告 ID
        report_id = str(uuid4())
        data['report_id'] = report_id
        
        # 分析問題 - 在實際場景中，這裡會調用 LLM 或其他分析服務
        # 示例分析結果
        data['analysis'] = "根據問題描述，初步判斷為設備校準問題。參數設定不正確導致加工精度不足。"
        data['solution'] = "建議進行系統校準，調整參數設定，並定期維護設備。"
        
        # 創建 PDF 報告
        pdf_data = create_pdf_report(data)
        
        # 上傳到 S3
        pdf_url = upload_to_s3(pdf_data, report_id)
    
        
        # 返回成功響應
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'success': True,
                'report_id': report_id,
                'pdf_url': pdf_url,
                'message': '報告已成功生成'
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'error': f'內部服務器錯誤: {str(e)}'
            })
        } 