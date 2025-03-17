import pygame
import math
from compat import random
from constants.colors import BLUE, CYAN, MAGENTA, RED, WHITE, WHITE_OVERLAY, BLACK, GRAY, DARK_GREY, GOLD, LIGHT_BLUE, LIGHT_GREEN
from constants.screen import PLAY_AREA_HEIGHT, STATUS_BAR_HEIGHT, WIDTH
from constants.ui import HEART_SPRITE_SIZE
from constants.player import INVINCIBILITY_FROM_DAMAGE_DURATION, INVINCIBILITY_DURATION, SPEED_BOOST_DURATION
from utils import render_retro_text, get_retro_font
from assets_loader import player_frames, get_frame, get_heart_sprite
from messages import message_manager, get_status_message
from logger import get_module_logger

logger = get_module_logger('ui')

# Heart pop-in effect variables
heart_sprite_size = HEART_SPRITE_SIZE
heart_flash_time = 0
heart_flash_duration = INVINCIBILITY_FROM_DAMAGE_DURATION 
new_heart_index = -1  # Index of the newly added heart (-1 means no new heart)
new_heart_time = 0    # Time when the new heart was added
new_heart_duration = 300  # Duration of the pop-in effect in milliseconds
plus_indicator_active = False
plus_indicator_time = 0
plus_indicator_duration = 300  # Duration of the "+X" animation in milliseconds

# Score highlight effect variables
score_highlight_duration = 800  # Duration of the score highlight effect in milliseconds
bonus_score_highlight_duration = 2000  # Duration for bonus highlights
score_highlights = []  # List to store multiple active score highlights

# FPS tracking variables
fps_update_time = 0
fps_update_interval = 500  # Update FPS every 500ms
fps_frame_count = 0
current_fps = 0

# Bonus score variables
bonus_score_circle_radius = 45
bonus_score_circle_thickness = 4
bonus_reached_time = 0
bonus_reached_active = False

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

# New function to trigger the score highlight effect
def set_score_highlight(amount=50, is_bonus=False):
    """Set the score to highlight with an animation effect when coins are collected or bonus is awarded."""
    global score_highlights
    # Create a new highlight object
    highlight = {
        'time': pygame.time.get_ticks(),
        'amount': amount,
        'is_bonus': is_bonus,
        'duration': bonus_score_highlight_duration if is_bonus else score_highlight_duration
    }
    # Add to the list of active highlights
    score_highlights.append(highlight)

# New function to trigger the target reached celebration effect
def set_target_reached_celebration():
    """Set the target reached celebration effect when player hits the score target early."""
    global bonus_reached_active, bonus_reached_time
    bonus_reached_active = True
    bonus_reached_time = pygame.time.get_ticks()

# Function to reset the target reached celebration effect
def reset_target_reached_celebration():
    """Reset the target reached celebration effect."""
    global bonus_reached_active
    bonus_reached_active = False

