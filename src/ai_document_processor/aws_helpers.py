"""Lazy AWS SDK helpers so local tests work without boto3 installed."""

from __future__ import annotations

import importlib


def client(service_name: str):
    boto3 = importlib.import_module("boto3")
    return boto3.client(service_name)


def resource(service_name: str):
    boto3 = importlib.import_module("boto3")
    return boto3.resource(service_name)
