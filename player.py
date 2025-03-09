import pygame
from constants import (
    PLAY_AREA_HEIGHT, GRAVITY, INVINCIBILITY_DURATION, INVINCIBILITY_FROM_DAMAGE_DURATION, IMMOBILIZED_DURATION,
    RED, DARK_RED, PURPLE, BLACK, PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_INITIAL_X, PLAYER_INITIAL_Y,
    PLAYER_ANIMATION_SPEED, HURT_ANIMATION_DURATION, DEATH_ANIMATION_DURATION, DEATH_ANIMATION_FRAME_DELAY,
    SPEED_BOOST_ANIMATION_FACTOR, INITIAL_LIVES
)
from utils import collide
from sprite_loader import get_frame, load_player_sprites, player_frames
import input_handler
import math
import random
from collection_effects import effect_manager

class Player:
    def __init__(self):
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.x = PLAYER_INITIAL_X
        self.y = PLAYER_INITIAL_Y
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
        
        # If invincible and not dying, make the sprite flash
        if self.invincible and not self.dying:
            # Flash every 50ms
            if current_time - self.invincible_flash_timer > 50:
                self.invincible_flash = not self.invincible_flash
                self.invincible_flash_timer = current_time
            
            # Only draw the sprite every other flash cycle
            if not self.invincible_flash:
                screen.blit(frame, (sprite_x, sprite_y))
        else:
            # Draw normally if not invincible or if dying
            screen.blit(frame, (sprite_x, sprite_y))
        
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
            
            # Draw more dust particles when speed boost is active
            screen.blit(dust_frame, (dust_x, dust_y))
            
            if self.speed_boost:
                # Add extra dust particles when speed boost is active
                if self.direction == 'right':
                    screen.blit(dust_frame, (dust_x - 15, dust_y + 5))
                else:
                    screen.blit(dust_frame, (dust_x + 15, dust_y + 5))
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

        # Apply gravity
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
        from constants import MAX_BACKTRACK_DISTANCE
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
                
                if power_up.type == 'speed':
                    self.speed_boost = True
                    self.speed_boost_timer = pygame.time.get_ticks()
                elif power_up.type == 'flying':
                    self.flying = True
                    self.flying_timer = pygame.time.get_ticks()
                elif power_up.type == 'invincibility':
                    self.start_invincibility(from_damage=False)
                    # Display a message when invincibility power-up is collected
                    from ui import message_manager
                    message_manager.set_message("Super Star! You can walk through obstacles and bombs won't explode!")
                elif power_up.type == 'life':
                    self.add_life()
                power_ups.remove(power_up)

        # Update power-up effects
        current_time = pygame.time.get_ticks()
        if self.speed_boost and current_time - self.speed_boost_timer > 5000:
            self.speed_boost = False
        if self.flying and current_time - self.flying_timer > 5000:
            self.flying = False
        if self.invincible:
            if self.invincible_from_damage and current_time - self.invincible_timer > INVINCIBILITY_FROM_DAMAGE_DURATION:
                self.invincible = False
            elif not self.invincible_from_damage and current_time - self.invincible_timer > INVINCIBILITY_DURATION:
                self.invincible = False

        # Update score based on distance and coins
        distance_score = int(self.x / 10)
        self.score = distance_score + self.coin_score

        # Update previous y position
        self.prev_y = self.y
        
        return False  # Return False to indicate no game over

    def start_invincibility(self, from_damage=False):
        self.invincible = True
        self.invincible_timer = pygame.time.get_ticks()
        self.invincible_from_damage = from_damage
        
        # Reset the hurt animation timer when taking damage
        if from_damage:
            self.hurt_animation_timer = pygame.time.get_ticks()
            # Reset animation frame to start the hurt animation from the beginning
            self.animation_frame = 0

    def start_death_animation(self):
        """Start the death animation sequence."""
        self.dying = True
        self.death_animation_frame = 0
        self.death_animation_timer = pygame.time.get_ticks()
        self.death_animation_complete = False
        
        # Stop all movement
        self.vx = 0
        self.vy = 0
        
        # Disable other states
        self.invincible = False
        self.jumping = False
        self.double_jumped = False
        self.flying = False
        self.speed_boost = False
        self.immobilized = False
        
        # Display a death message
        from ui import message_manager
        message_manager.set_message("Oh no! You died!")

    def add_life(self):
        """Add a life to the player and reset the last_life message flag."""
        self.lives += 1
        # Reset the last_life message flag so it can be shown again if needed
        from ui import message_manager
        message_manager.shown_messages.discard("last_life")
        # Display a message when a life is added
        message_manager.set_message("Yippee! Extra life collected!") 
        
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