def draw_heart(screen, x, y, size=HEART_SPRITE_SIZE, color=None, flashing=False, is_new=False):
    """Draw a heart at the specified position with the given size."""
    global heart_sprite_size
    
    # Get the heart sprite from asset_loader
    sprite_to_use = get_heart_sprite().copy() if (flashing or is_new) else get_heart_sprite()
    
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
    
    # Clean up expired score highlights
    global score_highlights
    score_highlights = [h for h in score_highlights if current_time - h['time'] < h['duration']]
    
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
    
    # Check if we have any active score highlights
    if score_highlights:
        # Use the most recent highlight for the score text effect
        latest_highlight = score_highlights[0]
        progress = min(1.0, (current_time - latest_highlight['time']) / latest_highlight['duration'])
        
        # Split the score text into "Score: " and the actual number
        score_label = render_retro_text("Score: ", 18, BLACK)
        
        # Render the number part with white flash effect
        flash_intensity = int(255 * (1 - progress))
        flash_color = (
            min(255, BLACK[0] + flash_intensity),
            min(255, BLACK[1] + flash_intensity),
            min(255, BLACK[2] + flash_intensity)
        )
        
        # For bonus highlights, use a gold tint
        if latest_highlight['is_bonus']:
            # Mix gold with the flash color
            gold_factor = 0.5 + 0.5 * math.sin(current_time / 100)  # Pulsing gold effect
            flash_color = (
                min(255, flash_color[0]),
                min(255, int(flash_color[1] * 0.8 + 215 * 0.2 * gold_factor)),  # Add gold tint
                min(255, int(flash_color[2] * 0.8))  # Reduce blue for gold effect
            )
        
        score_number = render_retro_text(f"{player.score}", 18, flash_color)
        
        # Calculate the total width to maintain right alignment
        total_width = score_label.get_width() + score_number.get_width()
        
        # Draw the label part
        label_x = WIDTH - total_width - 10
        screen.blit(score_label, (label_x, 10))
        
        # Draw the number part right after the label
        number_x = label_x + score_label.get_width()
        screen.blit(score_number, (number_x, 10))
        
        # Draw all active +amount indicators
        for i, highlight in enumerate(score_highlights):
            highlight_progress = min(1.0, (current_time - highlight['time']) / highlight['duration'])
            
            # Choose color based on whether it's a bonus
            plus_color = GOLD if highlight['is_bonus'] else GOLD
            plus_text = render_retro_text(f"+{highlight['amount']}", 14, plus_color)
            
            # For bonus highlights, make the text larger and add effects
            if highlight['is_bonus']:
                # Scale effect based on progress
                scale_factor = 1.0 + 0.3 * (1.0 - highlight_progress) * math.sin(current_time / 100)
                scaled_width = int(plus_text.get_width() * scale_factor)
                scaled_height = int(plus_text.get_height() * scale_factor)
                plus_text = pygame.transform.scale(plus_text, (scaled_width, scaled_height))
            
            plus_alpha = int(255 * (1 - highlight_progress))
            plus_text.set_alpha(plus_alpha)
            
            # Position the text - for bonus, position it more prominently
            if highlight['is_bonus']:
                # Position in the same place as regular score increases
                screen.blit(plus_text, (WIDTH - plus_text.get_width() - 10, 35))
                
                # Add sparkle effects around the bonus text
                if highlight_progress < 0.7:  # Only show sparkles for the first 70% of the animation
                    for j in range(3):
                        sparkle_x = WIDTH - plus_text.get_width() / 2 - 10 + random.randint(-20, 20)
                        sparkle_y = 35 + plus_text.get_height() / 2 + random.randint(-10, 10)
                        sparkle_size = random.randint(2, 4)
                        pygame.draw.circle(screen, WHITE, (int(sparkle_x), int(sparkle_y)), sparkle_size)
            else:
                # Normal position for regular score increases
                screen.blit(plus_text, (WIDTH - plus_text.get_width() - 10, 35))
    else:
        # Draw normal score without animation
        screen.blit(score_text, (WIDTH - score_rect.width - 10, 10))
    
    # Draw bonus score progress and target score if active
    if player.bonus_score_active:
        # Calculate progress (0.0 to 1.0)
        elapsed_time = current_time - player.bonus_score_timer
        time_progress = min(1.0, elapsed_time / player.bonus_score_period_duration)
        
        # Calculate remaining time in seconds
        remaining_seconds = max(0, (player.bonus_score_period_duration - elapsed_time) // 1000)
        
        # Calculate target score and current progress toward target
        target_score = player.bonus_score_start_score + player.bonus_score_increase_requirement
        current_score_increase = player.score - player.bonus_score_start_score
        score_progress = min(1.0, current_score_increase / player.bonus_score_increase_requirement)
        
        # Check if target has just been reached (to trigger celebration effect)
        if score_progress >= 1.0 and not bonus_reached_active:
            set_target_reached_celebration()
        
        # Check if celebration effect is active
        celebration_active = (current_time - bonus_reached_time < bonus_score_highlight_duration) and bonus_reached_active
        
        # Position for the circular timer
        circle_x = WIDTH - bonus_score_circle_radius - 30
        circle_y = 110
        inner_radius = bonus_score_circle_radius - 4

        
        # Determine colors for the timers
        time_color = WHITE
        
        # Calculate the difference between score progress and time progress
        # Positive value means score is ahead of time, negative means it's behind
        progress_difference = score_progress - time_progress
        
        # Determine score color based on the difference
        if progress_difference >= 0.1:  # Score is ahead by a safe margin (20% or more)
            score_color = LIGHT_GREEN
        elif progress_difference > 0:   # Score is slightly ahead but not by a safe margin
            score_color = GOLD
        else:                           # Score is equal to or behind time progress
            score_color = RED
        
        # Apply celebration or warning effects
        if celebration_active:
            # Pulse between gold and white when target is reached
            pulse_factor = 0.5 + 0.5 * math.sin(current_time / 50)  # Faster pulse for celebration
            time_color = (
                255,  # Red always max
                min(255, 215 + int(40 * pulse_factor)),  # Green pulses between gold and white
                min(255, int(255 * pulse_factor))  # Blue pulses
            )
            score_color = time_color  # Use the same color for both during celebration
        elif remaining_seconds <= 5:
            # Pulse between white and red when time is low
            pulse_factor = 0.5 + 0.5 * math.sin(current_time / 100)  # Oscillate between 0 and 1
            time_color = (
                255,  # Red always max
                max(0, min(255, int(255 * pulse_factor))),  # Green pulses
                max(0, min(255, int(255 * pulse_factor)))   # Blue pulses
            )

        # Background circle
        pygame.draw.circle(screen, LIGHT_BLUE, (circle_x, circle_y), bonus_score_circle_radius)

        # Draw outer circle (time progress)
        draw_circular_timer(screen, circle_x, circle_y, bonus_score_circle_radius, 
                           1.0 - time_progress, time_color, bonus_score_circle_thickness, True)
        
        # Draw inner circle (score progress)
        draw_circular_timer(screen, circle_x, circle_y, inner_radius, 
                           1.0 - score_progress, score_color, bonus_score_circle_thickness, True)

        # Draw target score in the center
        target_color = BLACK
        if celebration_active:
            # Use gold color with pulsing when target is reached and celebrating
            pulse_factor = 0.5 + 0.5 * math.sin(current_time / 50)  # Faster pulse for celebration
            target_color = (
                255,  # Red always max
                min(255, 215 + int(40 * pulse_factor)),  # Green pulses
                min(255, int(255 * pulse_factor))  # Blue pulses
            )
        elif score_progress >= 0.9 and score_progress < 1.0:
            # Pulse between black and gold when close to target
            pulse_factor = 0.5 + 0.5 * math.sin(current_time / 150)
            target_color = (
                int(255 * pulse_factor),  # Red pulses between 0 and 255
                int((215 + 40 * pulse_factor) * pulse_factor),  # Green pulses between 0 and 255
                0  # Blue stays at 0 for gold
            )
        # Add warning effect for target text when score is behind and time is low
        elif remaining_seconds <= 5 and progress_difference <= 0:
            # Make target text pulse red when score is behind and time is low
            pulse_factor = 0.5 + 0.5 * math.sin(current_time / 100)  # Oscillate between 0 and 1
            target_color = (
                255,  # Red always max
                max(0, min(255, int(255 * pulse_factor))),  # Green pulses
                max(0, min(255, int(255 * pulse_factor)))   # Blue pulses
            )
            
        # Render target score text
        target_text = render_retro_text(f"{target_score}", 14, target_color)
        target_rect = target_text.get_rect(center=(circle_x, circle_y + 5))
        screen.blit(target_text, target_rect)
        
        # Add a small "target" label above the score
        target_label = render_retro_text("TARGET", 8, target_color)
        target_label_rect = target_label.get_rect(center=(circle_x, circle_y - 7))
        screen.blit(target_label, target_label_rect)
        
        # Draw celebration effects if active
        if celebration_active:
            # Add sparkle effects around the circle
            for i in range(5):
                angle = random.random() * 2 * math.pi
                distance = bonus_score_circle_radius * 1.2
                sparkle_x = int(circle_x + math.cos(angle) * distance)
                sparkle_y = int(circle_y + math.sin(angle) * distance)
                sparkle_size = random.randint(2, 4)
                pygame.draw.circle(screen, WHITE, (sparkle_x, sparkle_y), sparkle_size)
    
    # Draw active power-up indicators
    draw_active_powerups(screen, player, current_time)
    
    # Draw status bar with message
    pygame.draw.rect(screen, GRAY, (0, PLAY_AREA_HEIGHT, WIDTH, STATUS_BAR_HEIGHT))
    
    # Get and display the streaming status message
    message = get_status_message()
    
    # Ensure message is a valid string
    if message is None:
        message = ""
    elif not isinstance(message, str):
        try:
            message = str(message)
        except:
            message = ""
    
    # Calculate max width for messages (leave some margin on both sides)
    max_message_width = WIDTH - 80  # Reduced to make room for player sprite
    
    # Get player idle animation frame for the status bar
    # Use the player's current animation frame to sync with the main animation
    animation_key = 'idle_right'
    
    # Make sure we have valid player frames before trying to access them
    if animation_key in player_frames and player_frames[animation_key]:
        frame_index = player.animation_frame % len(player_frames[animation_key])
        player_icon = get_frame(animation_key, frame_index)
        
        if player_icon:
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
        
        if prev_message_lines >= 2:
            # If previous message has 2+ lines, only show first 1 line with "..." at the end
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
                        if len(lines) >= 1:  # We have our one line
                            break
                    current_line = [word]
            
            # Add the last line if we don't have 1 yet
            if current_line and len(lines) < 1:
                lines.append(' '.join(current_line))
            
            # If we have at least one line
            if lines:
                # If we have one line, add "..." to the line
                if len(lines) >= 1:
                    lines[0] = lines[0][:-3] + "..."
                
                # Render the truncated message - render each line separately
                if len(lines) == 1:
                    prev_text = render_retro_text(lines[0], 14, DARK_GREY, max_message_width)
                else:  # len(lines) == 2
                    # Create a surface to hold both lines
                    line1_surf = prev_font.render(lines[0], True, DARK_GREY)
                    
                    total_height = prev_line_height * 2
                    prev_text = pygame.Surface((max_message_width, total_height), pygame.SRCALPHA)
                    
                    # Blit each line onto the surface
                    prev_text.blit(line1_surf, (0, 0))
        
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
        
        
        # Add radial gradient texture (concentric circles with varying opacity)
        for i in range(3):
            inner_radius = int(pulse_size * (0.7 - i * 0.2))
            if inner_radius > 0:
                # Create a slightly darker shade of the original color for inner circles
                darker_color = (
                    max(0, color[0] - 30),
                    max(0, color[1] - 30),
                    max(0, color[2] - 30)
                )
                pygame.draw.circle(screen, darker_color, (x_pos, indicator_y), inner_radius)
        
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

def draw_circular_timer(screen, x, y, radius, percentage, color, thickness=2, clockwise=True):
    """Draw a circular timer showing remaining time percentage"""
    if percentage <= 0:
        return
    
    # Ensure color is a valid RGB tuple with integers in the range [0, 255]
    if color is None:
        color = WHITE  # Default to white if color is None
    
    # Ensure each color component is an integer in the range [0, 255]
    try:
        if len(color) == 3 or len(color) == 4:
            validated_color = tuple(max(0, min(255, int(c))) for c in color)
        else:
            # If color has wrong number of components, use white
            validated_color = WHITE
    except (TypeError, ValueError):
        # If color is not iterable or components can't be converted to int, use white
        validated_color = WHITE
    
    # Draw arc from top (270 degrees) clockwise or anticlockwise
    start_angle = -90  # Start from top (270 degrees in pygame coordinates)
    if clockwise:
        end_angle = start_angle + (360 * percentage)
    else:
        end_angle = start_angle - (360 * percentage)
    
    # Convert to radians and draw
    rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
    pygame.draw.arc(screen, validated_color, rect, math.radians(start_angle), math.radians(end_angle), thickness)

def draw_debug_info(screen, player):
    y_pos = 50  # Start position for debug info
    line_height = 25
    
    # Calculate difficulty percentage
    from constants.difficulty import DIFFICULTY_START_DISTANCE, DIFFICULTY_MAX_DISTANCE
    if player.x <= DIFFICULTY_START_DISTANCE:
        difficulty_percentage = 0
    elif player.x >= DIFFICULTY_MAX_DISTANCE:
        difficulty_percentage = 100
    else:
        difficulty_percentage = int((player.x - DIFFICULTY_START_DISTANCE) / (DIFFICULTY_MAX_DISTANCE - DIFFICULTY_START_DISTANCE) * 100)
    
    # Update FPS calculation
    global fps_update_time, fps_frame_count, current_fps, fps_update_interval
    current_time = pygame.time.get_ticks()
    
    # Increment frame counter
    fps_frame_count += 1
    
    # Update FPS calculation every interval
    if current_time - fps_update_time > fps_update_interval:
        # Calculate FPS: frames / seconds
        current_fps = round(fps_frame_count / (fps_update_interval / 1000))
        # Reset counter and timer
        fps_frame_count = 0
        fps_update_time = current_time
    
    # Display FPS at the top of debug info
    fps_text = render_retro_text(f"FPS: {current_fps}", 12, BLACK)
    screen.blit(fps_text, (10, y_pos))
    y_pos += line_height
    
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
    personality_text = render_retro_text(f"Personality: {message_manager.llm_handler.get_current_personality()}", 12, BLACK)
    screen.blit(personality_text, (10, y_pos))
    y_pos += line_height
    
    # Display difficulty percentage
    difficulty_text = render_retro_text(f"Difficulty: {difficulty_percentage}%", 12, BLACK)
    screen.blit(difficulty_text, (10, y_pos))
    y_pos += line_height

    # Display bonus score system info
    if player.bonus_score_active:
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - player.bonus_score_timer
        remaining_time = max(0, (player.bonus_score_period_duration - elapsed_time) // 1000)
        current_score_increase = player.score - player.bonus_score_start_score
        
        bonus_text = render_retro_text(
            f"Bonus Score Target: {current_score_increase}/{player.bonus_score_increase_requirement} ({remaining_time}s)", 
            12, BLACK
        )
        screen.blit(bonus_text, (10, y_pos))
        y_pos += line_height