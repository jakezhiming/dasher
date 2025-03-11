from compat import pygame
from constants.player import BASE_MOVE_SPEED, SPEED_BOOST_MULTIPLIER, JUMP_VELOCITY, MAX_BACKTRACK_DISTANCE
from constants.screen import WIDTH
from constants.camera import CAMERA_RIGHT_BOUNDARY_FACTOR, CAMERA_LEFT_BOUNDARY_FACTOR
from logger import get_module_logger

logger = get_module_logger('input_handler')

# Global variables for input state
space_key_pressed = False
d_key_pressed = False
show_debug = False  # Start with debug off

def handle_input(player):
    """Handle keyboard input for player movement and debug toggle."""
    global space_key_pressed, show_debug, d_key_pressed
    keys = pygame.key.get_pressed()
    
    # Toggle debug display with 'D' key (both uppercase and lowercase)
    # Note: pygame.K_d is lowercase 'd', pygame.K_CAPITAL_D doesn't exist
    # Pygame handles this automatically based on the key pressed, not the case
    if keys[pygame.K_d] and not d_key_pressed:
        show_debug = not show_debug
        d_key_pressed = True
    elif not keys[pygame.K_d]:
        d_key_pressed = False
    
    move_speed = BASE_MOVE_SPEED * SPEED_BOOST_MULTIPLIER if player.speed_boost else BASE_MOVE_SPEED
    if not player.immobilized:
        if keys[pygame.K_LEFT]:
            player.vx = -move_speed
            player.direction = 'left'
        elif keys[pygame.K_RIGHT]:
            player.vx = move_speed
            player.direction = 'right'
        else:
            player.vx = 0
        
        # Handle jumping with space key
        if keys[pygame.K_SPACE] and not space_key_pressed:
            # First jump when on the ground
            if not player.jumping:
                player.vy = JUMP_VELOCITY
                player.jumping = True
            # Double jump when already in the air but haven't used double jump yet
            elif not player.double_jumped:
                player.vy = JUMP_VELOCITY
                player.perform_double_jump()  # Use the new method for double jumping
            # Flying power-up allows continuous jumping
            elif player.flying:
                player.vy = -move_speed
        
        # Update space key state
        space_key_pressed = keys[pygame.K_SPACE]
    
    return player_has_moved(player)

def player_has_moved(player):
    """Check if the player has moved."""
    return player.vx != 0 or player.vy != 0

def update_scroll(player, camera_x):
    """Update the camera position based on player movement."""
    
    # Calculate dynamic left boundary based on furthest right position
    dynamic_left_boundary = max(0, player.furthest_right_position - MAX_BACKTRACK_DISTANCE)
    
    # Follow player when moving right
    if player.x > camera_x + WIDTH * CAMERA_RIGHT_BOUNDARY_FACTOR:
        camera_x = player.x - WIDTH * CAMERA_RIGHT_BOUNDARY_FACTOR
    # Follow player when moving left
    elif player.x < camera_x + WIDTH * CAMERA_LEFT_BOUNDARY_FACTOR:
        camera_x = max(dynamic_left_boundary, player.x - WIDTH * CAMERA_LEFT_BOUNDARY_FACTOR)
    
    return camera_x 