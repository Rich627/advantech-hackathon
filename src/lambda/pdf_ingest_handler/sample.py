from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth, NotFoundError
import boto3
import numpy as np
import time
import json

# ---- OpenSearch 連線設定 ----
host = 'ho2i2x3rtedkasoik8uj.us-west-2.aoss.amazonaws.com'
region = 'us-west-2'

service = 'aoss'
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region, service)

client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    pool_maxsize=20,
)

try:
    # 索引名稱
    index_name = 'hello'
    
    # ---- 檢查索引是否存在 ----
    index_exists = client.indices.exists(index=index_name)
    print(f"索引 '{index_name}' 存在: {index_exists}")
    
    if not index_exists:
        print("警告：hello 不存在，可能需要先建立索引")
    
    # ---- 生成一個隨機 embedding vector ----
    dimension = 1024  # 更新為與 OpenSearch 上 knn_vector 定義的維度一致
    random_vector = np.random.rand(dimension).tolist()
    
    # ---- 插入 OpenSearch ----
    doc = {
        'vectors': random_vector,
        'report_id': f'test-report-{int(time.time())}'
    }
    
    print("準備插入文檔:", doc.keys())
    
    # 插入文檔
    response = client.index(
        index=index_name,
        body=doc
    )
    
    print("插入響應:", response)
    
    # # 嘗試獲取剛插入的文檔
    # try:
    #     doc_id = response['_id']
    #     print(f"文檔ID: {doc_id}")
        
    #     # 使用get嘗試直接獲取文檔
    #     try:
    #         get_response = client.get(
    #             index=index_name,
    #             id=doc_id
    #         )
    #         print("成功獲取文檔:", get_response['_source'].keys())
    #     except NotFoundError:
    #         print(f"無法通過ID獲取文檔: {doc_id}")
    # except KeyError:
    #     print("響應中沒有找到文檔ID")
    
    # # 使用簡單搜索嘗試找到文檔
    # try:
    #     # 增加延遲以確保數據已被索引
    #     print("等待1秒鐘讓數據被索引...")
    #     time.sleep(1)
        
    #     # 搜尋所有文檔
    #     search_response = client.search(
    #         index=index_name,
    #         body={
    #             'size': 10,
    #             'query': {
    #                 'match_all': {}
    #             }
    #         }
    #     )
        
    #     hits = search_response['hits']['hits']
    #     print(f"找到 {len(hits)} 個文檔:")
    #     for hit in hits:
    #         print(f"ID: {hit['_id']}")
    #         if 'report_id' in hit['_source']:
    #             print(f"報告ID: {hit['_source']['report_id']}")
    #         if 'vectors' in hit['_source']:
    #             vector_sample = hit['_source']['vectors'][:3]
    #             print(f"向量前3個元素: {vector_sample}...")
    #         print("-" * 40)
            
    # except Exception as e:
    #     print(f"搜尋時發生錯誤: {e}")
        
except Exception as e:
    print(f"發生錯誤: {type(e).__name__} - {e}")
    import traceback
    traceback.print_exc()