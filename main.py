import pygame
import random

# Import from our modules
from constants import (
    WIDTH, HEIGHT, PLAY_AREA_HEIGHT, STATUS_BAR_HEIGHT,
    GAME_RUNNING, GAME_LOST_MESSAGE, GAME_OVER,
    BLUE, BLACK, RED
)
from utils import render_retro_text, draw_background
from player import Player
from game_objects import Floor, Platform, Obstacle, Coin, PowerUp, load_textures
from ui import draw_status_bar, draw_debug_info, message_manager
import input_handler
from level_generator import generate_new_segment, remove_old_objects
from sprite_loader import load_player_sprites

# Initialize Pygame
pygame.init()

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dasher")
clock = pygame.time.Clock()

# Load game assets
load_textures()  # Load game object textures
load_player_sprites()  # Load player sprites

# Initialize game
player = Player()
camera_x = 0
rightmost_floor_end = 800
# Create initial floor that's wide enough for the starting area
floors = [Floor(0, 800)]
platforms = []
obstacles = []
coins = []
power_ups = []
game_over = False
game_state = GAME_RUNNING
game_over_timer = 0
player_has_moved = False

# Set initial messages
message_manager.set_message("Welcome to Dasher! Use arrow keys to move and SPACE to jump.")
# Add a message about the hitbox toggle after a delay
pygame.time.set_timer(pygame.USEREVENT, 3000)  # 3 second delay
show_controls_message = True

# Main loop
running = True
frame_count = 0
last_time = pygame.time.get_ticks()
while running:
    # Calculate delta time for smooth animations
    current_time = pygame.time.get_ticks()
    dt = (current_time - last_time) / 1000.0  # Convert to seconds
    last_time = current_time
    
    frame_count += 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.USEREVENT and show_controls_message:
            message_manager.set_message("Press 'H' to toggle hitbox visibility, 'D' for debug info.")
            show_controls_message = False

    if game_state == GAME_RUNNING:
        # Game logic
        player_has_moved = input_handler.handle_input(player) or player_has_moved
            
        game_over = player.update(floors, platforms, obstacles, coins, power_ups)
        
        # If game_over is True, the player has completed their death animation
        if game_over:
            game_state = GAME_LOST_MESSAGE
            game_over_timer = pygame.time.get_ticks()
            message_manager.set_message("Game Over! Your final score: " + str(player.score))
        
        camera_x = input_handler.update_scroll(player, camera_x)
        
        # Update animations for coins and power-ups
        for coin in coins:
            coin.update(dt)
        for power_up in power_ups:
            power_up.update(dt)
        # Update animations for obstacles
        for obstacle in obstacles:
            obstacle.update(dt)
        
        if camera_x + WIDTH > rightmost_floor_end - 600:
            rightmost_floor_end = generate_new_segment(player, floors, platforms, obstacles, coins, power_ups, rightmost_floor_end, camera_x, WIDTH)
        
        floors, platforms, obstacles, coins, power_ups = remove_old_objects(player, floors, platforms, obstacles, coins, power_ups)

        # Draw background
        draw_background(screen)
        for floor in floors:
            floor.draw(screen, camera_x)
        for platform in platforms:
            platform.draw(screen, camera_x)
        for obstacle in obstacles:
            obstacle.draw(screen, camera_x)
        for coin in coins:
            coin.draw(screen, camera_x)
        for power_up in power_ups:
            power_up.draw(screen, camera_x)
        player.draw(screen, camera_x)
        draw_status_bar(screen, player)
        
        # Draw debug info if enabled
        if input_handler.show_debug:
            draw_debug_info(screen, player)
            
        # Draw welcome text if player hasn't moved yet
        if not player_has_moved:
            text = render_retro_text("Welcome to Dasher", 28, BLUE)
            text_rect = text.get_rect(center=(WIDTH // 2, PLAY_AREA_HEIGHT // 2 - 50))
            screen.blit(text, text_rect)
    
    elif game_state == GAME_LOST_MESSAGE:
        # Show game over message for a few seconds
        if pygame.time.get_ticks() - game_over_timer > 3000:  # 3 seconds
            game_state = GAME_OVER
        
        # Continue drawing the game state
        draw_background(screen)
        for floor in floors:
            floor.draw(screen, camera_x)
        for platform in platforms:
            platform.draw(screen, camera_x)
        for obstacle in obstacles:
            obstacle.draw(screen, camera_x)
        for coin in coins:
            coin.draw(screen, camera_x)
        for power_up in power_ups:
            power_up.draw(screen, camera_x)
        player.draw(screen, camera_x)
        draw_status_bar(screen, player)
        
        # Draw game over text
        game_over_text = render_retro_text("GAME OVER", 36, RED)
        game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, PLAY_AREA_HEIGHT // 2 - 50))
        screen.blit(game_over_text, game_over_rect)
        
        score_text = render_retro_text(f"Final Score: {player.score}", 24, BLUE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, PLAY_AREA_HEIGHT // 2))
        screen.blit(score_text, score_rect)
    
    elif game_state == GAME_OVER:
        # Reset the game
        player = Player()
        camera_x = 0
        rightmost_floor_end = 800
        floors = [Floor(0, 800)]
        platforms = []
        obstacles = []
        coins = []
        power_ups = []
        game_over = False
        game_state = GAME_RUNNING
        player_has_moved = False
        message_manager.set_message("Welcome back! Let's try again.")

    # Update the message manager
    message_manager.update()
    
    # Update the display
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()