import pygame
import math
import asyncio
import threading
from constants import (
    PLAY_AREA_HEIGHT, STATUS_BAR_HEIGHT, WIDTH, HEIGHT,
    BLACK, DARK_GREY, GRAY, RED, WHITE,
    INVINCIBILITY_FROM_DAMAGE_DURATION, HEART_SPRITE_PATH,
    HEART_SPRITE_SIZE, MESSAGE_CHAR_DELAY, DEFAULT_MESSAGE_DELAY,
    WHITE_OVERLAY, BLUE, CYAN, MAGENTA,
    SPEED_BOOST_DURATION, INVINCIBILITY_DURATION
)
from utils import render_retro_text, get_retro_font
from sprite_loader import player_frames, get_frame
from llm_message_handler import LLMMessageHandler

heart_sprite = None
heart_sprite_size = HEART_SPRITE_SIZE
heart_flash_time = 0
heart_flash_duration = INVINCIBILITY_FROM_DAMAGE_DURATION 
# New variables for heart pop-in effect
new_heart_index = -1  # Index of the newly added heart (-1 means no new heart)
new_heart_time = 0    # Time when the new heart was added
new_heart_duration = 300  # Duration of the pop-in effect in milliseconds
# Variables for the "+X" indicator animation
plus_indicator_active = False
plus_indicator_time = 0
plus_indicator_duration = 300  # Duration of the "+X" animation in milliseconds

def load_heart_sprite():
    """Load the heart sprite image."""
    global heart_sprite, heart_sprite_size
    try:
        heart_sprite = pygame.image.load(HEART_SPRITE_PATH).convert_alpha()
        heart_sprite_size = HEART_SPRITE_SIZE
        print(f"Successfully loaded heart sprite from {HEART_SPRITE_PATH}")
    except Exception as e:
        print(f"Error loading heart sprite: {e}")
        exit()

def set_hearts_flash():
    """Set the hearts to flash (call this when player loses a life)."""
    global heart_flash_time
    heart_flash_time = pygame.time.get_ticks()

# New function to trigger the heart pop-in effect
def set_heart_pop_in(heart_index):
    """Set a heart to pop in with an animation effect."""
    global new_heart_index, new_heart_time
    new_heart_index = heart_index
    new_heart_time = pygame.time.get_ticks()

# New function to trigger the "+X" indicator animation
def set_plus_indicator_animation():
    """Set the "+X" indicator to animate when a life is added beyond max displayed hearts."""
    global plus_indicator_active, plus_indicator_time
    plus_indicator_active = True
    plus_indicator_time = pygame.time.get_ticks()

