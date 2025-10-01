"""Test API endpoint to verify Vercel routing."""

import json


def handler(request):
    """Simple test handler."""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "message": "API is working!",
            "timestamp": "2025-01-27T00:00:00Z"
        })
    }
