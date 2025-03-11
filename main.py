from pygame_compat import pygame
import asyncio
from dotenv_compat import load_dotenv

load_dotenv()

from assets_loader import load_all_assets
from constants.colors import BLUE, RED
from constants.screen import WIDTH, HEIGHT, PLAY_AREA_HEIGHT
from constants.game_states import (
    GAME_RUNNING, GAME_LOST_MESSAGE, GAME_OVER, GAME_OVER_DISPLAY_DURATION
)
from utils import render_retro_text, draw_background
from player import Player
from game_objects import Floor
from ui import draw_ui, draw_debug_info
from messages import message_manager
import input_handler
from level_generator import generate_new_segment, remove_old_objects
from effects import effect_manager
from logger import logger, log_game_start, log_game_over

# Try to import web-specific UI components
try:
    from web_ui import ApiKeyInput, is_web_environment, load_api_key_from_storage
    IS_WEB = is_web_environment()
    logger.info("Web environment detected")
except ImportError:
    IS_WEB = False
    logger.info("Desktop environment detected")

# Initialize Pygame
pygame.init()
logger.info("Pygame initialized")

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Dasher")
clock = pygame.time.Clock()
logger.info(f"Screen setup complete: {WIDTH}x{HEIGHT}")

# Load game assets
try:
    load_all_assets()  # Load all game assets using the asset_loader
    logger.info("Game assets loaded")
except Exception as e:
    logger.error(f"Failed to load assets: {str(e)}")
    # Don't exit the game, continue with potentially missing assets
    # This will prevent a black screen in the web version

# Load API key from localStorage if in web environment
api_key_input = None
if IS_WEB:
    load_api_key_from_storage()
    # Create API key input field
    api_key_input = ApiKeyInput(50, 50, 400, 30)
    logger.info("API key input field created")

