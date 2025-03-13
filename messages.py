import pygame
import asyncio
import threading
from constants.ui import MESSAGE_CHAR_DELAY, DEFAULT_MESSAGE_DELAY, MESSAGE_TRANSITION_DELAY
from llm_message_handler import LLMMessageHandler
from logger import get_module_logger
from compat import is_web_environment
from constants.messages import DEFAULT_MESSAGES

logger = get_module_logger('messages')

class StatusMessageManager:
    def __init__(self):
        self.current_message = ""
        self.target_message = ""
        self.display_index = 0
        self.last_char_time = 0
        self.char_delay = MESSAGE_CHAR_DELAY  # Milliseconds between characters
        self.last_message_time = 0  # Track when the last message was fully displayed
        self.default_message_delay = DEFAULT_MESSAGE_DELAY  # 5 seconds between default messages
        self.default_message_index = 0
        
        # Keep track of the last two messages
        self.previous_message = ""
        self.current_full_message = ""
        
        # Track messages that should only be shown once
        self.shown_messages = set()
        
        # Add a message queue
        self.message_queue = []
        
        # Initialize LLM message handler
        self.llm_handler = LLMMessageHandler()
        
        # Set up asyncio event loop in a separate thread, but only for desktop environment
        self.is_web = is_web_environment()
        if not self.is_web:
            self.loop = asyncio.new_event_loop()
            self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self.thread.start()
        else:
            # In web environment, we'll use the main event loop
            self.loop = None
            logger.info("Web environment detected, using main event loop for messages")
        
        # Add a delay between messages in the queue
        self.message_transition_delay = MESSAGE_TRANSITION_DELAY
        self.message_completed_time = 0  # Track when a message was fully displayed
    
    def _run_event_loop(self):
        """Run the asyncio event loop in a separate thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        
    def set_message(self, message):
        """Add a message to the queue. Doesn't immediately display it."""
        # Check if the message is new and not already in the queue or being displayed
        # Also check against the previous message to prevent immediate repetition
        if (message and 
            message not in self.message_queue and 
            message != self.target_message and 
            message != self.previous_message and
            message != self.current_full_message):
            
            # If LLM is not available, add the message directly to the queue
            if not self.llm_handler.is_available():
                self.message_queue.append(message)
                # If we're not currently displaying a message, show this one immediately
                if not self.target_message:
                    self._load_next_message()
            else:
                # Process the message through LLM
                if self.is_web:
                    # In web environment, we'll create a task in the main event loop
                    # The main loop will handle this task during the next await asyncio.sleep(0)
                    asyncio.create_task(self._process_with_llm(message))
                else:
                    # In desktop environment, use the separate event loop
                    asyncio.run_coroutine_threadsafe(self._process_with_llm(message), self.loop)
    
    async def _process_with_llm(self, original_message):
        """Process the message through LLM"""
        try:
            # Get the complete response as a string instead of streaming chunks
            full_response = await self.llm_handler.get_streaming_response(original_message)

            # Add the response to the queue if it's not a duplicate
            if (full_response and 
                full_response not in self.message_queue and 
                full_response != self.target_message and
                full_response != self.previous_message and
                full_response != self.current_full_message):
                
                self.message_queue.append(full_response)
                
                # If we're not currently displaying a message, show this one immediately
                if not self.target_message:
                    self._load_next_message()
        except Exception as e:
            logger.error(f"Error processing LLM message: {e}")
            # Fall back to original message
            if (original_message not in self.message_queue and
                original_message != self.target_message and
                original_message != self.previous_message and
                original_message != self.current_full_message):
                
                self.message_queue.append(original_message)
                if not self.target_message:
                    self._load_next_message()
    
    def _load_next_message(self):
        """Load the next message from the queue."""
        if not self.message_queue:
            return False
            
        # Save the current message as previous before setting the new one
        if self.current_full_message:
            self.previous_message = self.current_full_message
        
        # Get the next message from the queue
        next_message = self.message_queue.pop(0)
        logger.debug(next_message)

        current_time = pygame.time.get_ticks()
        self.last_message_time = current_time
        self.target_message = next_message
        self.current_full_message = next_message
        
        # Reset display index and timing for the character-by-character animation
        self.display_index = 0
        self.last_char_time = current_time
        
        return True
    
    def update(self):
        """Update the streaming text effect."""
        current_time = pygame.time.get_ticks()
        
        # If we're still streaming the message
        if self.display_index < len(self.target_message):
            if current_time - self.last_char_time > self.char_delay:
                self.display_index += 1
                self.current_message = self.target_message[:self.display_index]
                self.last_char_time = current_time
                
                # If we just finished displaying the message, record the time
                if self.display_index == len(self.target_message):
                    self.last_message_time = current_time
                    self.message_completed_time = current_time
        else:
            # Message is fully displayed
            self.current_message = self.target_message
            
            # If there are messages in the queue, show the next one after the delay
            if self.message_queue and current_time - self.message_completed_time > self.message_transition_delay:
                self._load_next_message()
            
        return self.current_message
    
    def can_show_default_message(self):
        """Check if enough time has passed to show a new default message."""
        current_time = pygame.time.get_ticks()
        
        # Only show default messages if:
        # 1. Enough time has passed since the last message was shown
        # 2. There are no messages in the queue
        # 3. Either we have no current message OR we have a fully displayed message
        return (current_time - self.last_message_time > self.default_message_delay and
                not self.message_queue and
                (not self.target_message or (self.target_message and self.display_index == len(self.target_message))))
    
    def get_previous_message(self):
        """Get the previous message."""
        return self.previous_message
        
    def has_shown_message(self, message_key):
        """Check if a specific message has already been shown."""
        return message_key in self.shown_messages
        
    def mark_message_shown(self, message_key):
        """Mark a message as having been shown"""
        self.shown_messages.add(message_key)
        
    def get_current_personality(self):
        """Get the current LLM personality"""
        if self.llm_handler.is_available():
            return self.llm_handler.get_current_personality()
        return "None"

# Create a global instance of the message manager
message_manager = StatusMessageManager()

def get_status_message():
    """
    Generate a status message based on the current game state.
    """

    # Only show default messages if it's been a while since the last one and no other messages are queued
    if message_manager.can_show_default_message():
        # Get the current default message
        current_default_message = DEFAULT_MESSAGES[message_manager.default_message_index]
        
        # Only set the message if it's different from the current and previous messages
        if (current_default_message != message_manager.current_full_message and 
            current_default_message != message_manager.previous_message):
            # Set the message first
            message_manager.set_message(current_default_message)
            # Then update the last_message_time and increment the default message index
            message_manager.last_message_time = pygame.time.get_ticks()
            # Increment the default message index to cycle through the messages
            message_manager.default_message_index = (message_manager.default_message_index + 1) % 5
    
    # Update and return the current streaming message
    return message_manager.update()