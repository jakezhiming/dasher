#!/usr/bin/env python3
"""
OpenAI API Proxy Server for Dasher Game

Usage:
    python proxy_server.py [--port PORT] [--host HOST]
"""

import os
import argparse
import time
import asyncio
import httpx
from quart import Quart, request
from quart_cors import cors
from logger import get_module_logger

logger = get_module_logger('proxy_server')

# Security
CORS_ALLOW_ORIGIN = os.getenv("CORS_ALLOW_ORIGIN", "*")
PROXY_TOKEN = os.getenv("PROXY_TOKEN")

# API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found in environment variables")
    logger.warning("Proxy server will not work without an API key")
    exit()

# Rate limiting
request_timestamps = []
MAX_REQUESTS_PER_MINUTE = int(os.getenv("OPENAI_RATE_LIMIT", "60"))

# Create Quart app
app = Quart(__name__)
app = cors(app, allow_origin=CORS_ALLOW_ORIGIN)

def check_rate_limit():
    """Check if we're exceeding the rate limit"""
    global request_timestamps
    
    current_time = time.time()
    # Remove timestamps older than 1 minute
    request_timestamps = [ts for ts in request_timestamps if current_time - ts < 60]
    
    # Check if we've exceeded the rate limit
    if len(request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
        return False
    
    # Add current timestamp
    request_timestamps.append(current_time)
    return True

@app.route('/api/openai', methods=['POST'])
async def proxy_openai():
    if request.headers.get("X-API-Token") != PROXY_TOKEN:
        return "Unauthorized", 401
    
    # Check rate limit
    if not check_rate_limit():
        logger.warning("Rate limit exceeded")
        return "Rate limit exceeded. Please try again later.", 429
    
    # Get request data
    data = await request.get_json()
    client_ip = request.remote_addr
    
    # Log the request
    logger.info(f"Request from {client_ip} - Model: {data.get('model', 'unknown')}")
    
    # Forward request to OpenAI asynchronously
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                json=data,
                timeout=5
            )
        
        # Log the response status
        logger.info(f"OpenAI API response: {response.status_code} - Message: {response.json().get('choices', [{}])[0].get('message', {}).get('content', 'unknown')}")
        return response.json(), response.status_code
    
    except httpx.TimeoutException:
        logger.error("Request to OpenAI API timed out")
        return "Request to OpenAI API timed out", 504
    
    except httpx.RequestError as e:
        logger.error(f"Error forwarding request to OpenAI: {str(e)}")
        return str(e), 500
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return str(e), 500

def main():
    """Run the proxy server"""
    parser = argparse.ArgumentParser(description="OpenAI API Proxy Server for Dasher Game")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    args = parser.parse_args()
    
    logger.info(f"Starting async OpenAI proxy server on {args.host}:{args.port}")
    logger.info("Use this server to avoid CORS issues when making OpenAI API calls from the web version")
    logger.info(f"CORS configured with allow_origin: {CORS_ALLOW_ORIGIN}")
    logger.info(f"Rate limit configured: {MAX_REQUESTS_PER_MINUTE} requests per minute")
    logger.info(f"Proxy endpoint: http://{args.host}:{args.port}/api/openai")
    
    # Run the Quart app with hypercorn
    import hypercorn.asyncio
    from hypercorn.config import Config
    
    config = Config()
    config.bind = [f"{args.host}:{args.port}"]
    asyncio.run(hypercorn.asyncio.serve(app, config))

if __name__ == "__main__":
    main() 