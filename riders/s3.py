import logging
import os

import boto3

logger = logging.getLogger(__name__)


def upload_to_s3(local_file_path: str):
    """Upload a local file to the configured S3 bucket."""
    bucket_name = os.getenv("S3_BUCKET_NAME")
    object_name = "uci_riders.json"
    endpoint_url = os.getenv("S3_ENDPOINT_URL")

    logger.info(f"Uploading to S3 bucket '{bucket_name}'...")
    if endpoint_url:
        logger.info(f"  Using custom endpoint: {endpoint_url}")

    s3_config = {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "region_name": os.getenv("AWS_REGION"),
    }
    if endpoint_url:
        s3_config["endpoint_url"] = endpoint_url

    s3 = boto3.client("s3", **s3_config)
    s3.upload_file(local_file_path, bucket_name, object_name)
    logger.info(f"Uploaded {object_name} to S3 bucket '{bucket_name}' successfully")