def draw_heart(screen, x, y, size=HEART_SPRITE_SIZE, color=None, flashing=False, is_new=False):
    """Draw a heart at the specified position with the given size."""
    global heart_sprite, heart_sprite_size
    
    # Load the sprite if it hasn't been loaded yet
    if heart_sprite is None:
        load_heart_sprite()
    
    # Create a copy of the sprite for potential color modification
    sprite_to_use = heart_sprite.copy() if (flashing or is_new) else heart_sprite
    
    # If flashing, apply a white tint
    if flashing:
        # Create a white overlay
        white_overlay = pygame.Surface(sprite_to_use.get_size()).convert_alpha()
        white_overlay.fill(WHITE_OVERLAY)  # Semi-transparent white
        sprite_to_use.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    
    # Apply pop-in effect if this is a new heart
    if is_new:
        current_time = pygame.time.get_ticks()
        effect_progress = min(1.0, (current_time - new_heart_time) / new_heart_duration)
        
        # Scale effect: start larger and shrink to normal size
        scale_factor = 1.5 - (0.5 * effect_progress)
        
        # Pulse effect: add a bright overlay that fades out
        if effect_progress < 0.7:
            pulse_alpha = int(255 * (1 - effect_progress / 0.7))
            white_overlay = pygame.Surface(sprite_to_use.get_size()).convert_alpha()
            white_overlay.fill((255, 255, 255, pulse_alpha))
            sprite_to_use.blit(white_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        
        # Apply the scale effect
        effect_size = int(size * scale_factor)
        scaled_sprite = pygame.transform.scale(sprite_to_use, (effect_size, effect_size))
        
        # Center the scaled sprite on the original position
        offset_x = (effect_size - size) // 2
        offset_y = (effect_size - size) // 2
        screen.blit(scaled_sprite, (x - offset_x, y - offset_y))
    else:
        # Scale the sprite if needed (normal case)
        if size != heart_sprite_size:
            scaled_sprite = pygame.transform.scale(sprite_to_use, (size, size))
            screen.blit(scaled_sprite, (x, y))
        else:
            screen.blit(sprite_to_use, (x, y))

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
        
        # Set up asyncio event loop in a separate thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        
        # Add a delay between messages in the queue
        self.message_transition_delay = 500  # 500ms delay between messages
        self.message_completed_time = 0  # Track when a message was fully displayed
        
        # Initialize with a welcome message
        self.set_message("Welcome to Dasher! Use arrow keys to move and SPACE to jump.")
    
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
            print(f"Error processing LLM message: {e}")
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
        print(f"Status Message: {next_message}")

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
        return "None (LLM not available)"

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
    
    # Update and return the current streaming message
    return message_manager.update()

def draw_ui(screen, player):
    # Check if hearts should be flashing
    current_time = pygame.time.get_ticks()
    hearts_flashing = (current_time - heart_flash_time < heart_flash_duration)
    
    # Flash pattern - alternate every 100ms
    flash_on = hearts_flashing and ((current_time // 100) % 2 == 0)
    
    # Check if the new heart effect should still be active
    new_heart_active = (current_time - new_heart_time < new_heart_duration)
    
    # Check if the "+X" indicator animation should be active
    plus_animation_active = (current_time - plus_indicator_time < plus_indicator_duration) and plus_indicator_active
    
    # Draw hearts for lives at top left
    heart_size = 24  # Adjust size as needed for the sprite
    heart_spacing = 28  # Space between hearts
    heart_y_position = 15
    max_hearts = 5  # Maximum number of hearts to display
    
    # Display hearts based on player lives, up to max_hearts
    displayed_hearts = min(player.lives, max_hearts)
    for i in range(displayed_hearts):
        # Check if this heart should have the pop-in effect
        is_new_heart = new_heart_active and i == new_heart_index
        draw_heart(screen, 15 + (i * heart_spacing), heart_y_position, heart_size, 
                  flashing=flash_on, is_new=is_new_heart)
    
    # If player has more lives than max_hearts, show a "+" indicator
    if player.lives > max_hearts:
        extra_lives = player.lives - max_hearts
        plus_text = render_retro_text(f"+{extra_lives}", 14, RED)
        
        # Apply animation effect to the "+X" indicator if active
        if plus_animation_active:
            # Calculate animation progress (0.0 to 1.0)
            progress = (current_time - plus_indicator_time) / plus_indicator_duration
            
            # Scale effect: start larger and shrink to normal size
            scale_factor = 1.5 - (0.5 * progress)
            
            # Create a copy of the text surface to apply effects
            original_width, original_height = plus_text.get_size()
            scaled_width = int(original_width * scale_factor)
            scaled_height = int(original_height * scale_factor)
            
            # Scale the text
            scaled_text = pygame.transform.scale(plus_text, (scaled_width, scaled_height))
            
            # Add a glow effect that fades out
            if progress < 0.7:
                # Create a white surface with decreasing alpha
                glow_alpha = int(180 * (1 - progress / 0.7))
                glow_surface = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
                glow_surface.fill((255, 255, 255, glow_alpha))
                
                # Apply the glow
                scaled_text.blit(glow_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            
            # Calculate position to keep the text centered during scaling
            x_pos = 15 + (max_hearts * heart_spacing) - (scaled_width - original_width) // 2
            y_pos = heart_y_position + 5 - (scaled_height - original_height) // 2
            
            # Draw the animated text
            screen.blit(scaled_text, (x_pos, y_pos))
        else:
            # Draw normal text without animation
            screen.blit(plus_text, (15 + (max_hearts * heart_spacing), heart_y_position + 5))
    
    # Draw score at top right
    score_text = render_retro_text(f"Score: {player.score}", 18, BLACK)
    score_rect = score_text.get_rect()
    screen.blit(score_text, (WIDTH - score_rect.width - 10, 10))
    
    # Draw active power-up indicators
    draw_active_powerups(screen, player, current_time)
    
    # Draw status bar with message
    pygame.draw.rect(screen, GRAY, (0, PLAY_AREA_HEIGHT, WIDTH, STATUS_BAR_HEIGHT))
    
    # Get and display the streaming status message
    message = get_status_message()
    
    # Calculate max width for messages (leave some margin on both sides)
    max_message_width = WIDTH - 80  # Reduced to make room for player sprite
    
    # Get player idle animation frame for the status bar
    # Use the player's current animation frame to sync with the main animation
    animation_key = 'idle_right'
    frame_index = player.animation_frame % len(player_frames[animation_key])
    player_icon = get_frame(animation_key, frame_index)
    
    # Scale down the player icon to fit in the status bar
    icon_size = 40
    aspect_ratio = player_icon.get_width() / player_icon.get_height()
    icon_width = int(icon_size * aspect_ratio)
    icon_height = icon_size
    player_icon = pygame.transform.scale(player_icon, (icon_width, icon_height))
    
    # Draw the player icon to the left of the message
    icon_x = 10
    icon_y = PLAY_AREA_HEIGHT + (STATUS_BAR_HEIGHT - icon_height) // 2
    screen.blit(player_icon, (icon_x, icon_y))
    
    # Display current message in first row
    message_text = render_retro_text(message, 16, BLACK, max_message_width)
    screen.blit(message_text, (60, PLAY_AREA_HEIGHT + 20))
    
    # Display previous message in second row (slightly smaller and faded)
    previous_message = message_manager.get_previous_message()
    
    # Check if the current message has 3 or more lines
    current_font = get_retro_font(16)
    current_line_height = current_font.get_linesize()
    current_message_lines = message_text.get_height() // current_line_height
    
    # Only show previous message if current message has fewer than 3 lines
    if previous_message and current_message_lines < 3:
        # Render the previous message
        prev_text = render_retro_text(previous_message, 14, DARK_GREY, max_message_width)
        
        # Check if previous message has 3 or more lines
        prev_font = get_retro_font(14)
        prev_line_height = prev_font.get_linesize()
        prev_message_lines = prev_text.get_height() // prev_line_height
        
        if prev_message_lines >= 3:
            # If previous message has 3+ lines, only show first 2 lines with "..." at the end
            words = previous_message.split(' ')
            lines = []
            current_line = []
            
            # Recreate the line wrapping logic to find the first two lines
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_width = prev_font.size(test_line)[0]
                
                if test_width <= max_message_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        if len(lines) >= 2:  # We have our two lines
                            break
                    current_line = [word]
            
            # Add the last line if we don't have 2 yet
            if current_line and len(lines) < 2:
                lines.append(' '.join(current_line))
            
            # If we have at least one line
            if lines:
                # If we have two lines, add "..." to the second line
                if len(lines) >= 2:
                    lines[1] = lines[1][:-3] + "..."
                
                # Render the truncated message - render each line separately
                if len(lines) == 1:
                    prev_text = render_retro_text(lines[0], 14, DARK_GREY, max_message_width)
                else:  # len(lines) == 2
                    # Create a surface to hold both lines
                    line1_surf = prev_font.render(lines[0], True, DARK_GREY)
                    line2_surf = prev_font.render(lines[1], True, DARK_GREY)
                    
                    total_height = prev_line_height * 2
                    prev_text = pygame.Surface((max_message_width, total_height), pygame.SRCALPHA)
                    
                    # Blit each line onto the surface
                    prev_text.blit(line1_surf, (0, 0))
                    prev_text.blit(line2_surf, (0, prev_line_height))
        
        screen.blit(prev_text, (60, PLAY_AREA_HEIGHT + STATUS_BAR_HEIGHT - 35))

def draw_active_powerups(screen, player, current_time):
    """Draw indicators for active power-ups"""
    # Position for power-up indicators (top center)
    indicator_size = 24
    indicator_spacing = 65
    indicator_y = 80
    indicator_start_x = 35  # Center position, adjusted for multiple indicators
    
    active_powerups = []
    
    # Check which power-ups are active
    if player.speed_boost:
        active_powerups.append(('speed', BLUE))
    if player.flying:
        active_powerups.append(('flying', CYAN))
    if player.invincible and not player.invincible_from_damage:
        active_powerups.append(('invincibility', MAGENTA))
    
    # Draw each active power-up indicator
    for i, (powerup_type, color) in enumerate(active_powerups):
        x_pos = indicator_start_x + (i * indicator_spacing)
        
        # Create a pulsing effect for the indicator
        pulse_factor = 1.0 + 0.2 * math.sin(current_time / 200)  # Pulsing size
        pulse_size = int(indicator_size * pulse_factor)
        
        # Draw the power-up indicator
        pygame.draw.circle(screen, color, (x_pos, indicator_y), pulse_size)
        
        # Draw an icon or symbol inside the circle based on power-up type
        if powerup_type == 'speed':
            # Draw lightning bolt symbol for speed
            points = [
                (x_pos - 5, indicator_y - 8),  # Top left
                (x_pos + 2, indicator_y - 2),  # Middle right
                (x_pos - 5, indicator_y),      # Middle left
                (x_pos + 5, indicator_y + 8)   # Bottom right
            ]
            pygame.draw.polygon(screen, WHITE, points)
        elif powerup_type == 'flying':
            # Draw two triangles side by side to represent wings
            indicator_y += 5
            wing_width = 10
            wing_height = 8
            
            # Left wing triangle
            left_wing = [
                (x_pos - wing_width, indicator_y),          # Left base
                (x_pos, indicator_y),                       # Right base
                (x_pos - wing_width/2 + 1, indicator_y - wing_height)  # Top point
            ]
            pygame.draw.polygon(screen, WHITE, left_wing)
            
            # Right wing triangle
            right_wing = [
                (x_pos, indicator_y),                       # Left base
                (x_pos + wing_width, indicator_y),          # Right base
                (x_pos + wing_width/2 - 1, indicator_y - wing_height)  # Top point
            ]
            pygame.draw.polygon(screen, WHITE, right_wing)
            
        elif powerup_type == 'invincibility':
            # Draw star symbol for invincibility
            pygame.draw.circle(screen, WHITE, (x_pos, indicator_y), pulse_size // 3)
        
        # Draw timer indicator (circular progress)
        if powerup_type == 'speed':
            # Calculate remaining time percentage
            remaining_time = 1.0 - min(1.0, (current_time - player.speed_boost_timer) / SPEED_BOOST_DURATION)
            draw_circular_timer(screen, x_pos, indicator_y, pulse_size + 2, remaining_time, WHITE)
        elif powerup_type == 'flying':
            remaining_time = 1.0 - min(1.0, (current_time - player.flying_timer) / 5000)
            draw_circular_timer(screen, x_pos, indicator_y, pulse_size + 2, remaining_time, WHITE)
        elif powerup_type == 'invincibility':
            remaining_time = 1.0 - min(1.0, (current_time - player.invincible_timer) / INVINCIBILITY_DURATION)
            draw_circular_timer(screen, x_pos, indicator_y, pulse_size + 2, remaining_time, WHITE)

def draw_circular_timer(screen, x, y, radius, percentage, color):
    """Draw a circular timer showing remaining time percentage"""
    if percentage <= 0:
        return
    
    # Draw arc from top (270 degrees) clockwise
    start_angle = -90  # Start from top (270 degrees in pygame coordinates)
    end_angle = start_angle + (360 * percentage)
    
    # Convert to radians and draw
    rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
    pygame.draw.arc(screen, color, rect, math.radians(start_angle), math.radians(end_angle), 2)

def draw_debug_info(screen, player):
    y_pos = 50  # Start position for debug info
    line_height = 25
    
    # Calculate difficulty percentage
    from constants import DIFFICULTY_START_DISTANCE, DIFFICULTY_MAX_DISTANCE
    if player.x <= DIFFICULTY_START_DISTANCE:
        difficulty_percentage = 0
    elif player.x >= DIFFICULTY_MAX_DISTANCE:
        difficulty_percentage = 100
    else:
        difficulty_percentage = int((player.x - DIFFICULTY_START_DISTANCE) / (DIFFICULTY_MAX_DISTANCE - DIFFICULTY_START_DISTANCE) * 100)
    
    # Display player position
    pos_text = render_retro_text(f"Position: ({int(player.x)}, {int(player.y)})", 12, BLACK)
    screen.blit(pos_text, (10, y_pos))
    y_pos += line_height
    
    # Display player velocity
    vel_text = render_retro_text(f"Velocity: ({int(player.vx)}, {int(player.vy)})", 12, BLACK)
    screen.blit(vel_text, (10, y_pos))
    y_pos += line_height
    
    # Display player state
    state_text = render_retro_text(f"Jumping: {player.jumping}, Double jumped: {player.double_jumped}", 12, BLACK)
    screen.blit(state_text, (10, y_pos))
    y_pos += line_height
    
    # Display power-up status
    powerup_text = render_retro_text(f"Speed boost: {player.speed_boost}, Flying: {player.flying}", 12, BLACK)
    screen.blit(powerup_text, (10, y_pos))
    y_pos += line_height
    
    # Display invincibility status
    invincible_text = render_retro_text(f"Invincible: {player.invincible}", 12, BLACK)
    screen.blit(invincible_text, (10, y_pos))
    y_pos += line_height
    
    # Display coin count
    coin_text = render_retro_text(f"Coins: {player.coin_score}", 12, BLACK)
    screen.blit(coin_text, (10, y_pos))
    y_pos += line_height
    
    # Display current LLM personality
    personality_text = render_retro_text(f"LLM Personality: {message_manager.get_current_personality()}", 12, BLACK)
    screen.blit(personality_text, (10, y_pos))
    y_pos += line_height
    
    # Display difficulty percentage
    difficulty_text = render_retro_text(f"Difficulty: {difficulty_percentage}%", 12, BLACK)
    screen.blit(difficulty_text, (10, y_pos)) 