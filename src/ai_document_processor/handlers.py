"""AWS Lambda handlers for the deployable document pipeline."""

from __future__ import annotations

import base64
import binascii
import json
import os
from pathlib import Path
from datetime import UTC, datetime
from uuid import uuid4

from .aws_helpers import client, resource
from .pipeline import build_payload
from .extractor import extract_text_from_s3


def _json_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _validate_upload(filename: str, content: bytes) -> str:
    safe_name = Path(filename).name
    if safe_name != filename or not safe_name:
        raise ValueError("invalid filename")

    allowed = {
        item.strip().lower()
        for item in os.getenv("ALLOWED_EXTENSIONS", "").split(",")
        if item.strip()
    }
    suffix = Path(safe_name).suffix.lower()
    if allowed and suffix not in allowed:
        raise ValueError("unsupported file type")

    max_bytes = int(os.getenv("MAX_DOCUMENT_BYTES", "5242880"))
    if len(content) > max_bytes:
        raise ValueError("document exceeds size limit")

    return safe_name


def ingest_handler(event: dict, context) -> dict:
    del context
    try:
        body = json.loads(event.get("body") or "{}")
        content = base64.b64decode(body["content"], validate=True)
        filename = _validate_upload(body["filename"], content)
    except (KeyError, ValueError, TypeError, json.JSONDecodeError, binascii.Error):
        return _json_response(400, {"error": "invalid document upload request"})

    document_id = f"doc_{uuid4().hex[:12]}"
    object_key = f"uploads/{document_id}/{filename}"
    bucket = os.environ["RAW_BUCKET_NAME"]

    s3 = client("s3")
    try:
        s3.put_object(Bucket=bucket, Key=object_key, Body=content)
    except Exception as exc:
        print(f"document ingest storage error: {exc}")
        return _json_response(502, {"error": "unable to store document"})

    state_machine_arn = os.environ["STATE_MACHINE_ARN"]
    execution_input = {
        "document_id": document_id,
        "bucket": bucket,
        "object_key": object_key,
        "filename": filename,
        "uploaded_at": datetime.now(UTC).isoformat(),
    }
    try:
        execution = client("stepfunctions").start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(execution_input),
            name=f"{document_id}-{uuid4().hex[:8]}",
        )
    except Exception as exc:
        print(f"document ingest execution error: {exc}")
        return _json_response(502, {"error": "unable to start processing workflow"})
    return _json_response(
        202,
        {
            "document_id": document_id,
            "object_key": object_key,
            "execution_arn": execution["executionArn"],
        },
    )


def parse_handler(event: dict, context) -> dict:
    del context
    text = extract_text_from_s3(event["bucket"], event["object_key"])
    payload = dict(event)
    payload["text"] = text
    return payload


def classify_handler(event: dict, context) -> dict:
    del context
    payload = dict(event)
    analysis = build_payload(event["filename"], event["text"])
    payload["classification"] = analysis["classification"]
    payload["entities"] = analysis["entities"]
    payload["text_preview"] = analysis["text_preview"]
    payload["character_count"] = analysis["character_count"]
    return payload


def route_handler(event: dict, context) -> dict:
    del context
    processed_bucket = os.environ["PROCESSED_BUCKET_NAME"]
    result_key = f"processed/{event['document_id']}.json"
    result_payload = {
        "document_id": event["document_id"],
        "source_file": event["filename"],
        "classification": event["classification"],
        "entities": event["entities"],
        "text_preview": event["text_preview"],
        "character_count": event["character_count"],
        "raw_bucket": event["bucket"],
        "raw_key": event["object_key"],
    }

    client("s3").put_object(
        Bucket=processed_bucket,
        Key=result_key,
        Body=json.dumps(result_payload, indent=2, sort_keys=True).encode(),
        ContentType="application/json",
    )

    table = resource("dynamodb").Table(os.environ["DOCUMENTS_TABLE_NAME"])
    table.put_item(Item=result_payload | {"result_key": result_key})
    return {
        "document_id": event["document_id"],
        "processed_bucket": processed_bucket,
        "result_key": result_key,
    }
