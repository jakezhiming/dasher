import asyncio
import pygame
from src.utils.compat import random, IS_WEB
from src.core.assets_loader import load_all_assets
from src.constants.colors import BLUE, RED
from src.constants.screen import WIDTH, HEIGHT, PLAY_AREA_HEIGHT
from src.constants.game_states import (
    GAME_RUNNING,
    GAME_LOST_MESSAGE,
    GAME_OVER,
    GAME_OVER_DISPLAY_DURATION,
)
from src.constants.messages import (
    WELCOME_MESSAGES,
    NEW_PERSONALITY_MESSAGES,
    WELCOME_BACK_MESSAGES,
    DEFAULT_PERSONALITY,
)
from src.utils.utils import render_retro_text, draw_background
from src.entities.player import Player
from src.entities.game_objects import Floor
from src.ui.ui import draw_ui, draw_debug_info
from src.entities.messages import message_manager
import src.core.input_handler as input_handler
from src.level.level_generator import generate_new_segment, remove_old_objects
from src.entities.effects import effect_manager
from src.utils.logger import logger, get_module_logger
from src.services.leaderboard import fetch_leaderboard, submit_score_and_wait

logger = get_module_logger("game")


class Game:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        logger.info("Pygame initialized")

        # Screen setup
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Dasher")
        self.clock = pygame.time.Clock()
        logger.info(f"Screen setup complete: {WIDTH}x{HEIGHT}")

        # Load game assets
        try:
            load_all_assets()
            logger.info("Game assets loaded")
        except Exception as e:
            logger.error(f"Failed to load assets: {str(e)}")
            exit()

        # Set starting personality
        self.set_personality()

        # Initialize game state
        self.reset_game()

    def reset_game(self):
        # Initialize game
        self.player = Player()
        self.camera_x = 0
        self.rightmost_floor_end = WIDTH
        self.floors = [Floor(0, WIDTH)]
        self.platforms = []
        self.obstacles = []
        self.coins = []
        self.power_ups = []
        self.game_over = False
        self.game_state = GAME_RUNNING
        self.game_over_timer = 0
        self.player_has_moved = False
        self.score_submitted = False
        self.running = True
        self.frame_count = 0
        self.last_time = pygame.time.get_ticks()

        # Reset conversation history for new game
        try:
            message_manager.llm_handler.reset_conversation_history()
        except Exception as e:
            logger.warning(f"Failed to reset conversation history: {str(e)}")

        # Update leaderboard display at start
        if IS_WEB:
            fetch_leaderboard()

        logger.info("Game initialized/reset")

    def set_personality(self, start_game=True):
        # Starting personality
        if message_manager.llm_handler.is_available():
            if start_game:
                starting_personality = message_manager.llm_handler.change_personality()
                logger.info(f"Starting personality: {starting_personality}")
                try:
                    message_manager.set_message(random.choice(WELCOME_MESSAGES))
                except Exception as e:
                    logger.warning(f"Failed to set welcome message: {str(e)}")
            else:
                try:
                    new_personality = message_manager.llm_handler.change_personality()
                    message_manager.set_message(
                        f"{random.choice(NEW_PERSONALITY_MESSAGES)} {new_personality.lower()}."
                    )
                    logger.info(f"Changed personality to {new_personality}")
                except Exception as e:
                    logger.warning(f"Failed to change personality: {str(e)}")
        else:
            # LLM service is not available
            message_manager.llm_handler.personality = DEFAULT_PERSONALITY
            if start_game:
                message_manager.set_message(random.choice(WELCOME_MESSAGES))
            else:
                message_manager.set_message(random.choice(WELCOME_BACK_MESSAGES))
            logger.info(
                f"Using personality: {message_manager.llm_handler.get_current_personality()}"
            )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("Game quit requested")
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize for web compatibility
                logger.debug(f"Window resized to {event.w}x{event.h}")
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

    def update(self, dt):
        # Update message manager
        try:
            message_manager.update()
        except Exception as e:
            logger.error(f"Error updating message manager: {e}")

        # Update game state
        if self.game_state == GAME_RUNNING:
            # Game logic
            self.player_has_moved = (
                input_handler.handle_input(self.player) or self.player_has_moved
            )

            self.game_over = self.player.update(
                self.floors, self.platforms, self.obstacles, self.coins, self.power_ups
            )

            # If game_over is True, the player has completed their death animation
            if self.game_over:
                self.game_state = GAME_LOST_MESSAGE
                self.game_over_timer = pygame.time.get_ticks()

            self.camera_x = input_handler.update_scroll(self.player, self.camera_x)

            # Update animations for coins and power-ups
            for coin in self.coins:
                coin.update(dt)
            for power_up in self.power_ups:
                power_up.update(dt)
            # Update animations for obstacles
            for obstacle in self.obstacles:
                obstacle.update(dt)

            # Update effects
            effect_manager.update(dt)

            if self.camera_x + WIDTH > self.rightmost_floor_end - 600:
                self.rightmost_floor_end = generate_new_segment(
                    self.player,
                    self.floors,
                    self.platforms,
                    self.obstacles,
                    self.coins,
                    self.power_ups,
                    self.camera_x,
                    WIDTH,
                )

            self.floors, self.platforms, self.obstacles, self.coins, self.power_ups = (
                remove_old_objects(
                    self.player,
                    self.floors,
                    self.platforms,
                    self.obstacles,
                    self.coins,
                    self.power_ups,
                )
            )

        elif self.game_state == GAME_LOST_MESSAGE:
            # Show game over message for a few seconds
            if (
                pygame.time.get_ticks() - self.game_over_timer
                > GAME_OVER_DISPLAY_DURATION
            ):
                self.game_state = GAME_OVER
                logger.info(f"Game over")
                return (
                    True  # Signal that the game is over and score should be submitted
                )

        elif self.game_state == GAME_OVER:
            # Reset the game
            self.reset_game()
            # After reset, change personality for the new game
            self.set_personality(start_game=False)

        return False  # Continue normal game loop

    def draw(self):
        # Visible range for culling objects outside view
        visible_range = (self.camera_x - 100, self.camera_x + WIDTH + 100)

        if self.game_state == GAME_RUNNING or self.game_state == GAME_LOST_MESSAGE:
            # Draw background
            draw_background(self.screen, self.camera_x)

            # Draw game objects
            for floor in self.floors:
                if (
                    floor.x + floor.width >= visible_range[0]
                    and floor.x <= visible_range[1]
                ):
                    floor.draw(self.screen, self.camera_x)

            for platform in self.platforms:
                if (
                    platform.x + platform.width >= visible_range[0]
                    and platform.x <= visible_range[1]
                ):
                    platform.draw(self.screen, self.camera_x)

            for obstacle in self.obstacles:
                if (
                    obstacle.x + obstacle.width >= visible_range[0]
                    and obstacle.x <= visible_range[1]
                ):
                    obstacle.draw(self.screen, self.camera_x)

            for coin in self.coins:
                if (
                    coin.x + coin.width >= visible_range[0]
                    and coin.x <= visible_range[1]
                ):
                    coin.draw(self.screen, self.camera_x)

            for power_up in self.power_ups:
                if (
                    power_up.x + power_up.width >= visible_range[0]
                    and power_up.x <= visible_range[1]
                ):
                    power_up.draw(self.screen, self.camera_x)

            self.player.draw(self.screen, self.camera_x)

            # Draw effects
            effect_manager.draw(self.screen, self.camera_x)

            draw_ui(self.screen, self.player)

            # Draw debug info if enabled
            if input_handler.show_debug:
                draw_debug_info(self.screen, self.player)

            # Draw welcome text if player hasn't moved yet
            if not self.player_has_moved and self.game_state == GAME_RUNNING:
                text = render_retro_text("Welcome to Dasher", 28, BLUE)
                text_rect = text.get_rect(
                    center=(WIDTH // 2, PLAY_AREA_HEIGHT // 2 - 50)
                )
                self.screen.blit(text, text_rect)

            # Draw game over text if in game lost message state
            if self.game_state == GAME_LOST_MESSAGE:
                game_over_text = render_retro_text("GAME OVER", 36, RED)
                game_over_rect = game_over_text.get_rect(
                    center=(WIDTH // 2, PLAY_AREA_HEIGHT // 2 - 50)
                )
                self.screen.blit(game_over_text, game_over_rect)

                personality_text = render_retro_text(
                    f"Player: {message_manager.llm_handler.get_current_personality()}",
                    24,
                    BLUE,
                )
                personality_rect = personality_text.get_rect(
                    center=(WIDTH // 2, PLAY_AREA_HEIGHT // 2)
                )
                self.screen.blit(personality_text, personality_rect)

                score_text = render_retro_text(
                    f"Final Score: {self.player.score}", 24, BLUE
                )
                score_rect = score_text.get_rect(
                    center=(WIDTH // 2, PLAY_AREA_HEIGHT // 2 + 50)
                )
                self.screen.blit(score_text, score_rect)

    async def run(self):
        logger.info("Game started")

        try:
            while self.running:
                # This is needed for Pygbag to work properly
                # In web environment, this allows other tasks to run
                await asyncio.sleep(0)

                # Calculate delta time for smooth animations
                current_time = pygame.time.get_ticks()
                dt = (current_time - self.last_time) / 1000.0  # Convert to seconds
                self.last_time = current_time

                self.frame_count += 1

                # Handle events
                self.handle_events()

                # Update game state
                submit_score = self.update(dt)

                # Draw the game
                self.draw()

                # Submit score if game is over and score not yet submitted
                if submit_score and IS_WEB and not self.score_submitted:
                    current_personality = (
                        message_manager.llm_handler.get_current_personality()
                    )
                    self.score_submitted = True
                    await submit_score_and_wait(current_personality, self.player.score)

                # Update the display
                pygame.display.flip()
                self.clock.tick(60)  # 60 FPS

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
