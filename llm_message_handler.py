import os
import json
import random
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
    from compat import is_web_environment
    IS_WEB = is_web_environment()
    if IS_WEB:
        logger.info("Web environment detected")
    else:
        logger.info("Desktop environment detected")
except ImportError as e:
    IS_WEB = False
    logger.error(f"Failed to import is_web_environment: {e}")

from constants.messages import PERSONALITIES

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_PROXY_URL = os.getenv("OPENAI_PROXY_URL", "")

class LLMMessageHandler:
    def __init__(self):
        # Initialize OpenAI client
        self.client = None
        self.proxy_url = OPENAI_PROXY_URL
        self.is_streaming = False
        self.current_message = ""
        self.conversation_history = []
        
        # Select a random personality
        self.personalities = PERSONALITIES
        self.personality = random.choice(self.personalities)
        logger.info(f"Selected personality: {self.personality}")
        
        # Initialize OpenAI client if available
        if not IS_WEB and OPENAI_AVAILABLE and OPENAI_API_KEY:
            try:
                self.client = AsyncOpenAI(
                    api_key=OPENAI_API_KEY
                )
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        elif IS_WEB:
            # In web environment, we'll use the proxy URL
            logger.info(f"Web environment detected, using proxy URL: {self.proxy_url}")
            # We'll initialize the client when needed
        
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
Do not use any emojis or special characters.
The rephrased messages are shown sequentially for a game, so they should be short and to the point.

{history_context}Current message: "{original_message}" """
            
            if IS_WEB:
                # Use Pyodide's js fetch for web version
                try:
                    complete_message = await asyncio.wait_for(self._fetch_openai_web(prompt, original_message), timeout)
                except asyncio.TimeoutError:
                    logger.error(f"Proxy Server API call timed out after {timeout} seconds")
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
                except asyncio.TimeoutError:
                    logger.error(f"API call timed out after {timeout} seconds. Switch to default messages.")
                    self.client = None
                    return original_message

            complete_message = complete_message.strip()
            if complete_message.startswith('"') and complete_message.endswith('"'):
                complete_message = complete_message[1:-1].strip()

            # Store the complete message
            self.current_message = complete_message
            
            # Add to conversation history
            self.add_to_conversation_history(original_message, complete_message)
            return complete_message

        except Exception as e:
            logger.error(f"Error in LLM API call: {e}. Switch to default messages.")
            self.client = None
            return original_message
        finally:
            self.is_streaming = False
    
    async def _fetch_openai_web(self, prompt, original_message, timeout=5):
        """Use JavaScript's fetch to call OpenAI API in web environment"""
        try:
            from js import window  # Pyodide's interface to JavaScript

            if not hasattr(window, 'fetchLLMResponse'):
                logger.error("fetchLLMResponse is not defined in JavaScript")
                return original_message

            if not callable(window.fetchLLMResponse):
                logger.error(f"fetchLLMResponse exists but is not callable: {window.fetchLLMResponse}")
                return original_message
            
            payload = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
                "temperature": 0.5
            })

            # Call JavaScript function to make the API request
            window.fetchLLMResponse(payload)
            
            # Use asyncio.wait_for to properly enforce the timeout   
            async def wait_for_response():
                while True:
                    if hasattr(window, 'llmResponse'):
                        response = window.llmResponse
                        if response:
                            del window.llmResponse  # Clear it after use
                            return response
                    await asyncio.sleep(0.1)
            
            llm_response = await asyncio.wait_for(wait_for_response(), timeout)
            
            if llm_response:
                logger.info("Successfully received response from Proxy Server")
                return llm_response
                
        except Exception as e:
            logger.error(f"Error making Proxy Server API call: {e}")
            return original_message
    
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