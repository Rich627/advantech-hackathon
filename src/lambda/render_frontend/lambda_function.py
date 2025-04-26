import boto3
import json
import logging
import os
from jinja2 import Template

# 配置日誌
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    API Gateway 觸發的 Lambda 函數，用於渲染前端頁面
    
    Parameters:
        event: API Gateway 事件數據
        context: Lambda 運行時上下文
    
    Returns:
        包含 HTML 內容的 HTTP 響應
    """
    try:
        logger.info("Received event: %s", json.dumps(event))
        
        # 使用 Jinja2 模板渲染 HTML
        html_template = """
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Advantech 設備問題分析系統</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #0066cc;
                }
                .form-group {
                    margin-bottom: 15px;
                }
                label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }
                input, textarea, select {
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }
                button {
                    background-color: #0066cc;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                }
                button:hover {
                    background-color: #004999;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Advantech 設備問題分析系統</h1>
                <form id="problemForm">
                    <div class="form-group">
                        <label for="equipment">設備名稱</label>
                        <input type="text" id="equipment" name="equipment" required>
                    </div>
                    <div class="form-group">
                        <label for="issue">問題描述</label>
                        <textarea id="issue" name="issue" rows="4" required></textarea>
                    </div>
                    <div class="form-group">
                        <label for="department">部門</label>
                        <select id="department" name="department">
                            <option value="manufacturing">製造部</option>
                            <option value="qa">品管部</option>
                            <option value="rd">研發部</option>
                            <option value="it">IT部</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="image">上傳圖片</label>
                        <input type="file" id="image" name="image" accept="image/*">
                    </div>
                    <button type="submit">提交問題</button>
                </form>
                <div id="result" style="margin-top: 20px;"></div>
            </div>
            
            <script>
                document.getElementById('problemForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const formData = new FormData(this);
                    const resultDiv = document.getElementById('result');
                    
                    resultDiv.innerHTML = '<p>處理中，請稍候...</p>';
                    
                    try {
                        const response = await fetch('/process', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok) {
                            resultDiv.innerHTML = `
                                <h2>分析結果</h2>
                                <p>${data.result}</p>
                            `;
                        } else {
                            resultDiv.innerHTML = `<p style="color: red">錯誤: ${data.error}</p>`;
                        }
                    } catch (error) {
                        resultDiv.innerHTML = `<p style="color: red">發生錯誤: ${error.message}</p>`;
                    }
                });
            </script>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render()
        
        # 返回 HTML 內容
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
            },
            'body': html_content
        }
        
    except Exception as e:
        logger.error(f"Error rendering frontend: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'error': f'內部服務器錯誤: {str(e)}'
            })
        } 