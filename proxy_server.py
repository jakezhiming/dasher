#!/usr/bin/env python3
"""
OpenAI API Proxy Server for Dasher Game

This script creates a simple proxy server that forwards requests to the OpenAI API
and handles CORS headers. This is useful for testing the web version of the game
locally or deploying it to a server where you want to avoid CORS issues.

Usage:
    python proxy_server.py [--port PORT] [--host HOST] [--log-file LOG_FILE]

Requirements:
    - quart
    - quart-cors
    - httpx
"""

import os
import argparse
import logging
import time
import asyncio
from datetime import datetime
import httpx
from quart import Quart, request, jsonify
from quart_cors import cors

# Create Quart app (async Flask alternative)
app = Quart(__name__)
app = cors(app)  # Enable CORS for all routes

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('openai_proxy')

# Get API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found in environment variables")
    logger.warning("Proxy server will not work without an API key")

# Simple rate limiting
request_timestamps = []
MAX_REQUESTS_PER_MINUTE = 60  # Adjust based on your OpenAI plan

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
    """Proxy requests to OpenAI API asynchronously"""
    if not OPENAI_API_KEY:
        logger.error("API key not configured on server")
        return jsonify({"error": "API key not configured on server"}), 500
    
    # Check rate limit
    if not check_rate_limit():
        logger.warning("Rate limit exceeded")
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
    
    # Get request data
    data = await request.get_json()
    client_ip = request.remote_addr
    
    # Log the request (without sensitive data)
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
                timeout=30  # Add timeout to prevent hanging requests
            )
        
        # Log the response status
        logger.info(f"OpenAI API response: {response.status_code}")
        
        # Return the response from OpenAI
        return response.json(), response.status_code
    
    except httpx.TimeoutException:
        logger.error("Request to OpenAI API timed out")
        return jsonify({"error": "Request to OpenAI API timed out"}), 504
    
    except httpx.RequestError as e:
        logger.error(f"Error forwarding request to OpenAI: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['GET'])
async def test():
    """Test endpoint to verify the server is running"""
    return jsonify({
        "status": "ok", 
        "message": "OpenAI proxy server is running (async)",
        "time": datetime.now().isoformat(),
        "api_key_configured": bool(OPENAI_API_KEY)
    })

def setup_file_logging(log_file):
    """Set up file logging if a log file is specified"""
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        logger.info(f"Logging to {log_file}")

def main():
    """Run the proxy server"""
    parser = argparse.ArgumentParser(description="OpenAI API Proxy Server for Dasher Game")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--log-file", type=str, help="Log file to write to")
    args = parser.parse_args()
    
    # Set up file logging if specified
    setup_file_logging(args.log_file)
    
    logger.info(f"Starting async OpenAI proxy server on {args.host}:{args.port}")
    logger.info("Use this server to avoid CORS issues when making OpenAI API calls from the web version")
    logger.info(f"Proxy endpoint: http://{args.host}:{args.port}/api/openai")
    logger.info(f"Test endpoint: http://{args.host}:{args.port}/api/test")
    
    # Run the Quart app with hypercorn
    import hypercorn.asyncio
    from hypercorn.config import Config
    
    config = Config()
    config.bind = [f"{args.host}:{args.port}"]
    asyncio.run(hypercorn.asyncio.serve(app, config))

if __name__ == "__main__":
    main() 