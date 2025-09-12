import os
import uuid
from datetime import datetime
import boto3
from botocore.client import Config
from app.core.config import settings


_s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    region_name=settings.AWS_DEFAULT_REGION or None,
    config=Config(s3={"addressing_style": "virtual"}),
)


def upload_image_bytes(image_bytes: bytes, topic: str, subtopic: str, content_type: str = "image/png") -> str:
    safe_topic = (topic or "topic").replace(" ", "_")[:60]
    safe_subtopic = (subtopic or "subtopic").replace(" ", "_")[:60]
    key = f"images/{safe_topic}/{safe_subtopic}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}.png"

    _s3.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=image_bytes,
        ContentType=content_type,
    )

    if settings.S3_PUBLIC_BASE:
        return f"{settings.S3_PUBLIC_BASE}/{key}"
    # Fallback to presigned URL for private buckets
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
        ExpiresIn=3600,
    )


