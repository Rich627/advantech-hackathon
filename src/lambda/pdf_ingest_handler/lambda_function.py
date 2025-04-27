import json
import logging
import os
import tempfile
import time

import boto3
import numpy as np
from opensearchpy import (AWSV4SignerAuth, NotFoundError, OpenSearch,
                          RequestsHttpConnection, helpers)
from pdf_utils import chunk, extract_text

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ==== Initialize external clients ====
s3 = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))

# OpenSearch connection settings
host = "g9eu5n37g2c5goi6ymzh.us-west-2.aoss.amazonaws.com"
region = "us-west-2"
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

MODEL_ID = "amazon.titan-embed-text-v2"
INDEX = "vectors"


def titan_embed(texts: list[str]) -> list[list[float]]:
    body = json.dumps({"inputText": texts})
    resp = bedrock.invoke_model(
        modelId=MODEL_ID, contentType="application/json", body=body
    )
    return [r["embedding"] for r in json.loads(resp["body"].read())["results"]]


def upsert(report_id: str, chunks: list[str], vectors: list[list[float]]):
    try:
        # First try bulk insertion
        actions = (
            {
                "_op_type": "index",
                "_index": INDEX,
                "_id": f"{report_id}_{i}",
                "report_id": report_id,
                "chunk": txt,
                "vectors": vec,
            }
            for i, (txt, vec) in enumerate(zip(chunks, vectors))
        )
        try:
            helpers.bulk(client, actions)
        except Exception as bulk_error:
            logger.warning(f"Bulk insertion failed: {str(bulk_error)}. Trying individual insertions.")
            # Fall back to individual insertions if bulk fails
            for i, (txt, vec) in enumerate(zip(chunks, vectors)):
                doc = {
                    "report_id": report_id,
                    "chunk": txt,
                    "vectors": vec
                }
                response = client.index(
                    index=INDEX,
                    id=f"{report_id}_{i}",
                    body=doc
                )
                logger.debug(f"Inserted document {i} with ID: {response['_id']}")
        
        logger.info(f"Successfully indexed {len(chunks)} chunks for report {report_id}")
    except Exception as e:
        logger.error(f"Error inserting data into OpenSearch: {str(e)}")
        raise


# ==== Lambda handler ====
def lambda_handler(event, context):
    rec = event["Records"][0]
    bucket = rec["s3"]["bucket"]["name"]
    key = rec["s3"]["object"]["key"]
    report_id = os.path.splitext(os.path.basename(key))[0]

    try:
        # Ensure the index exists
        index_exists = client.indices.exists(index=INDEX)
        if not index_exists:
            logger.warning(f"Index '{INDEX}' does not exist, you may need to create it first")

        # Download the PDF file
        tmp = tempfile.mktemp(suffix=".pdf")
        s3.download_file(bucket, key, tmp)

        # Process the PDF
        text = extract_text(tmp)
        chunks = chunk(text)
        vectors = titan_embed(chunks)

        # Upload to OpenSearch
        upsert(report_id, chunks, vectors)
        logger.info("Upserted %s chunks for %s", len(chunks), report_id)
        return {"ok": True, "chunks": len(chunks)}
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return {"ok": False, "error": str(e)}








