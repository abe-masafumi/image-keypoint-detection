from __future__ import annotations

import boto3


def fetch_s3_object_bytes(
    bucket_name: str,
    object_key: str,
    *,
    aws_profile: str = "",
) -> bytes:
    if aws_profile:
        session = boto3.Session(profile_name=aws_profile)
        client = session.client("s3")
    else:
        client = boto3.client("s3")
    response = client.get_object(Bucket=bucket_name, Key=object_key)
    return response["Body"].read()
