import os
import json
import boto3
import tempfile
import logging
from pdf_utils import extract_text, chunk
from opensearchpy import OpenSearch, helpers

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ==== 初始化外部 client ====
s3 = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))
os_cli = OpenSearch(
    hosts=[{"host": os.getenv("OS_ENDPOINT"), "port": 443}],
    http_auth=("sigv4", ""),  # IAM SigV4，自動簽名
    use_ssl=True,
    verify_certs=True,
    ssl_assert_hostname=False,
)

MODEL_ID = "amazon.titan-embed-text-v2"
INDEX = "repair-reports"


def titan_embed(texts: list[str]) -> list[list[float]]:
    body = json.dumps({"inputText": texts})
    resp = bedrock.invoke_model(
        modelId=MODEL_ID, contentType="application/json", body=body
    )
    return [r["embedding"] for r in json.loads(resp["body"].read())["results"]]


def upsert(report_id: str, chunks: list[str], vectors: list[list[float]]):
    actions = (
        {
            "_op_type": "index",
            "_index": INDEX,
            "_id": f"{report_id}_{i}",
            "report_id": report_id,
            "chunk": txt,
            "vector": vec,
        }
        for i, (txt, vec) in enumerate(zip(chunks, vectors))
    )
    helpers.bulk(os_cli, actions)


# ==== Lambda handler ====
def lambda_handler(event, context):
    rec = event["Records"][0]
    bucket = rec["s3"]["bucket"]["name"]
    key = rec["s3"]["object"]["key"]
    report_id = os.path.splitext(os.path.basename(key))[0]

    tmp = tempfile.mktemp(suffix=".pdf")
    s3.download_file(bucket, key, tmp)

    text = extract_text(tmp)
    chunks = chunk(text)
    vectors = titan_embed(chunks)

    upsert(report_id, chunks, vectors)
    logger.info("Upserted %s chunks for %s", len(chunks), report_id)
    return {"ok": True, "chunks": len(chunks)}
