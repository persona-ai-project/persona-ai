"""
Singleton boto3 client for Cloudflare R2 object storage.
R2 is S3-compatible so we use the standard boto3 S3 client
pointed at the R2 endpoint.
"""
from __future__ import annotations

import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

# ── configuration ────────────────────────────────────────────────────────────

R2_ENDPOINT    = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY  = os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY  = os.getenv("R2_SECRET_KEY", "")
R2_AUDIO_BUCKET  = os.getenv("R2_AUDIO_BUCKET", "audio-uploads")
R2_INGEST_BUCKET = os.getenv("R2_INGEST_BUCKET", "ingestion-uploads")

# ── singleton client ──────────────────────────────────────────────────────────

_client = None


def get_client():
    """Return the singleton boto3 S3 client pointed at R2."""
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
    return _client


# ── public methods ────────────────────────────────────────────────────────────

def get_presigned_url(
    key: str,
    bucket: str = R2_INGEST_BUCKET,
    expires_in: int = 3600,
    method: str = "get_object",
) -> str:
    """
    Generate a presigned URL for GET or PUT access to an R2 object.

    Args:
        key:        Object key (path) inside the bucket
        bucket:     Bucket name — defaults to ingestion bucket
        expires_in: URL expiry in seconds (default 1 hour)
        method:     'get_object' for download, 'put_object' for upload

    Returns:
        Presigned URL string
    """
    client = get_client()
    url = client.generate_presigned_url(
        method,
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )
    return url


def upload_bytes(
    key: str,
    data: bytes,
    content_type: str = "application/octet-stream",
    bucket: str = R2_INGEST_BUCKET,
) -> str:
    """
    Upload raw bytes directly to R2.

    Args:
        key:          Object key (path) inside the bucket
        data:         Raw bytes to upload
        content_type: MIME type of the content
        bucket:       Bucket name — defaults to ingestion bucket

    Returns:
        Full R2 URL to the uploaded object
    """
    import io
    client = get_client()
    client.upload_fileobj(
        io.BytesIO(data),
        bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return f"{R2_ENDPOINT}/{bucket}/{key}"


def delete_object(key: str, bucket: str = R2_INGEST_BUCKET) -> None:
    """Delete an object from R2."""
    client = get_client()
    client.delete_object(Bucket=bucket, Key=key)


def list_objects(prefix: str = "", bucket: str = R2_INGEST_BUCKET) -> list[str]:
    """List all object keys in a bucket with optional prefix filter."""
    client = get_client()
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [obj["Key"] for obj in response.get("Contents", [])]


def download_bytes(key: str, bucket: str = R2_INGEST_BUCKET) -> bytes:
    """
    Download an object from R2 and return its bytes.

    Args:
        key:    Object key (path) inside the bucket
        bucket: Bucket name — defaults to ingestion bucket

    Returns:
        Raw bytes of the downloaded object
    """
    import io
    client = get_client()
    buffer = io.BytesIO()
    client.download_fileobj(bucket, key, buffer)
    buffer.seek(0)
    return buffer.read()