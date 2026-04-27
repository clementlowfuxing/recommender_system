"""
Invoke an LLM model via AWS Bedrock using a Bearer token (API key).
Usage: python bedrock_invoke.py
"""

import boto3
import json
import os

# ── Config ────────────────────────────────────────────────────────────
REGION = "ap-southeast-1"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
BEARER_TOKEN = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "")  # set in env or paste here

# ── Client ────────────────────────────────────────────────────────────
session = boto3.Session(region_name=REGION)
bedrock = session.client(
    service_name="bedrock-runtime",
    region_name=REGION,
    endpoint_url=f"https://bedrock-runtime.{REGION}.amazonaws.com",
    # If using bearer token instead of IAM credentials:
    # boto3 doesn't natively support bearer tokens, so we inject it via headers
)


def invoke_claude(prompt: str, max_tokens: int = 512) -> str:
    """Invoke Claude 3 Haiku via Bedrock Converse API."""
    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        inferenceConfig={
            "maxTokens": max_tokens,
            "temperature": 0.0,
        },
    )
    return response["output"]["message"]["content"][0]["text"]


def invoke_claude_with_bearer(prompt: str, max_tokens: int = 512) -> str:
    """Invoke Claude via Bedrock using a Bearer token (for sandbox environments)."""
    import urllib.request

    url = f"https://bedrock-runtime.{REGION}.amazonaws.com/model/{MODEL_ID}/converse"
    payload = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.0},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {BEARER_TOKEN}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["output"]["message"]["content"][0]["text"]


if __name__ == "__main__":
    prompt = "Explain what AWS Bedrock is in 2 sentences."

    print(f"Model: {MODEL_ID}")
    print(f"Prompt: {prompt}")
    print("-" * 50)

    if BEARER_TOKEN:
        print("Using Bearer token authentication...")
        response = invoke_claude_with_bearer(prompt)
    else:
        print("Using IAM/SSO credentials...")
        response = invoke_claude(prompt)

    print(f"Response:\n{response}")
