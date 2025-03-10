import os
import random
from openai import AsyncOpenAI

# List of personality types for the LLM to use
PERSONALITIES = [
    "pirate",
    "robot",
    "medieval knight", 
    "valley girl",
    "wise old wizard",
    "excited puppy",
    "grumpy cat",
    "superhero",
    "alien visitor",
    "cowboy",
    "ninja",
    "poet",
    "detective",
    "space explorer",
    "time traveler",
    "mad scientist",
    "dragon",
    "ghost",
    "vampire",
    "fairy godparent",
    "surfer dude",
    "game show host",
    "conspiracy theorist",
    "fortune teller",
    "sassy barista",
    "sarcastic friend",
    "drill sergeant",
    "sports commentator",
    "dissapointed parent",
    "annoyed teacher",
    "frustrated cashier",
    "angry customer",
    "weather forecaster",
    "motivational speaker",
    "shakespearean actor",
    "tech support",
    "royal monarch",
    "circus ringmaster"
]

class LLMMessageHandler:
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not found in environment variables")
            print("Game will use original messages without AI rephrasing")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key)
        
        # Choose a random personality at startup
        self.personality = random.choice(PERSONALITIES)
        print(f"Game messages will be in the style of a {self.personality}")
        
        # For storing the streaming response
        self.current_message = ""
        self.is_streaming = False
    
    def is_available(self):
        """Check if the LLM service is available"""
        return self.client is not None
    
    async def get_streaming_response(self, original_message):
        """Get the LLM response as a complete string"""
        if not self.client:
            return original_message
        
        try:
            self.is_streaming = True
            self.current_message = ""
            
            prompt = f"""Rephrase the following message in the style of a {self.personality}. 
            Keep it very short (within one sentence if possible) and game-appropriate:
            
            Message: {original_message}"""
            
            stream = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                max_tokens=100,
                temperature=0.5
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
            
        except Exception as e:
            print(f"Error in LLM API call: {e}")
            return original_message
        finally:
            self.is_streaming = False
    
    def get_current_personality(self):
        """Return the current personality being used"""
        return self.personality
    
    def change_personality(self):
        """Change to a different random personality"""
        new_personality = random.choice([p for p in PERSONALITIES if p != self.personality])
        self.personality = new_personality
        return self.personality 