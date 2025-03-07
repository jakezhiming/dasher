import pygame
from constants import (
    PLAY_AREA_HEIGHT, GRAVITY, INVINCIBILITY_DURATION, IMMOBILIZED_DURATION,
    RED, DARK_RED, PURPLE, BLACK
)
from utils import collide

class Player:
    def __init__(self):
        self.width = 50
        self.height = 50
        self.x = 100
        self.y = PLAY_AREA_HEIGHT - self.height - 20
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
        self.lives = 3
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

    def draw(self, screen, camera_x):
        screen_x = self.x - camera_x
        
        # Determine player color
        if self.invincible:
            # Flash every 100ms
            current_time = pygame.time.get_ticks()
            if current_time - self.invincible_flash_timer > 100:
                self.invincible_flash = not self.invincible_flash
                self.invincible_flash_timer = current_time
            
            if self.invincible_from_damage:
                # Flash between DARK_RED and RED for damage invincibility
                color = DARK_RED if self.invincible_flash else RED
            else:
                # Flash between PURPLE and RED for power-up invincibility
                color = PURPLE if self.invincible_flash else RED
        else:
            color = RED
            
        pygame.draw.rect(screen, color, (screen_x, self.y, self.width, self.height))
        
        # Eyes based on direction
        eye_y = int(self.y + 10)
        if self.direction == 'right':
            pygame.draw.circle(screen, BLACK, (int(screen_x + 30), eye_y), 5)
            pygame.draw.circle(screen, BLACK, (int(screen_x + 40), eye_y), 5)
        else:
            pygame.draw.circle(screen, BLACK, (int(screen_x + 10), eye_y), 5)
            pygame.draw.circle(screen, BLACK, (int(screen_x + 20), eye_y), 5)

    def update(self, floors, platforms, obstacles, coins, power_ups):
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
        
        # Check for horizontal collisions with obstacles
        for obstacle in obstacles:
            if collide(self, obstacle):
                obstacle_collision = True
                collided_obstacle = obstacle
                if self.vx > 0:  # Moving right
                    self.x = obstacle.x - self.width  # Place player to the left of the obstacle
                elif self.vx < 0:  # Moving left
                    self.x = obstacle.x + obstacle.width  # Place player to the right of the obstacle
        
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

        # Collide with platforms
        for platform in platforms:
            if (collide(self, platform) and 
                self.vy > 0 and 
                self.y + self.height <= platform.y + 10 and  # Check if player's feet are near the top of platform
                self.prev_y + self.height <= platform.y):    # Check if player was above the platform in the previous frame
                self.y = platform.y - self.height
                self.vy = 0
                self.jumping = False
                self.double_jumped = False  # Reset double jump when landing
                self.respawn_x = self.x
                self.respawn_y = self.y
            # Handle vertical collision with platform sides
            elif collide(self, platform) and not (self.vy > 0 and self.prev_y + self.height <= platform.y):
                if self.vy < 0:  # Moving up
                    self.y = platform.y + platform.height
                    self.vy = 0  # Stop upward movement

        # Vertical collision with obstacles
        for obstacle in obstacles:
            if collide(self, obstacle):
                obstacle_collision = True
                collided_obstacle = obstacle
                if self.vy > 0:  # Moving down
                    self.y = obstacle.y - self.height
                    self.vy = 0
                    self.jumping = False
                    self.double_jumped = False
                elif self.vy < 0:  # Moving up
                    self.y = obstacle.y + obstacle.height
                    self.vy = 0

        # Pit fall
        if self.y > PLAY_AREA_HEIGHT:
            self.lives -= 1
            if self.lives > 0:
                # Reset the last_life message flag if we have more than 1 life left
                from ui import message_manager
                if self.lives > 1:
                    message_manager.shown_messages.discard("last_life")
                self.x = self.respawn_x
                self.y = self.respawn_y
                self.vx = 0
                self.vy = 0
                self.start_invincibility(from_damage=True)
                self.immobilized = True
                self.immobilized_timer = pygame.time.get_ticks()
            else:
                return True  # Return True to indicate game over

        # Handle damage from obstacle collision
        if obstacle_collision and not self.invincible:
            self.lives -= 1
            if self.lives > 0:
                # Reset the last_life message flag if we have more than 1 life left
                from ui import message_manager
                if self.lives > 1:
                    message_manager.shown_messages.discard("last_life")
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
                return True  # Return True to indicate game over

        # Collect coins
        for coin in coins[:]:
            if collide(self, coin):
                self.coin_score += 10
                coins.remove(coin)

        # Collect power-ups
        for power_up in power_ups[:]:
            if collide(self, power_up):
                if power_up.type == 'speed':
                    self.speed_boost = True
                    self.speed_boost_timer = pygame.time.get_ticks()
                elif power_up.type == 'flying':
                    self.flying = True
                    self.flying_timer = pygame.time.get_ticks()
                elif power_up.type == 'invincibility':
                    self.start_invincibility(from_damage=False)
                elif power_up.type == 'life':
                    self.add_life()
                power_ups.remove(power_up)

        # Update power-up effects
        current_time = pygame.time.get_ticks()
        if self.speed_boost and current_time - self.speed_boost_timer > 5000:
            self.speed_boost = False
        if self.flying and current_time - self.flying_timer > 5000:
            self.flying = False
        if self.invincible and current_time - self.invincible_timer > INVINCIBILITY_DURATION:
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

    def add_life(self):
        """Add a life to the player and reset the last_life message flag."""
        self.lives += 1
        # Reset the last_life message flag so it can be shown again if needed
        from ui import message_manager
        message_manager.shown_messages.discard("last_life")
        # Display a message when a life is added
        message_manager.set_message("Yippee! Extra life collected!") 