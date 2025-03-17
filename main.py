import asyncio
import pygame
from compat import random, IS_WEB

if not IS_WEB:
    from dotenv import load_dotenv
    load_dotenv()

from assets_loader import load_all_assets
from constants.colors import BLUE, RED
from constants.screen import WIDTH, HEIGHT, PLAY_AREA_HEIGHT
from constants.game_states import (
    GAME_RUNNING, GAME_LOST_MESSAGE, GAME_OVER, GAME_OVER_DISPLAY_DURATION
)
from constants.messages import (
    WELCOME_MESSAGES, NEW_PERSONALITY_MESSAGES, WELCOME_BACK_MESSAGES, DEFAULT_PERSONALITY
)
from utils import render_retro_text, draw_background
from player import Player
from game_objects import Floor
from ui import draw_ui, draw_debug_info
from messages import message_manager
import input_handler
from level_generator import generate_new_segment, remove_old_objects
from effects import effect_manager
from logger import logger, get_module_logger, log_game_start, log_game_over
from leaderboard import fetch_leaderboard, submit_score

logger = get_module_logger('main')

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
    load_all_assets()
    logger.info("Game assets loaded")
except Exception as e:
    logger.error(f"Failed to load assets: {str(e)}")
    exit()

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
    
    # Starting personality
    if message_manager.llm_handler.is_available():
        message_manager.llm_handler.change_personality()
        logger.info(f"Starting personality: {message_manager.llm_handler.get_current_personality()}")
    else:
        logger.info(f"Starting personality: {message_manager.llm_handler.get_current_personality()}")

    # Set an initial welcome message
    try:
        message_manager.set_message(random.choice(WELCOME_MESSAGES))
    except Exception as e:
        logger.warning(f"Failed to set welcome message: {str(e)}")

    # Log game start
    log_game_start()

    # Update leaderboard display at start
    if IS_WEB:
        fetch_leaderboard()

    # Main loop
    running = True
    frame_count = 0
    last_time = pygame.time.get_ticks()
    
    try:
        while running:
            # This is needed for Pygbag to work properly - moved to the beginning of the loop
            # In web environment, this allows other tasks to run
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
                    rightmost_floor_end = generate_new_segment(player, floors, platforms, obstacles, coins, power_ups, camera_x, WIDTH)
                
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
                    
                    # Submit score to leaderboard
                    if IS_WEB:
                        current_personality = message_manager.llm_handler.get_current_personality()
                        submit_score(current_personality, player.score)
                
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
                
                score_text = render_retro_text(f"Player: {message_manager.llm_handler.get_current_personality()}", 24, BLUE)
                score_rect = score_text.get_rect(center=(WIDTH // 2, PLAY_AREA_HEIGHT // 2))
                screen.blit(score_text, score_rect)

                score_text = render_retro_text(f"Final Score: {player.score}", 24, BLUE)
                score_rect = score_text.get_rect(center=(WIDTH // 2, PLAY_AREA_HEIGHT // 2 + 50))
                screen.blit(score_text, score_rect)
                
                # Draw UI to ensure status messages continue to be displayed
                draw_ui(screen, player)
            
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
                
                # Change to a new personality if LLM is available
                if message_manager.llm_handler.is_available():
                    try:
                        new_personality = message_manager.llm_handler.change_personality()
                        message_manager.set_message(f"{random.choice(NEW_PERSONALITY_MESSAGES)} {new_personality.lower()}.")
                        logger.info(f"Changed personality to {new_personality}")
                    except Exception as e:
                        # Handle case where personality change fails for some reason
                        logger.warning(f"Failed to change personality: {str(e)}")
                        message_manager.set_message(random.choice(WELCOME_BACK_MESSAGES))
                else:
                    # LLM service is not available
                    message_manager.llm_handler.personality = DEFAULT_PERSONALITY
                    message_manager.set_message(random.choice(WELCOME_BACK_MESSAGES))
                
                # Refresh leaderboard at start of new game
                if IS_WEB:
                    fetch_leaderboard()

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
    if IS_WEB:
        # In web environment, we need to be careful with asyncio
        # Use the existing event loop instead of creating a new one
        loop = asyncio.get_event_loop()
        loop.create_task(main())
    else:
        # In desktop environment, we can use asyncio.run
        asyncio.run(main())
except Exception as e:
    logger.error(f"Failed to start game: {str(e)}", exc_info=True)
    if not IS_WEB:
        exit()