import os
import random
import json
import asyncio

# Try to import OpenAI for desktop version
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import js module for web version
try:
    import js
    import pyodide
    from pyodide.http import pyfetch
    IS_WEB = True
except ImportError:
    IS_WEB = False

from constants.messages import PERSONALITIES

# Default proxy URL - can be overridden with environment variable
PROXY_URL = os.getenv("OPENAI_PROXY_URL", "http://localhost:5000/api/openai")

class LLMMessageHandler:
    def __init__(self):
        # Initialize OpenAI client
        self.client = None
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.proxy_url = PROXY_URL
        
        # For web compatibility with Pygbag
        if not OPENAI_AVAILABLE and not IS_WEB:
            print("OpenAI module not available and not running in web - LLM features disabled")
        elif IS_WEB:
            print(f"Running in web mode - will use proxy server at {self.proxy_url}")
            # In web mode, we'll use the proxy server
            if not self.api_key and not self.proxy_url:
                print("Warning: Neither API key nor proxy URL available")
                print("Game will use original messages without AI rephrasing")
        else:
            # Desktop mode with OpenAI Python SDK
            if not self.api_key:
                print("Warning: OPENAI_API_KEY not found in environment variables")
                print("Game will use original messages without AI rephrasing")
            else:
                self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Choose a random personality at startup
        self.personality = random.choice(PERSONALITIES)
        
        # For storing the streaming response
        self.current_message = ""
        self.is_streaming = False
    
    def is_available(self):
        """Check if the LLM service is available"""
        return (self.client is not None) or (IS_WEB and (self.api_key or self.proxy_url))
    
    async def get_streaming_response(self, original_message, timeout=2):
        """Get the LLM response as a complete string"""
        if not self.is_available():
            return original_message
        
        try:
            self.is_streaming = True
            self.current_message = ""
            
            prompt = f"""Rephrase the following message in the style of a {self.personality}. 
            Keep it very short (within one sentence if possible) and game-appropriate.
            Do not use any emojis or special characters.
            
            Message: {original_message}"""
            
            if IS_WEB:
                # Use Pyodide's js fetch for web version
                try:
                    return await asyncio.wait_for(self._fetch_openai_web(prompt), timeout)
                except asyncio.TimeoutError:
                    print(f"API call timed out after {timeout} seconds")
                    return original_message
            else:
                # Use OpenAI Python SDK for desktop version
                try:
                    stream = await asyncio.wait_for(
                        self.client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                            stream=True,
                            max_tokens=100,
                            temperature=0.5
                        ), 
                        timeout
                    )
                    
                    # Collect all chunks into a complete message
                    complete_message = ""
                    async for chunk in stream:
                        if chunk.choices[0].delta.content:
                            complete_message += chunk.choices[0].delta.content
                    
                    complete_message = complete_message.strip()
                    if complete_message.startswith('"') and complete_message.endswith('"'):
                        complete_message = complete_message[1:-1].strip()

                    # Store the complete message
                    self.current_message = complete_message
                    return complete_message
                except asyncio.TimeoutError:
                    print(f"API call timed out after {timeout} seconds. Switch to default messages.")
                    self.client = None
                    return original_message
            
        except Exception as e:
            print(f"Error in LLM API call: {e}. Switch to default messages.")
            self.client = None
            return original_message
        finally:
            self.is_streaming = False
    
    async def _fetch_openai_web(self, prompt, timeout=2):
        """Use Pyodide's js fetch to call OpenAI API in web environment"""
        try:
            # Prepare the request payload
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
                "temperature": 0.5
            }
            
            # Determine which endpoint to use
            if self.proxy_url:
                # Use the proxy server
                url = self.proxy_url
                headers = {"Content-Type": "application/json"}
            else:
                # Direct to OpenAI (likely to fail due to CORS)
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
            
            # Make the fetch request using pyfetch with timeout
            response = await pyfetch(
                url,
                method="POST",
                headers=headers,
                body=json.dumps(payload)
            )
            
            if response.status == 200:
                # Add timeout to the JSON parsing operation
                response_json = await asyncio.wait_for(response.json(), timeout)
                # Handle both direct OpenAI response and our proxy response format
                if "choices" in response_json:
                    if "message" in response_json["choices"][0]:
                        message = response_json["choices"][0]["message"]["content"].strip()
                    else:
                        # Handle streaming response format
                        message = response_json["choices"][0]["text"].strip()
                else:
                    # Unexpected response format
                    print(f"Unexpected API response format: {response_json}")
                    return prompt
                
                # Remove quotes if present
                if message.startswith('"') and message.endswith('"'):
                    message = message[1:-1].strip()
                
                self.current_message = message
                return message
            else:
                # Add timeout to the error text retrieval
                error_text = await asyncio.wait_for(response.text(), timeout)
                print(f"API error: {response.status}")
                print(f"Error details: {error_text}")
                self.client = None
                return prompt
                
        except asyncio.TimeoutError:
            print("Timeout occurred during web API operations")
            self.client = None
            return prompt
        except Exception as e:
            print(f"Error in web API call: {e}")
            self.client = None
            return prompt
    
    def get_current_personality(self):
        """Return the current personality being used"""
        return self.personality
    
    def change_personality(self):
        """Change to a different random personality"""
        new_personality = random.choice([p for p in PERSONALITIES if p != self.personality])
        self.personality = new_personality
        return self.personality 