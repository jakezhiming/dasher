from pygame_compat import pygame, is_web_environment
import asyncio
import threading
from constants.ui import MESSAGE_CHAR_DELAY, DEFAULT_MESSAGE_DELAY
from llm_message_handler import LLMMessageHandler
from logger import get_module_logger
import random

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
        
        # Set up asyncio event loop in a separate thread - but only in desktop environment
        self.loop = None
        self.thread = None
        
        try:
            if not is_web_environment():
                # In desktop environment, create a new event loop and run it in a separate thread
                self.loop = asyncio.new_event_loop()
                self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
                self.thread.start()
                logger.info("Started event loop in separate thread (desktop environment)")
            else:
                # In web environment, use the existing event loop
                self.loop = asyncio.get_event_loop()
                logger.info("Using existing event loop (web environment)")
        except Exception as e:
            logger.error(f"Error setting up event loop: {e}")
            # Fallback to a simple implementation without asyncio
            logger.info("Falling back to simple implementation without asyncio")
            self.loop = None
        
        # Add a delay between messages in the queue
        self.message_transition_delay = 500  # 500ms delay between messages
        self.message_completed_time = 0  # Track when a message was fully displayed
        
        # Initialize with a welcome message
        self.set_message("Welcome to Dasher! Use arrow keys to move and SPACE to jump.")
    
    def _run_event_loop(self):
        """Run the asyncio event loop in a separate thread."""
        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"Error in event loop: {e}")
    
    def set_message(self, message):
        """Set a new message to be displayed."""
        if not message:
            return
            
        # Store the current message as the previous message
        if self.current_full_message:
            self.previous_message = self.current_full_message
            
        # Reset the display index for the new message
        self.display_index = 0
        self.last_char_time = pygame.time.get_ticks()
        
        # Process the message with LLM if available
        if self.loop and self.llm_handler.is_available():
            try:
                if is_web_environment():
                    # In web environment, use a different approach
                    asyncio.ensure_future(self._process_with_llm_web(message), loop=self.loop)
                else:
                    # In desktop environment, use run_coroutine_threadsafe
                    if self.loop.is_running():
                        future = asyncio.run_coroutine_threadsafe(self._process_with_llm(message), self.loop)
                        # We don't wait for the result here, it will be processed asynchronously
                    else:
                        # Fallback to direct processing if loop is not running
                        self.target_message = message
            except Exception as e:
                logger.error(f"Error processing message with LLM: {e}")
                # Fallback to direct message setting
                self.target_message = message
        else:
            # If LLM is not available, just set the message directly
            self.target_message = message
    
    async def _process_with_llm(self, original_message):
        """Process a message with the LLM in desktop environment."""
        try:
            processed_message = await self.llm_handler.process_message(original_message)
            # Update the target message with the processed message
            self.target_message = processed_message if processed_message else original_message
        except Exception as e:
            logger.error(f"Error in _process_with_llm: {e}")
            # Fallback to the original message
            self.target_message = original_message
    
    async def _process_with_llm_web(self, original_message):
        """Process a message with the LLM in web environment."""
        try:
            # In web environment, we need to handle this differently
            processed_message = await self.llm_handler.process_message(original_message)
            
            # Update the target message with the processed message
            if processed_message:
                self.target_message = processed_message
            else:
                self.target_message = original_message
        except Exception as e:
            logger.error(f"Error in _process_with_llm_web: {e}")
            # Fallback to the original message
            self.target_message = original_message
    
    def _load_next_message(self):
        """Load the next message from the queue."""
        if self.message_queue:
            next_message = self.message_queue.pop(0)
            
            # Store the current message as the previous message
            if self.current_full_message:
                self.previous_message = self.current_full_message
                
            # Reset the display index for the new message
            self.display_index = 0
            self.last_char_time = pygame.time.get_ticks()
            
            # Set the new target message
            self.target_message = next_message
        else:
            # If the queue is empty, clear the target message
            self.target_message = ""
    
    def update(self):
        """Update the message display."""
        current_time = pygame.time.get_ticks()
        
        # Web optimization: Skip message updates in web environment on some frames
        if is_web_environment():
            # Only update messages every few frames to reduce CPU usage
            if hasattr(self, 'web_frame_skip'):
                self.web_frame_skip = (self.web_frame_skip + 1) % 3
                if self.web_frame_skip != 0:
                    return
            else:
                self.web_frame_skip = 0
        
        # If we have a target message, animate it character by character
        if self.target_message:
            if self.display_index < len(self.target_message):
                # Check if it's time to display the next character
                if current_time - self.last_char_time > self.char_delay:
                    # Web optimization: Display characters faster in web environment
                    if is_web_environment():
                        # Display multiple characters at once in web environment
                        chars_to_add = min(3, len(self.target_message) - self.display_index)
                        self.display_index += chars_to_add
                    else:
                        self.display_index += 1
                    
                    self.current_message = self.target_message[:self.display_index]
                    self.last_char_time = current_time
            else:
                # Message is fully displayed
                if self.current_full_message != self.target_message:
                    self.current_full_message = self.target_message
                    self.message_completed_time = current_time
                
                # Check if it's time to load the next message from the queue
                if (current_time - self.message_completed_time > self.message_transition_delay and 
                    self.message_queue):
                    self._load_next_message()
        
        # If we don't have a target message and there's nothing in the queue,
        # check if it's time to show a default message
        elif not self.message_queue and self.can_show_default_message():
            # Web optimization: Show fewer default messages in web environment
            if not is_web_environment() or random.random() < 0.5:
                self.show_default_message()
    
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
    # Default messages that cycle based on time
    default_messages = [
        "Run, jump, and collect coins to increase your score!",
        "Watch out for obstacles ahead!",
        "Try to go as far as you can!",
        "Collect power-ups to gain special abilities!",
        "Press SPACE to jump. Double-tap to double jump!"
    ]
    
    # Only show default messages if it's been a while since the last one and no other messages are queued
    if message_manager.can_show_default_message():
        # Get the current default message
        current_default_message = default_messages[message_manager.default_message_index]
        
        # Only set the message if it's different from the current and previous messages
        if (current_default_message != message_manager.current_full_message and 
            current_default_message != message_manager.previous_message):
            # Set the message first
            message_manager.set_message(current_default_message)
            # Then update the last_message_time and increment the default message index
            message_manager.last_message_time = pygame.time.get_ticks()
            # Increment the default message index to cycle through the messages
            message_manager.default_message_index = (message_manager.default_message_index + 1) % 5
    
    # Update the message manager
    message_manager.update()
    
    # Return the current message
    return message_manager.current_message or ""