from unittest.mock import patch, MagicMock
from lambda_function import lambda_handler


@patch("boto3.client")
def test_lambda_handler(mock_boto_client):
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3

    mock_s3.download_file.return_value = None

    fake_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "fake-bucket"},
                    "object": {"key": "fake-file.pdf"},
                }
            }
        ]
    }
    fake_context = None

    result = lambda_handler(fake_event, fake_context)

    print("✅ Lambda result:", result)
