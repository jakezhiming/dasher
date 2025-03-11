import os
import random
import json
import asyncio
from logger import get_module_logger

logger = get_module_logger('llm_message_handler')

# Try to import OpenAI for desktop version
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
    logger.debug("Using desktop OpenAI")
except ImportError:
    OPENAI_AVAILABLE = False

# Try to detect web environment
try:
    from js import window
    IS_WEB = True
    logger.info("Web environment detected via js.window")
except ImportError as e:
    IS_WEB = False

from constants.messages import PERSONALITIES

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PROXY_URL = os.getenv("OPENAI_PROXY_URL", "")

class LLMMessageHandler:
    def __init__(self):
        # Initialize OpenAI client
        self.client = None
        self.api_key = OPENAI_API_KEY
        self.proxy_url = PROXY_URL

        # For web compatibility with Pygbag
        if not OPENAI_AVAILABLE and not IS_WEB:
            logger.error("Not detected to be running in desktop or web mode - LLM features disabled")
        elif IS_WEB:
            if self.proxy_url:
                logger.info(f"Running in web mode - Use proxy server at {self.proxy_url}")
            else:
                logger.warning("No proxy URL configured - LLM features disabled")
        else:
            # Desktop mode with OpenAI Python SDK
            if self.api_key:
                self.client = AsyncOpenAI(api_key=self.api_key)
                logger.info("Running in desktop mode - OpenAI client initialized")
            else:
                logger.warning("No OpenAI API key provided - LLM features disabled")
        
        # Choose a random personality at startup
        if self.is_available():
            self.personality = random.choice(PERSONALITIES)
        else:
            self.personality = None
        logger.info(f"Starting with personality: {self.personality}")
        
        # For storing the streaming response
        self.current_message = ""
        self.is_streaming = False
        
        # Initialize conversation history
        self.conversation_history = []
        logger.info("Conversation history initialized")
    
    def is_available(self):
        """Check if the LLM service is available"""
        return (self.client is not None) or (IS_WEB and self.proxy_url)
    
    def reset_conversation_history(self):
        """Reset the conversation history for a new game"""
        self.conversation_history = []
        logger.info("Conversation history reset for new game")
    
    def add_to_conversation_history(self, original_message, rephrased_message):
        """Add a message pair to the conversation history"""
        self.conversation_history.append({
            "original": original_message,
            "rephrased": rephrased_message
        })
        # Keep history to a reasonable size (last 10 messages)
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)
    
    async def get_streaming_response(self, original_message, timeout=5):
        """Get the LLM response as a complete string"""
        if not self.is_available():
            return original_message
        
        try:
            self.is_streaming = True
            self.current_message = ""
            
            # Create the conversation history context
            history_context = ""
            if self.conversation_history:
                history_context = "Previous messages shown in the game:\n"
                for i, msg in enumerate(self.conversation_history):
                    history_context += f"{i+1}. Original: \"{msg['original']}\", Rephrased: \"{msg['rephrased']}\"\n"
                history_context += "\n"
            
            prompt = f"""Rephrase the following message in the style of a {self.personality}. 
Keep it very short (within one sentence if possible) and game-appropriate.
Do not use any emojis or special characters.

{history_context}Current message: "{original_message}" """
            
            if IS_WEB:
                # Use Pyodide's js fetch for web version
                try:
                    rephrased_message = await asyncio.wait_for(self._fetch_openai_web(prompt), timeout)
                    # Add to conversation history
                    self.add_to_conversation_history(original_message, rephrased_message)
                    return rephrased_message
                except asyncio.TimeoutError:
                    logger.error(f"API call timed out after {timeout} seconds")
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
                    
                    # Add to conversation history
                    self.add_to_conversation_history(original_message, complete_message)
                    
                    return complete_message
                except asyncio.TimeoutError:
                    logger.error(f"API call timed out after {timeout} seconds. Switch to default messages.")
                    self.client = None
                    return original_message
            
        except Exception as e:
            logger.error(f"Error in LLM API call: {e}. Switch to default messages.")
            self.client = None
            return original_message
        finally:
            self.is_streaming = False
    
    async def _fetch_openai_web(self, prompt, timeout=5):
        """Use JavaScript's fetch to call OpenAI API in web environment"""
        try:
            # Check if proxy URL is configured
            if not self.proxy_url:
                logger.error("No proxy URL configured for web API calls")
                return prompt
            
            # Prepare the request payload
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
                "temperature": 0.5
            }
            
            # Use the proxy server URL
            url = self.proxy_url
            
            # Set up the request parameters for JavaScript
            try:
                # Convert the payload to a JSON string
                payload_json = json.dumps(payload)
                
                # Call the JavaScript function to make the API request
                # This assumes you have a JavaScript function called fetchLLMResponse
                # that takes the URL, payload, and handles the API call
                window.fetchLLMResponse(url, payload_json)
                
                # Wait for the response from JavaScript
                llm_response = None
                for _ in range(50):  # Poll for up to 5 seconds (50 * 0.1)
                    await asyncio.sleep(0.1)
                    if hasattr(window, 'llmResponse'):
                        llm_response = window.llmResponse
                        # Clear it after use
                        del window.llmResponse
                        break
                
                if llm_response is None:
                    logger.error("No response received from JavaScript after timeout")
                    return prompt
                
                logger.info(f"Received response from JavaScript: {llm_response[:50]}...")
                
                # Process the response
                try:
                    # Check if the response is already a string or needs parsing
                    if isinstance(llm_response, str):
                        # Try to parse it as JSON if it looks like JSON
                        if llm_response.startswith('{') and llm_response.endswith('}'):
                            try:
                                response_json = json.loads(llm_response)
                                # Extract the message from the JSON response
                                if "choices" in response_json:
                                    if "message" in response_json["choices"][0]:
                                        message = response_json["choices"][0]["message"]["content"].strip()
                                    else:
                                        # Handle streaming response format
                                        message = response_json["choices"][0]["text"].strip()
                                else:
                                    # If it's not in the expected format, use the raw response
                                    message = llm_response
                            except json.JSONDecodeError:
                                # If it's not valid JSON, use the raw response
                                message = llm_response
                        else:
                            # If it doesn't look like JSON, use the raw response
                            message = llm_response
                    else:
                        # If it's not a string, convert it to one
                        message = str(llm_response)
                    
                    # Remove quotes if present
                    if message.startswith('"') and message.endswith('"'):
                        message = message[1:-1].strip()
                    
                    self.current_message = message
                    logger.info(f"Successfully processed web API response: '{message}'")
                    return message
                except Exception as e:
                    logger.error(f"Error processing JavaScript response: {e}")
                    return prompt
                
            except Exception as e:
                logger.error(f"Error calling JavaScript function: {e}")
                return prompt
            
        except Exception as e:
            logger.error(f"Error in web API call: {e}")
            return prompt
    
    def get_current_personality(self):
        """Return the current personality being used"""
        return self.personality
    
    def change_personality(self):
        """Change to a different random personality"""
        # Only change personality if LLM service is available
        if not self.is_available():
            logger.info("LLM service not available - personality change skipped")
            return self.personality
            
        new_personality = random.choice([p for p in PERSONALITIES if p != self.personality])
        self.personality = new_personality
        return self.personality

    async def process_message(self, original_message, timeout=2):
        """Process a message and return the response."""
        return await self.get_streaming_response(original_message, timeout) 