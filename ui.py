import pygame
from constants import (
    PLAY_AREA_HEIGHT, STATUS_BAR_HEIGHT, WIDTH, HEIGHT,
    BLACK, DARK_GREY, GRAY
)
from utils import render_retro_text

class StatusMessageManager:
    def __init__(self):
        self.current_message = ""
        self.target_message = ""
        self.display_index = 0
        self.last_char_time = 0
        self.char_delay = 5  # Milliseconds between characters
        self.last_default_time = 0
        self.default_message_delay = 5000  # 5 seconds between default messages
        self.default_message_index = 0
        
        # Keep track of the last two messages
        self.previous_message = ""
        self.current_full_message = ""
        
        # Track messages that should only be shown once
        self.shown_messages = set()
        
        # Initialize with a welcome message
        self.set_message("Welcome to Dasher! Use arrow keys to move and SPACE to jump.")
        
    def set_message(self, message):
        """Set a new message. Newer messages always take precedence."""
        if message != self.target_message:
            # Save the current message as previous before setting the new one
            if self.current_full_message:
                self.previous_message = self.current_full_message
            
            self.target_message = message
            self.current_full_message = message
            self.display_index = 0
            self.last_char_time = pygame.time.get_ticks()
    
    def update(self):
        """Update the streaming text effect."""
        current_time = pygame.time.get_ticks()
        
        # If we're still streaming the message
        if self.display_index < len(self.target_message):
            if current_time - self.last_char_time > self.char_delay:
                self.display_index += 1
                self.current_message = self.target_message[:self.display_index]
                self.last_char_time = current_time
        else:
            # Message is fully displayed
            self.current_message = self.target_message
            
        return self.current_message
    
    def can_show_default_message(self):
        """Check if enough time has passed to show a new default message."""
        return pygame.time.get_ticks() - self.last_default_time > self.default_message_delay
    
    def set_default_message_shown(self):
        """Mark that a default message has been shown."""
        self.last_default_time = pygame.time.get_ticks()
        self.default_message_index = (self.default_message_index + 1) % 5  # Cycle through 5 default messages
    
    def get_previous_message(self):
        """Get the previous message."""
        return self.previous_message
        
    def has_shown_message(self, message_key):
        """Check if a specific message has already been shown."""
        return message_key in self.shown_messages
        
    def mark_message_shown(self, message_key):
        """Mark a specific message as having been shown."""
        self.shown_messages.add(message_key)

# Create a global instance of the message manager
message_manager = StatusMessageManager()

def get_status_message(player):
    """
    Generate a status message based on the current game state.
    This function will be easy to replace with an LLM-based solution in the future.
    """
    # Default messages that cycle based on time
    default_messages = [
        "Run, jump, and collect coins to increase your score!",
        "Watch out for obstacles ahead!",
        "Try to go as far as you can!",
        "Collect power-ups to gain special abilities!",
        "Press SPACE to jump. Double-tap to double jump!"
    ]
    
    # Priority order for messages (most important first)
    if player.lives == 1 and not message_manager.has_shown_message("last_life"):
        message_manager.set_message("You're on your last life! Be careful!")
        message_manager.mark_message_shown("last_life")
    elif player.lives > 0 and player.invincible and player.invincible_from_damage:
        message_manager.set_message("Ouch! You're temporarily invincible after taking damage.")
    elif player.invincible and not player.invincible_from_damage:
        message_manager.set_message("You're invincible! Nothing can hurt you now!")
    elif player.flying:
        message_manager.set_message("You can fly now! Press SPACE to soar through the sky!")
    elif player.speed_boost:
        message_manager.set_message("Super speed activated! Zoom zoom!")
    elif player.immobilized:
        message_manager.set_message("You're stuck! Wait to regain movement.")
    # Only show default messages if it's been a while since the last one
    elif message_manager.can_show_default_message():
        message_manager.set_message(default_messages[message_manager.default_message_index])
        message_manager.set_default_message_shown()
    
    # Update and return the current streaming message
    return message_manager.update()

def draw_status_bar(screen, player):
    # Draw lives at top left
    lives_text = render_retro_text(f"Lives: {player.lives}", 18, BLACK)
    screen.blit(lives_text, (10, 10))
    
    # Draw score at top right
    score_text = render_retro_text(f"Score: {player.score}", 18, BLACK)
    score_rect = score_text.get_rect()
    screen.blit(score_text, (WIDTH - score_rect.width - 10, 10))
    
    # Draw status bar with message
    pygame.draw.rect(screen, GRAY, (0, PLAY_AREA_HEIGHT, WIDTH, STATUS_BAR_HEIGHT))
    
    # Get and display the streaming status message
    message = get_status_message(player)
    
    # Calculate max width for messages (leave some margin on both sides)
    max_message_width = WIDTH - 40
    
    # Display previous message in second row (slightly smaller and faded)
    previous_message = message_manager.get_previous_message()
    if previous_message:
        prev_text = render_retro_text(previous_message, 14, DARK_GREY, max_message_width)
        screen.blit(prev_text, (20, PLAY_AREA_HEIGHT + STATUS_BAR_HEIGHT - 35))
    
    # Display current message in first row
    message_text = render_retro_text(message, 16, BLACK, max_message_width)
    screen.blit(message_text, (20, PLAY_AREA_HEIGHT + 20))

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
    invincible_text = render_retro_text(f"Invincible: {player.invincible} ({player.invincible_timer})", 12, BLACK)
    screen.blit(invincible_text, (10, y_pos))
    y_pos += line_height
    
    # Display coin count
    coin_text = render_retro_text(f"Coins: {player.coin_score}", 12, BLACK)
    screen.blit(coin_text, (10, y_pos))
    y_pos += line_height
    
    # Display difficulty percentage
    difficulty_text = render_retro_text(f"Difficulty: {difficulty_percentage}%", 12, BLACK)
    screen.blit(difficulty_text, (10, y_pos)) 