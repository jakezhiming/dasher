from compat import pygame
import random
from constants.player import (
    PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_INITIAL_X, PLAYER_INITIAL_Y,
    GRAVITY, FLYING_GRAVITY_REDUCTION, INVINCIBILITY_DURATION, INVINCIBILITY_FROM_DAMAGE_DURATION, 
    IMMOBILIZED_DURATION, INITIAL_LIVES, HURT_ANIMATION_DURATION, DEATH_ANIMATION_DURATION,
    SPEED_BOOST_DURATION, MAX_BACKTRACK_DISTANCE
)
from constants.screen import PLAY_AREA_HEIGHT
from constants.colors import DARK_RED, LIGHT_BLUE
from constants.animation import PLAYER_ANIMATION_SPEED, DEATH_ANIMATION_FRAME_DELAY, SPEED_BOOST_ANIMATION_FACTOR
from utils import collide
from assets_loader import get_frame, player_frames, get_cloud_image
import input_handler
import math
from effects import effect_manager
from logger import get_module_logger

logger = get_module_logger('player')

class Player:
    def __init__(self, x=PLAYER_INITIAL_X, y=PLAYER_INITIAL_Y):
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.jumping = False
        self.double_jumped = False  # Track if player has used their double jump
        self.direction = 'right'
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_flash = False  # New variable to track flashing state
        self.invincible_flash_timer = 0  # Timer for flashing effect
        self.invincible_from_damage = False  # Track if invincibility is from damage
        self.lives = INITIAL_LIVES
        self.score = 0
        self.coin_score = 0  # Separate score for coins
        self.speed_boost = False
        self.speed_boost_timer = 0
        self.trail_positions = []  # Store previous positions for speed boost trail effect
        self.flying = False
        self.flying_timer = 0
        self.immobilized = False
        self.immobilized_timer = 0
        self.respawn_x = self.x
        self.respawn_y = self.y
        self.furthest_right_position = self.x  # Track the furthest right position
        self.prev_x = self.x  # Added to track previous x position
        self.prev_y = self.y  # Added to track previous y position
        
        # Animation properties
        self.animation_frame = 0
        self.animation_speed = PLAYER_ANIMATION_SPEED
        self.animation_timer = 0
        self.dust_animation_frame = 0
        self.dust_animation_timer = 0
        self.show_dust = False
        self.double_jump_dust_frame = 0
        self.double_jump_dust_timer = 0
        self.show_double_jump_dust = False
        self.hurt_animation_active = False
        self.hurt_animation_timer = 0
        self.hurt_animation_duration = HURT_ANIMATION_DURATION
        
        # Death animation properties
        self.dying = False
        self.death_animation_frame = 0
        self.death_animation_timer = 0
        self.death_animation_complete = False
        self.death_animation_duration = DEATH_ANIMATION_DURATION
        
        # Sprite dimensions (will be updated when sprites are loaded)
        self.sprite_width = self.width
        self.sprite_height = self.height
        self.sprite_offset_x = 0
        self.sprite_offset_y = 0

    def draw(self, screen, camera_x):
        screen_x = self.x - camera_x
        
        # Draw speed boost trail if active
        if self.speed_boost and not self.dying:
            self._draw_speed_trail(screen, camera_x)
        
        # Determine which animation to use based on player state
        animation_key = self._get_animation_key()
        
        # Update animation frame
        current_time = pygame.time.get_ticks()
        
        # Handle death animation separately with slower speed
        if self.dying:
            if current_time - self.death_animation_timer > DEATH_ANIMATION_FRAME_DELAY:
                self.death_animation_frame += 1
                self.death_animation_timer = current_time
                
                # Check if death animation is complete
                if self.death_animation_frame >= len(player_frames['death_right']):
                    self.death_animation_complete = True
                    self.death_animation_frame = len(player_frames['death_right']) - 1  # Stay on last frame
        else:
            # Normal animation update
            # Adjust animation speed for running with speed boost
            animation_speed = self.animation_speed
            if self.speed_boost and 'run' in animation_key:
                # Make running animation faster when speed boost is active
                animation_speed *= SPEED_BOOST_ANIMATION_FACTOR
                
            if current_time - self.animation_timer > 1000 * animation_speed:
                self.animation_frame += 1
                self.animation_timer = current_time
        
        # Get the current frame
        if self.dying:
            # Use death animation frame
            dir_suffix = '_right' if self.direction == 'right' else '_left'
            frame = get_frame('death' + dir_suffix, self.death_animation_frame)
        else:
            # Use normal animation frame
            frame = get_frame(animation_key, self.animation_frame)
        
        # Calculate sprite position (center the sprite on the player's hitbox)
        self.sprite_width = frame.get_width()
        self.sprite_height = frame.get_height()
        
        # Center the sprite horizontally within the hitbox
        self.sprite_offset_x = (self.width - self.sprite_width) // 2
        
        # Align the bottom of the sprite with the bottom of the hitbox
        # This ensures the feet are at the bottom of the collision box
        self.sprite_offset_y = self.height - self.sprite_height
        
        # Draw the sprite
        sprite_x = screen_x + self.sprite_offset_x
        sprite_y = self.y + self.sprite_offset_y
        
        # Add motion blur effect when speed boost is active and moving
        if self.speed_boost and abs(self.vx) > 3 and not self.dying:
            # Create a motion blur by drawing faded copies of the sprite
            blur_count = 2  # Number of blur images
            for i in range(1, blur_count + 1):
                # Calculate offset based on direction and blur index
                blur_offset = i * 10 * (-1 if self.direction == 'right' else 1)
                
                # Create a copy of the frame with reduced alpha
                blur_frame = frame.copy()
                blur_frame.set_alpha(64 - i * 20)  # Decrease alpha for each blur copy
                
                # Draw the blur frame
                screen.blit(blur_frame, (sprite_x + blur_offset, sprite_y))
        
        # If invincible from damage and not dying, make the sprite flash
        if self.invincible and self.invincible_from_damage and not self.dying:
            if self.invincible_flash:
                # Draw the sprite with a red tint
                tinted_frame = frame.copy()
                tinted_frame.fill(DARK_RED, special_flags=pygame.BLEND_RGB_MULT)
                screen.blit(tinted_frame, (sprite_x, sprite_y))
            else:
                # Draw the normal sprite
                screen.blit(frame, (sprite_x, sprite_y))
        else:
            # Draw normally if not invincible from damage or if dying
            if self.invincible and not self.invincible_from_damage and not self.dying:
                # Make the player translucent when invincible from powerup
                translucent_frame = frame.copy()
                translucent_frame.set_alpha(64)  # 25% opacity
                screen.blit(translucent_frame, (sprite_x, sprite_y))
            else:
                # Draw the normal sprite
                screen.blit(frame, (sprite_x, sprite_y))
        
        # Draw cloud effect at player's feet when flying power-up is active
        # Drawing after the player sprite so it appears in front
        if self.flying and not self.dying:
            # Get the cloud image if it hasn't been loaded yet
            if not hasattr(self, 'cloud_image'):
                # Try to get the cloud image from utils
                original_cloud = get_cloud_image()
                
                if original_cloud is not None:
                    # Scale it to an appropriate size for the player
                    cloud_width = self.width * 4
                    cloud_height = self.height * 3
                    self.cloud_image = pygame.transform.scale(original_cloud, (cloud_width, cloud_height))
                else:
                    # Fallback to loading directly if the utils function returned None
                    try:
                        self.cloud_image = pygame.image.load('assets/images/background/cloud_lonely.png').convert_alpha()
                        cloud_width = self.width * 4
                        cloud_height = self.height * 3
                        self.cloud_image = pygame.transform.scale(self.cloud_image, (cloud_width, cloud_height))
                    except Exception as e:
                        logger.error(f"Error loading cloud image: {e}")
                        exit()

            # Position the cloud based on player direction
            if self.direction == 'right':
                cloud_x = screen_x - self.width - 60
                cloud_image = self.cloud_image
            else:
                # Flip the cloud image when facing left
                cloud_x = screen_x + self.width - 85
                cloud_image = pygame.transform.flip(self.cloud_image, True, False)  # Flip horizontally
                
            cloud_y = self.y + self.height - 38
            
            # Draw the cloud with slight bobbing motion
            bob_offset = math.sin(pygame.time.get_ticks() * 0.005) * 2  # Gentle bobbing motion
            screen.blit(cloud_image, (cloud_x, cloud_y + bob_offset))
        
        # Draw dust effects if needed and not dying
        if not self.dying:
            self._draw_dust_effects(screen, screen_x)
        
        # Draw hitbox for debugging if enabled
        if input_handler.show_debug:
            # Draw the collision rect in red
            collision_rect = self.get_collision_rect()
            pygame.draw.rect(screen, (255, 0, 0, 128), 
                            (collision_rect.x - camera_x, collision_rect.y, 
                             collision_rect.width, collision_rect.height), 1)

    def _get_animation_key(self):
        """Determine which animation to use based on player state."""
        # Determine direction suffix
        dir_suffix = '_right' if self.direction == 'right' else '_left'
        
        # Check for special states in priority order
        
        # 1. Hurt animation when taking damage
        if self.invincible_from_damage:
            # Check if we're within the hurt animation duration
            current_time = pygame.time.get_ticks()
            if current_time - self.hurt_animation_timer < self.hurt_animation_duration:
                return 'hurt' + dir_suffix
        
        # 2. Invincibility from power-up
        if self.invincible and not self.invincible_from_damage:
            return 'invincible' + dir_suffix
        
        # 3. Flying
        elif self.flying:
            return 'flying' + dir_suffix
        
        # 4. Jumping/Double jumping
        elif self.jumping:
            if self.double_jumped:
                return 'double_jump' + dir_suffix
            else:
                return 'jump' + dir_suffix
        
        # 5. Speed boost (when running)
        elif self.speed_boost and self.vx != 0:
            return 'speed_boost' + dir_suffix
            
        # 6. Default: running or idle
        elif self.vx != 0:
            return 'run' + dir_suffix
        else:
            return 'idle' + dir_suffix

    def _draw_dust_effects(self, screen, screen_x):
        """Draw dust effects for walking and double jumping."""
        current_time = pygame.time.get_ticks()
        
        # Draw walking dust if player is moving on the ground
        if not self.jumping and abs(self.vx) > 0:
            # Show dust effect
            if not self.show_dust:
                self.show_dust = True
                self.dust_animation_frame = 0
                self.dust_animation_timer = current_time
            
            # Update dust animation
            dust_animation_speed = 0.1
            # Speed up dust animation when speed boost is active
            if self.speed_boost:
                dust_animation_speed *= 0.6  # 40% faster dust animation
                
            if current_time - self.dust_animation_timer > 1000 * dust_animation_speed:
                self.dust_animation_frame += 1
                self.dust_animation_timer = current_time
                
                # Reset animation when complete
                if self.dust_animation_frame >= len(player_frames['dust_walk']):
                    self.dust_animation_frame = 0
            
            # Draw dust at player's feet
            dust_frame = get_frame('dust_walk', self.dust_animation_frame)
            
            # Position dust based on player direction
            if self.direction == 'right':
                dust_x = screen_x - 20  # Behind player when moving right
            else:
                dust_x = screen_x + self.width - 10  # Behind player when moving left
                
            dust_y = self.y + self.height - 20  # At player's feet
            
            screen.blit(dust_frame, (dust_x, dust_y))
        else:
            self.show_dust = False
        
        # Double jump dust
        if self.show_double_jump_dust:
            # Speed up double jump dust animation when speed boost is active
            double_jump_dust_speed = 100
            if self.speed_boost:
                double_jump_dust_speed = 60  # 40% faster animation
                
            if current_time - self.double_jump_dust_timer > double_jump_dust_speed:
                self.double_jump_dust_frame += 1
                self.double_jump_dust_timer = current_time
                
                # Check if we've reached the end of the double jump dust animation
                if self.double_jump_dust_frame >= len(player_frames['dust_double_jump']):
                    self.show_double_jump_dust = False
            
            # Only draw if the animation is still active
            if self.show_double_jump_dust:
                dust_frame = get_frame('dust_double_jump', self.double_jump_dust_frame)
                
                # Position dust at the player's feet
                dust_x = screen_x + (self.width - dust_frame.get_width()) // 2
                dust_y = self.y + self.height - dust_frame.get_height()
                
                # Draw the dust effect
                screen.blit(dust_frame, (dust_x, dust_y))
                
                # Add extra effects for speed boost
                if self.speed_boost:
                    # Draw a slightly larger version behind for a more dramatic effect
                    larger_frame = pygame.transform.scale(
                        dust_frame, 
                        (int(dust_frame.get_width() * 1.2), int(dust_frame.get_height() * 1.2))
                    )
                    larger_x = dust_x - (larger_frame.get_width() - dust_frame.get_width()) // 2
                    larger_y = dust_y - (larger_frame.get_height() - dust_frame.get_height()) // 2
                    screen.blit(larger_frame, (larger_x, larger_y))

    def _draw_speed_trail(self, screen, camera_x):
        """Draw a trail effect behind the player when speed boost is active."""
        # Calculate screen_x for this method
        screen_x = self.x - camera_x
        
        # Add a speed line effect when moving fast
        if abs(self.vx) >= 5:
            line_length = min(30, abs(self.vx) * 3)
            line_start_x = screen_x + (0 if self.direction == 'right' else self.width)
            line_start_y = self.y + self.height // 2
            
            for i in range(1):
                y_offset = random.randint(-10, 10)
                line_end_x = line_start_x + (-line_length if self.direction == 'right' else line_length)
                pygame.draw.line(
                    screen, 
                    LIGHT_BLUE, 
                    (line_start_x, line_start_y + y_offset), 
                    (line_end_x, line_start_y + y_offset), 
                    2
                )

    def update(self, floors, platforms, obstacles, coins, power_ups):
        # If player is dying, just update the death animation and return
        if self.dying:
            # Check if death animation is complete
            if self.death_animation_complete:
                return True  # Return True to indicate game over
            return False  # Return False to continue showing death animation
            
        if self.immobilized:
            if pygame.time.get_ticks() - self.immobilized_timer > IMMOBILIZED_DURATION:
                self.immobilized = False
            return False  # Return False to indicate no game over

        # Apply gravity with reduced effect during flying
        if self.flying:
            # Apply reduced gravity during flying power-up
            self.vy += GRAVITY * FLYING_GRAVITY_REDUCTION
        else:
            # Apply normal gravity
            self.vy += GRAVITY
        
        # Store previous position before movement
        self.prev_x = self.x
        self.prev_y = self.y
        
        # Track if we're colliding with an obstacle this frame
        obstacle_collision = False
        collided_obstacle = None
        
        # Move horizontally first
        self.x += self.vx
        
        # Update player direction based on velocity
        if self.vx > 0:
            self.direction = 'right'
        elif self.vx < 0:
            self.direction = 'left'
        
        # Check for horizontal collisions with obstacles
        for obstacle in obstacles:
            if collide(self, obstacle):
                # Get the collision rectangle for the obstacle
                obstacle_rect = obstacle.get_collision_rect()
                player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
                
                # Check if player collides with the collision rectangle
                if player_rect.colliderect(obstacle_rect):
                    # Handle special case for bomb
                    if obstacle.type == 'bomb' and not obstacle.exploded:
                        # Skip bomb explosion if player is invincible from power-up
                        if not (self.invincible and not self.invincible_from_damage):
                            # Trigger bomb explosion on contact only if not invincible from power-up
                            obstacle.start_explosion()
                        # Don't count as collision yet (explosion will damage later)
                    # Skip collision handling if player is invincible from power-up (not from damage)
                    elif self.invincible and not self.invincible_from_damage:
                        # Allow player to pass through obstacles when invincible from power-up
                        pass
                    else:
                        obstacle_collision = True
                        collided_obstacle = obstacle
                        if self.vx > 0:  # Moving right
                            self.x = obstacle_rect.x - self.width  # Place player to the left of the obstacle
                        elif self.vx < 0:  # Moving left
                            self.x = obstacle_rect.x + obstacle_rect.width  # Place player to the right of the obstacle
        
        # Check for horizontal collisions with platforms (treating them as solid objects too)
        for platform in platforms:
            if collide(self, platform):
                # Only block horizontal movement if we're not landing on top
                if not (self.vy > 0 and self.prev_y + self.height <= platform.y):
                    if self.vx > 0:  # Moving right
                        self.x = platform.x - self.width
                    elif self.vx < 0:  # Moving left
                        self.x = platform.x + platform.width

        # Update furthest right position if player moves further right
        if self.x > self.furthest_right_position:
            self.furthest_right_position = self.x

        # Calculate dynamic left boundary based on furthest right position
        dynamic_left_boundary = max(0, self.furthest_right_position - MAX_BACKTRACK_DISTANCE)
        
        # Prevent moving left past the dynamic left boundary
        if self.x < dynamic_left_boundary:
            self.x = dynamic_left_boundary
        
        # Now move vertically
        self.y += self.vy

        # Collide with floors
        for floor in floors:
            if collide(self, floor) and self.vy > 0:
                self.y = floor.y - self.height
                self.vy = 0
                self.jumping = False
                self.double_jumped = False  # Reset double jump when landing
                self.respawn_x = self.x
                self.respawn_y = self.y

        # Collide with platforms - improved to prevent falling through at high speeds
        for platform in platforms:
            # Check if player is currently colliding with platform
            if collide(self, platform):
                # Case 1: Player is landing on top of the platform
                if (self.vy > 0 and  # Moving downward
                    (self.y + self.height <= platform.y + 10 or  # Either feet are near the top
                     self.prev_y + self.height <= platform.y)):  # OR was above the platform in previous frame
                    self.y = platform.y - self.height
                    self.vy = 0
                    self.jumping = False
                    self.double_jumped = False  # Reset double jump when landing
                    self.respawn_x = self.x
                    self.respawn_y = self.y
                # Case 2: Player is hitting the bottom or sides of the platform
                elif self.vy < 0:  # Moving up
                    self.y = platform.y + platform.height
                    self.vy = 0  # Stop upward movement
            
            # Additional check for tunneling: check if player "jumped over" the platform in this frame
            # This handles cases where player moved so fast they went from below to above the platform in one frame
            elif (not collide(self, platform) and  # Not currently colliding
                  self.prev_y + self.height > platform.y + platform.height and  # Was below the platform
                  self.y < platform.y and  # Now above the platform
                  self.x + self.width > platform.x and self.x < platform.x + platform.width):  # Horizontally aligned
                # Player tunneled through the platform, place them on top
                self.y = platform.y - self.height
                self.vy = 0
                self.jumping = False
                self.double_jumped = False
                self.respawn_x = self.x
                self.respawn_y = self.y

        # Vertical collision with obstacles
        for obstacle in obstacles:
            if collide(self, obstacle):
                # Get the collision rectangle for the obstacle
                obstacle_rect = obstacle.get_collision_rect()
                player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
                
                # Check if player collides with the collision rectangle
                if player_rect.colliderect(obstacle_rect):
                    # Handle special case for bomb
                    if obstacle.type == 'bomb' and not obstacle.exploded:
                        # Skip bomb explosion if player is invincible from power-up
                        if not (self.invincible and not self.invincible_from_damage):
                            # Trigger bomb explosion on contact only if not invincible from power-up
                            obstacle.start_explosion()
                        # Don't count as collision yet (explosion will damage later)
                    # Skip collision handling if player is invincible from power-up (not from damage)
                    elif self.invincible and not self.invincible_from_damage:
                        # Allow player to pass through obstacles when invincible from power-up
                        pass
                    else:
                        obstacle_collision = True
                        collided_obstacle = obstacle
                        if self.vy > 0:  # Moving down
                            self.y = obstacle_rect.y - self.height
                            self.vy = 0
                            self.jumping = False
                            self.double_jumped = False
                        elif self.vy < 0:  # Moving up
                            self.y = obstacle_rect.y + obstacle_rect.height
                            self.vy = 0

        # Pit fall
        if self.y > PLAY_AREA_HEIGHT:
            self.lives -= 1
            if self.lives > 0:
                # Reset the last_life message flag if we have more than 1 life left
                from ui import message_manager, set_hearts_flash
                set_hearts_flash()  # Trigger heart flashing effect
                if self.lives > 1:
                    message_manager.shown_messages.discard("last_life")
                # Check if this is the last life
                elif self.lives == 1 and not message_manager.has_shown_message("last_life"):
                    message_manager.set_message("You're on your last life! Be careful!")
                    message_manager.mark_message_shown("last_life")
                
                # Set pit fall message
                pit_fall_messages = [
                    "Watch your step! That was a nasty fall!",
                    "Oops! Mind the gap next time!",
                    "Gravity: 1, Player: 0. Try jumping over pits!",
                    "Falling isn't flying! Jump earlier next time."
                ]
                message_manager.set_message(random.choice(pit_fall_messages))
                
                self.x = self.respawn_x
                self.y = self.respawn_y
                self.vx = 0
                self.vy = 0
                
                # Start invincibility and hurt animation
                self.start_invincibility(from_damage=True)
                
                self.immobilized = True
                self.immobilized_timer = pygame.time.get_ticks()
            else:
                # Start death animation
                self.start_death_animation()
                return False  # Return False to continue showing death animation

        # Handle damage from obstacle collision
        if obstacle_collision and not self.invincible:
            # Check if the obstacle has special collision handling
            take_damage = True
            if hasattr(collided_obstacle, 'handle_collision'):
                take_damage = collided_obstacle.handle_collision()
                
            if take_damage:
                self.lives -= 1
                if self.lives > 0:
                    # Reset the last_life message flag if we have more than 1 life left
                    from ui import message_manager, set_hearts_flash
                    set_hearts_flash()  # Trigger heart flashing effect
                    if self.lives > 1:
                        message_manager.shown_messages.discard("last_life")
                    # Check if this is the last life
                    elif self.lives == 1 and not message_manager.has_shown_message("last_life"):
                        message_manager.set_message("You're on your last life! Be careful!")
                        message_manager.mark_message_shown("last_life")
                    
                    # Set obstacle collision message based on obstacle type
                    if collided_obstacle:
                        if collided_obstacle.type == 'spikes':
                            message_manager.set_message("Those spikes are sharp! Be careful!")
                        elif collided_obstacle.type == 'fire':
                            message_manager.set_message("Hot hot hot! Avoid the flames!")
                        elif collided_obstacle.type == 'bomb' and collided_obstacle.exploded:
                            message_manager.set_message("BOOM! That explosion packed a punch!")
                        else:
                            obstacle_messages = [
                                "Ouch! That hurt!",
                                "Watch out for obstacles in your path!",
                                "Try jumping over obstacles next time!",
                                "That's going to leave a mark!"
                            ]
                            message_manager.set_message(random.choice(obstacle_messages))
                    
                    # Start invincibility and hurt animation
                    self.start_invincibility(from_damage=True)
                    
                    # Push player away from obstacle slightly to prevent immediate re-collision
                    if collided_obstacle:
                        # Determine push direction based on collision side
                        if self.x + self.width/2 < collided_obstacle.x + collided_obstacle.width/2:
                            # Player is to the left of obstacle center
                            self.x = collided_obstacle.x - self.width - 5
                        else:
                            # Player is to the right of obstacle center
                            self.x = collided_obstacle.x + collided_obstacle.width + 5
                else:
                    # Start death animation
                    self.start_death_animation()
                    return False  # Return False to continue showing death animation

        # Collect coins
        for coin in coins[:]:
            if collide(self, coin):
                self.coin_score += 50
                # Create collection effect at the coin's position
                effect_manager.create_coin_effect(coin.x, coin.y)
                coins.remove(coin)

        # Collect power-ups
        for power_up in power_ups[:]:
            if collide(self, power_up):
                # Create collection effect at the power-up's position
                effect_manager.create_powerup_effect(power_up.x, power_up.y, power_up.type)
                
                # Import message_manager here to avoid circular imports
                from ui import message_manager
                
                if power_up.type == 'speed':
                    self.speed_boost = True
                    self.speed_boost_timer = pygame.time.get_ticks()
                    message_manager.set_message("Super speed activated! Zoom zoom!")
                elif power_up.type == 'flying':
                    self.flying = True
                    self.flying_timer = pygame.time.get_ticks()
                    message_manager.set_message("You can fly now! Keep jumping to soar through the sky!")
                elif power_up.type == 'invincibility':
                    self.start_invincibility(from_damage=False)
                    message_manager.set_message("You're invincible! Nothing can hurt you now!")
                elif power_up.type == 'life':
                    self.add_life()
                    message_manager.set_message("Extra life obtained! Keep going!")
                power_ups.remove(power_up)

        # Update power-up effects
        current_time = pygame.time.get_ticks()
        if self.speed_boost and current_time - self.speed_boost_timer > SPEED_BOOST_DURATION:
            self.speed_boost = False
            self.trail_positions = []  # Clear trail positions when speed boost ends
        if self.flying and current_time - self.flying_timer > 5000:
            self.flying = False
        if self.invincible:
            if self.invincible_from_damage and current_time - self.invincible_timer > INVINCIBILITY_FROM_DAMAGE_DURATION:
                self.invincible = False
            elif not self.invincible_from_damage and current_time - self.invincible_timer > INVINCIBILITY_DURATION:
                self.invincible = False
                
            # Update flashing effect when invincible from damage
            if self.invincible_from_damage:
                # Flash every 100ms (10 times per second)
                if current_time - self.invincible_flash_timer > 100:
                    self.invincible_flash = not self.invincible_flash
                    self.invincible_flash_timer = current_time

        # Update score based on distance and coins
        distance_score = int((self.furthest_right_position - PLAYER_INITIAL_X) / 10)
        self.score = distance_score + self.coin_score

        # Update previous y position
        self.prev_y = self.y
        
        # Handle input and movement
        if not self.immobilized and not self.dying:
            # Use the input handler to get movement input
            input_handler.handle_input(self)
            
            # Create speed trail particles when speed boost is active (even when idle)
            if self.speed_boost:
                # Only create particles occasionally for performance
                if random.random() < 0.2:  # 20% chance each frame
                    # Position particles at the player's feet
                    particle_x = self.x + (0 if self.direction == 'right' else self.width)
                    particle_y = self.y + self.height - 5
                    effect_manager.create_speed_trail(particle_x, particle_y)
            
            # Create invincibility trail particles when invincibility is active (even when idle)
            if self.invincible and not self.invincible_from_damage:
                # Only create particles occasionally for performance
                if random.random() < 0.2:  # 20% chance each frame
                    # Position particles at the player's feet
                    particle_x = self.x + (0 if self.direction == 'right' else self.width)
                    particle_y = self.y + self.height - 5
                    effect_manager.create_invincibility_trail(particle_x, particle_y)

            if self.flying:
                # Only create particles occasionally for performance
                if random.random() < 0.2:  # 20% chance each frame
                    # Position particles at the player's feet
                    particle_x = self.x + (0 if self.direction == 'right' else self.width)
                    particle_y = self.y + self.height - 5
                    effect_manager.create_flying_trail(particle_x, particle_y)
        
        return False  # Return False to indicate no game over

    def start_invincibility(self, from_damage=False):
        self.invincible = True
        self.invincible_timer = pygame.time.get_ticks()
        self.invincible_from_damage = from_damage
        
        # Initialize flashing effect when taking damage
        if from_damage:
            self.invincible_flash = True
            self.invincible_flash_timer = pygame.time.get_ticks()
            # Reset the hurt animation timer when taking damage
            self.hurt_animation_timer = pygame.time.get_ticks()
            # Reset animation frame to start the hurt animation from the beginning
            self.animation_frame = 0

    def start_death_animation(self):
        """Start the death animation sequence"""
        self.dying = True
        self.death_animation_frame = 0
        self.death_animation_timer = pygame.time.get_ticks()
        self.death_animation_complete = False
        
        # Stop all movement
        self.vx = 0
        self.vy = 0
        
        # Disable other states
        self.jumping = False
        self.double_jumped = False
        self.speed_boost = False
        self.flying = False
        self.invincible = False
        self.immobilized = False
        self.trail_positions = []  # Clear trail positions
        
        # Set death message
        from ui import message_manager
        death_messages = [
            "Game Over! Better luck next time!",
            "You ran out of lives! Try again?",
            "The adventure ends here... for now!",
            "Ouch! That was your last life!"
        ]
        message_manager.set_message(random.choice(death_messages))

    def add_life(self):
        """Add a life to the player and reset the last_life message flag."""
        self.lives += 1
        # Reset the last_life message flag so it can be shown again if needed
        from ui import message_manager, set_heart_pop_in, set_plus_indicator_animation
        message_manager.shown_messages.discard("last_life")
        
        # Determine which animation to trigger based on the number of lives
        max_displayed_hearts = 5
        if self.lives <= max_displayed_hearts:
            # If we're showing individual hearts, animate the newly added heart
            set_heart_pop_in(self.lives - 1)
        else:
            # If we're showing the "+X" indicator, animate that instead
            set_plus_indicator_animation()

    def perform_double_jump(self):
        """Perform a double jump and show the dust effect."""
        self.double_jumped = True
        self.show_double_jump_dust = True
        self.double_jump_dust_frame = 0
        self.double_jump_dust_timer = pygame.time.get_ticks() 

    def get_collision_rect(self):
        """Return a slightly smaller collision rectangle for the player.
        This makes the collision box 5 pixels smaller from the top, left, and right."""
        return pygame.Rect(
            self.x + 5,  # 5px in from the left
            self.y + 5,  # 5px in from the top
            self.width - 10,  # 5px in from both left and right (total 10px reduction)
            self.height - 5  # 5px in from the top only
        ) 

    def _handle_movement(self):
        """Handle player movement based on input."""
        # Use the input handler to get movement input
        input_handler.handle_input(self)
        
        # Limit falling speed
        if self.vy > 15:
            self.vy = 15 

    def reset(self):
        """Reset the player after death."""
        self.x = self.respawn_x
        self.y = self.respawn_y
        self.vx = 0
        self.vy = 0
        self.jumping = False
        self.double_jumped = False
        self.dying = False
        self.death_animation_frame = 0
        self.death_animation_complete = False
        self.speed_boost = False
        self.trail_positions = []  # Clear trail positions
        self.flying = False
        self.invincible = False 