async def main():
    # Initialize game
    player = Player()
    camera_x = 0
    rightmost_floor_end = WIDTH
    # Create initial floor that's wide enough for the starting area
    floors = [Floor(0, WIDTH)]
    platforms = []
    obstacles = []
    coins = []
    power_ups = []
    game_over = False
    game_state = GAME_RUNNING
    game_over_timer = 0
    player_has_moved = False
    
    # Reset conversation history for new game
    try:
        message_manager.llm_handler.reset_conversation_history()
    except Exception as e:
        logger.warning(f"Failed to reset conversation history: {str(e)}")
    
    # Set an initial welcome message
    try:
        message_manager.set_message("Welcome to Dasher! Use arrow keys to move and jump.")
    except Exception as e:
        logger.warning(f"Failed to set welcome message: {str(e)}")
    
    # Log game start
    log_game_start()
    
    # Web-specific settings
    show_api_key_input = IS_WEB and not message_manager.llm_handler.is_available()
    pending_api_test = False

    # Main loop
    running = True
    frame_count = 0
    last_time = pygame.time.get_ticks()
    
    try:
        while running:
            # This is needed for Pygbag to work properly - moved to the beginning of the loop
            await asyncio.sleep(0)
            
            # Calculate delta time for smooth animations
            current_time = pygame.time.get_ticks()
            dt = (current_time - last_time) / 1000.0  # Convert to seconds
            last_time = current_time
            
            frame_count += 1
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    logger.info("Game quit requested")
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    # Handle window resize for web compatibility
                    logger.debug(f"Window resized to {event.w}x{event.h}")
                    pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                
                # Handle API key input in web version
                if IS_WEB and show_api_key_input and api_key_input:
                    if api_key_input.handle_event(event):
                        # If API key was saved, update the LLM handler
                        if api_key_input.saved:
                            logger.info("API key saved")
                            message_manager.llm_handler.api_key = api_key_input.text
                            # Check if we should still show the input
                            show_api_key_input = not message_manager.llm_handler.is_available()
                        
                        # Check if we need to test the API key
                        if api_key_input.testing:
                            logger.info("Testing API key")
                            pending_api_test = True

            # Handle pending API key test
            if pending_api_test and api_key_input:
                try:
                    await api_key_input._test_api_key()
                    logger.info("API key test completed")
                except Exception as e:
                    logger.error(f"API key test failed: {str(e)}")
                pending_api_test = False

            # Update message manager
            try:
                message_manager.update()
            except Exception as e:
                logger.error(f"Error updating message manager: {e}")
            
            # Update game state
            if game_state == GAME_RUNNING:
                # Game logic
                player_has_moved = input_handler.handle_input(player) or player_has_moved
                
                game_over = player.update(floors, platforms, obstacles, coins, power_ups)
                
                # If game_over is True, the player has completed their death animation
                if game_over:
                    game_state = GAME_LOST_MESSAGE
                    game_over_timer = pygame.time.get_ticks()
                
                camera_x = input_handler.update_scroll(player, camera_x)
                
                # Update animations for coins and power-ups
                for coin in coins:
                    coin.update(dt)
                for power_up in power_ups:
                    power_up.update(dt)
                # Update animations for obstacles
                for obstacle in obstacles:
                    obstacle.update(dt)
                
                # Update collection effects
                effect_manager.update(dt)
                
                if camera_x + WIDTH > rightmost_floor_end - 600:
                    old_rightmost = rightmost_floor_end
                    rightmost_floor_end = generate_new_segment(player, floors, platforms, obstacles, coins, power_ups, camera_x, WIDTH)
                    logger.debug(f"Generated new segment from {old_rightmost} to {rightmost_floor_end}")
                
                floors, platforms, obstacles, coins, power_ups = remove_old_objects(player, floors, platforms, obstacles, coins, power_ups)

                # Draw background
                draw_background(screen, camera_x)
                
                # Batch similar objects together to reduce draw calls
                visible_range = (camera_x - 100, camera_x + WIDTH + 100)
                
                for floor in floors:
                    if floor.x + floor.width >= visible_range[0] and floor.x <= visible_range[1]:
                        floor.draw(screen, camera_x)
                
                for platform in platforms:
                    if platform.x + platform.width >= visible_range[0] and platform.x <= visible_range[1]:
                        platform.draw(screen, camera_x)
                
                for obstacle in obstacles:
                    if obstacle.x + obstacle.width >= visible_range[0] and obstacle.x <= visible_range[1]:
                        obstacle.draw(screen, camera_x)
                
                for coin in coins:
                    if coin.x + coin.width >= visible_range[0] and coin.x <= visible_range[1]:
                        coin.draw(screen, camera_x)
                
                for power_up in power_ups:
                    if power_up.x + power_up.width >= visible_range[0] and power_up.x <= visible_range[1]:
                        power_up.draw(screen, camera_x)
                
                player.draw(screen, camera_x)
                
                # Draw collection effects
                effect_manager.draw(screen, camera_x)
                
                draw_ui(screen, player)
                
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
                if pygame.time.get_ticks() - game_over_timer > GAME_OVER_DISPLAY_DURATION:
                    game_state = GAME_OVER
                    log_game_over(player.score)
                
                # Continue drawing the game state - reuse the same drawing code
                draw_background(screen, camera_x)
                
                for floor in floors:
                    if floor.x + floor.width >= visible_range[0] and floor.x <= visible_range[1]:
                        floor.draw(screen, camera_x)
                
                for platform in platforms:
                    if platform.x + platform.width >= visible_range[0] and platform.x <= visible_range[1]:
                        platform.draw(screen, camera_x)
                
                for obstacle in obstacles:
                    if obstacle.x + obstacle.width >= visible_range[0] and obstacle.x <= visible_range[1]:
                        obstacle.draw(screen, camera_x)
                
                for coin in coins:
                    if coin.x + coin.width >= visible_range[0] and coin.x <= visible_range[1]:
                        coin.draw(screen, camera_x)
                
                for power_up in power_ups:
                    if power_up.x + power_up.width >= visible_range[0] and power_up.x <= visible_range[1]:
                        power_up.draw(screen, camera_x)
                
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
                rightmost_floor_end = WIDTH
                floors = [Floor(0, WIDTH)]
                platforms = []
                obstacles = []
                coins = []
                power_ups = []
                game_over = False
                game_state = GAME_RUNNING
                player_has_moved = False
                
                # Reset conversation history for the new game
                message_manager.llm_handler.reset_conversation_history()
                
                logger.info("Game reset after game over")
                
                # Change to a new LLM personality
                try:
                    new_personality = message_manager.llm_handler.change_personality()
                    message_manager.set_message(f"Welcome back! I'm now speaking like a {new_personality}.")
                    logger.info(f"Changed LLM personality to {new_personality}")
                except Exception as e:
                    # Handle case where LLM is not available
                    logger.warning(f"Failed to change LLM personality: {str(e)}")
                    message_manager.set_message("Welcome back! Let's play again!")

            # Update the display
            pygame.display.flip()
            clock.tick(60)  # 60 FPS
            
    except Exception as e:
        logger.error(f"Game loop error: {str(e)}")
        # In web version, we want to keep the game running even if there's an error
        if not IS_WEB:
            raise
    finally:
        logger.info("Game loop ended")
        if not IS_WEB:  # Don't quit pygame in web version
            pygame.quit()
            logger.info("Pygame quit")

# This is the entry point for Pygbag
logger.info("Starting game")
try:
    asyncio.run(main())
except Exception as e:
    logger.error(f"Failed to start game: {str(e)}")
    if not IS_WEB:
        exit()
    else:
        # In web version, stop the game loop but don't exit
        try:
            import js
            js.stop_game()
        except ImportError:
            pass