import pygame
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 800
HEIGHT = 600
STATUS_BAR_HEIGHT = 100
PLAY_AREA_HEIGHT = HEIGHT - STATUS_BAR_HEIGHT
GRAVITY = 0.45
JUMP_VELOCITY = -10
BASE_MOVE_SPEED = 6
SPEED_BOOST_MULTIPLIER = 1.25
INVINCIBILITY_DURATION = 2000  # milliseconds
IMMOBILIZED_DURATION = 1000
MAX_BACKTRACK_DISTANCE = 1000  # How far left the player can go from their furthest right position

# Difficulty scaling constants
DIFFICULTY_START_DISTANCE = 1000  # Distance at which difficulty starts increasing
DIFFICULTY_MAX_DISTANCE = 20000   # Distance at which difficulty reaches maximum
BASE_OBSTACLE_SIZE = 25           # Base size of obstacles
MAX_OBSTACLE_CHANCE = 0.9         # Maximum chance of obstacles at highest difficulty
MAX_PIT_CHANCE = 0.5              # Maximum chance of pits at highest difficulty
MIN_PIT_WIDTH = 200               # Minimum pit width at lowest difficulty
MAX_PIT_WIDTH = 500               # Maximum pit width at highest difficulty
MIN_PLATFORM_CHANCE = 0.8         # Minimum chance of platforms over pits at highest difficulty

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 60, 60)        # Softer red for player
DARK_RED = (180, 0, 0)     # Darker red for damage invincibility
GREEN = (76, 187, 23)      # Vibrant green for floors/platforms
YELLOW = (255, 215, 0)     # Gold for coins
BLUE = (30, 144, 255)      # Dodger blue for speed power-up
CYAN = (0, 191, 255)       # Deep sky blue for flying power-up
MAGENTA = (218, 112, 214)  # Orchid for other power-ups
GRAY = (128, 128, 128)     # Medium gray
ORANGE = (255, 140, 0)     # Dark orange for obstacles
PURPLE = (147, 112, 219)   # Medium purple for invincibility flashing
LIGHT_BLUE = (173, 216, 230) # Light blue for background

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dasher")
clock = pygame.time.Clock()

# Game state
space_key_pressed = False  # Track if space key was pressed in the previous frame
show_debug = False  # Initialize debug display flag
d_key_pressed = False  # Track D key state to prevent multiple toggles

# Collision detection
def collide(rect1, rect2):
    return (rect1.x < rect2.x + rect2.width and
            rect1.x + rect1.width > rect2.x and
            rect1.y < rect2.y + rect2.height and
            rect1.y + rect1.height > rect2.y)

# Player class
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

    def draw(self, camera_x):
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
        global game_over
        
        if self.immobilized:
            if pygame.time.get_ticks() - self.immobilized_timer > IMMOBILIZED_DURATION:
                self.immobilized = False
            return

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
                self.x = self.respawn_x
                self.y = self.respawn_y
                self.vx = 0
                self.vy = 0
                self.start_invincibility(from_damage=True)
                self.immobilized = True
                self.immobilized_timer = pygame.time.get_ticks()
            else:
                game_over = True

        # Handle damage from obstacle collision
        if obstacle_collision and not self.invincible:
            self.lives -= 1
            if self.lives > 0:
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
                game_over = True

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

    def start_invincibility(self, from_damage=False):
        self.invincible = True
        self.invincible_timer = pygame.time.get_ticks()
        self.invincible_from_damage = from_damage

# Floor class
class Floor:
    def __init__(self, x, width):
        self.x = x
        self.width = width
        self.height = 20
        self.y = PLAY_AREA_HEIGHT - self.height

    def draw(self, camera_x):
        pygame.draw.rect(screen, GREEN, (self.x - camera_x, self.y, self.width, self.height))

# Platform class
class Platform:
    def __init__(self, x, y, width):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20

    def draw(self, camera_x):
        pygame.draw.rect(screen, GREEN, (self.x - camera_x, self.y, self.width, self.height))

# Obstacle class
class Obstacle:
    def __init__(self, x, y, width=30, height=30):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, camera_x):
        pygame.draw.rect(screen, ORANGE, (self.x - camera_x, self.y, self.width, self.height))

# Coin class
class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20

    def draw(self, camera_x):
        pygame.draw.circle(screen, YELLOW, (int(self.x - camera_x + 10), int(self.y + 10)), 10)

# PowerUp class
class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.radius = 10  # Changed from width/height to radius
        self.type = type
        # Keep width and height properties for existing collision detection
        self.width = self.radius * 2
        self.height = self.radius * 2
        # Update center coordinates
        self.update_center()
        
    def update_center(self):
        # Calculate center coordinates based on top-left position
        self.center_x = self.x + self.radius
        self.center_y = self.y + self.radius

    def draw(self, camera_x):
        color = BLUE if self.type == 'speed' else CYAN if self.type == 'flying' else MAGENTA
        # Draw a circle instead of a rectangle
        pygame.draw.circle(screen, color, (self.center_x - camera_x, self.center_y), self.radius)

# Input handling
def handle_input(player):
    global space_key_pressed, show_debug, d_key_pressed
    keys = pygame.key.get_pressed()
    
    # Toggle debug display with 'D' key
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
                player.double_jumped = True
            # Flying power-up allows continuous jumping
            elif player.flying:
                player.vy = -move_speed
        
        # Update space key state
        space_key_pressed = keys[pygame.K_SPACE]

# Scrolling
def update_scroll(player):
    global camera_x
    # Calculate dynamic left boundary based on furthest right position
    dynamic_left_boundary = max(0, player.furthest_right_position - MAX_BACKTRACK_DISTANCE)
    
    # Follow player when moving right
    if player.x > camera_x + WIDTH * 0.5:
        camera_x = player.x - WIDTH * 0.5
    # Follow player when moving left
    elif player.x < camera_x + WIDTH * 0.3:
        camera_x = max(dynamic_left_boundary, player.x - WIDTH * 0.3)

# Status bar
def draw_status_bar(player):
    # Draw lives at top left
    font = pygame.font.Font(None, 36)
    lives_text = font.render(f"Lives: {player.lives}", True, BLACK)
    screen.blit(lives_text, (10, 10))
    
    # Draw score at top right
    score_text = font.render(f"Score: {player.score}", True, BLACK)
    screen.blit(score_text, (WIDTH - 150, 10))
    
    # Status bar is kept empty as requested
    pygame.draw.rect(screen, GRAY, (0, PLAY_AREA_HEIGHT, WIDTH, STATUS_BAR_HEIGHT))

# New function to display debug information
def draw_debug_info(player):
    font = pygame.font.Font(None, 24)
    y_pos = 50  # Start position for debug info
    line_height = 25
    
    # Player position
    pos_text = font.render(f"Position: ({int(player.x)}, {int(player.y)})", True, BLACK)
    screen.blit(pos_text, (10, y_pos))
    y_pos += line_height
    
    # Player velocity
    vel_text = font.render(f"Velocity: ({int(player.vx)}, {int(player.vy)})", True, BLACK)
    screen.blit(vel_text, (10, y_pos))
    y_pos += line_height
    
    # Player state
    state_text = font.render(f"Jumping: {player.jumping}, Double jumped: {player.double_jumped}", True, BLACK)
    screen.blit(state_text, (10, y_pos))
    y_pos += line_height
    
    # Power-ups
    powerup_text = font.render(f"Speed boost: {player.speed_boost}, Flying: {player.flying}", True, BLACK)
    screen.blit(powerup_text, (10, y_pos))
    y_pos += line_height
    
    # Invincibility
    invincible_text = font.render(f"Invincible: {player.invincible} ({player.invincible_timer})", True, BLACK)
    screen.blit(invincible_text, (10, y_pos))
    y_pos += line_height
    
    # Coin score
    coin_text = font.render(f"Coins: {player.coin_score}", True, BLACK)
    screen.blit(coin_text, (10, y_pos))
    y_pos += line_height
    
    # Difficulty
    progress = max(0, player.furthest_right_position - DIFFICULTY_START_DISTANCE)
    difficulty_factor = min(1.0, progress / (DIFFICULTY_MAX_DISTANCE - DIFFICULTY_START_DISTANCE))
    difficulty_percentage = int(difficulty_factor * 100)
    difficulty_text = font.render(f"Difficulty: {difficulty_percentage}%", True, BLACK)
    screen.blit(difficulty_text, (10, y_pos))

# Generate new map segment
def generate_new_segment():
    global rightmost_floor_end, camera_x
    last_floor = floors[-1]
    new_x = last_floor.x + last_floor.width
    
    # Calculate difficulty factor (0.0 to 1.0) based on player's progress
    progress = max(0, player.furthest_right_position - DIFFICULTY_START_DISTANCE)
    difficulty_factor = min(1.0, progress / (DIFFICULTY_MAX_DISTANCE - DIFFICULTY_START_DISTANCE))
    
    # Scale pit chance and width based on difficulty
    base_pit_chance = 0.2
    pit_chance = base_pit_chance + (MAX_PIT_CHANCE - base_pit_chance) * difficulty_factor
    
    # Determine if there will be a pit
    has_pit = random.random() < pit_chance
    if has_pit:
        # Scale pit width based on difficulty
        max_pit_width = 300 + int((MAX_PIT_WIDTH - 300) * difficulty_factor)
        pit_width = random.randint(MIN_PIT_WIDTH, max_pit_width)
        new_x += pit_width
        
        # Always add a platform above the pit for the player to use
        # Ensure the platform width is appropriate for the pit width
        max_platform_width = min(150, pit_width - 120)  # Ensure there's at least 120px of space (60px on each side)
        min_platform_width = min(50, max_platform_width)  # Ensure min_platform_width is not greater than max_platform_width
        
        if max_platform_width >= min_platform_width:
            platform_width = random.randint(min_platform_width, max_platform_width)
            
            # Calculate valid range for platform placement
            min_x_position = new_x - pit_width + 50  # 50px from left edge of pit
            max_x_position = new_x - platform_width - 50  # 50px from right edge of pit
            
            # Ensure we have a valid range
            if max_x_position > min_x_position:
                platform_x = random.randint(min_x_position, max_x_position)
            else:
                # If no valid range, place platform in the middle of the pit
                platform_x = new_x - pit_width/2 - platform_width/2
                
            platform_y = random.randint(100, PLAY_AREA_HEIGHT - 150)
            platforms.append(Platform(platform_x, platform_y, platform_width))
        else:
            # If pit is too narrow for a platform, place a wider platform that extends beyond the pit
            platform_width = 150
            platform_x = new_x - pit_width - 50  # Place it starting before the pit
            platform_y = random.randint(100, PLAY_AREA_HEIGHT - 150)
            platforms.append(Platform(platform_x, platform_y, platform_width + 100))  # Make it extend beyond the pit
    
    new_width = random.randint(100, 300)
    floors.append(Floor(new_x, new_width))
    rightmost_floor_end = new_x + new_width

    # Platform (additional platforms besides the ones over pits)
    platform_chance = 0.5
    if random.random() < platform_chance:
        platforms.append(Platform(
            new_x + random.randint(0, new_width - 100),
            random.randint(100, PLAY_AREA_HEIGHT - 100),
            random.randint(50, 150)
        ))

    # Obstacle (on floor or platform)
    generated_obstacles = []
    # Scale obstacle chance based on difficulty
    base_obstacle_chance = 0.3
    obstacle_chance = base_obstacle_chance + (MAX_OBSTACLE_CHANCE - base_obstacle_chance) * difficulty_factor
    
    if random.random() < obstacle_chance:
        # Calculate the right edge of the visible screen
        visible_right_edge = camera_x + WIDTH
        
        # Ensure obstacles are generated beyond the visible area
        obstacle_x = max(visible_right_edge, new_x) + random.randint(50, 150)
        
        # Generate random width and height for the obstacle
        # Make obstacles slightly larger with difficulty
        base_width = BASE_OBSTACLE_SIZE + int(40 * difficulty_factor)
        
        # Increase chance of larger obstacles with difficulty
        # At low difficulty, bias towards smaller obstacles
        # At high difficulty, bias towards larger obstacles
        if random.random() < difficulty_factor:
            # Big obstacle - biased towards maximum size at higher difficulties
            min_size = max(BASE_OBSTACLE_SIZE, int(BASE_OBSTACLE_SIZE + 20 * difficulty_factor))
            obstacle_width = random.randint(min_size, base_width)
            obstacle_height = random.randint(min_size, base_width)
        else:
            # Regular obstacle - standard size range
            obstacle_width = random.randint(BASE_OBSTACLE_SIZE, max(BASE_OBSTACLE_SIZE + 30, int(base_width * 0.7)))
            obstacle_height = random.randint(BASE_OBSTACLE_SIZE, max(BASE_OBSTACLE_SIZE + 30, int(base_width * 0.7)))
        
        # Add a chance for extra large obstacles at high difficulties
        if difficulty_factor > 0.6 and random.random() < difficulty_factor * 0.3:
            # Extra large obstacle
            size_boost = int(BASE_OBSTACLE_SIZE * difficulty_factor)
            obstacle_width += size_boost
            obstacle_height += size_boost
        
        if random.random() < 0.5 and platforms:
            p = platforms[-1]
            # Place obstacle on the platform but ensure it's off-screen
            # Check if the platform is wide enough for the obstacle
            if p.width > obstacle_width:
                new_obstacle = Obstacle(
                    max(obstacle_x, p.x + random.randint(0, p.width - obstacle_width)), 
                    p.y - obstacle_height,
                    obstacle_width,
                    obstacle_height
                )
                obstacles.append(new_obstacle)
                generated_obstacles.append(new_obstacle)
            else:
                # If platform is too narrow, place obstacle at the start of platform
                new_obstacle = Obstacle(
                    max(obstacle_x, p.x),
                    p.y - obstacle_height,
                    obstacle_width,
                    obstacle_height
                )
                obstacles.append(new_obstacle)
                generated_obstacles.append(new_obstacle)
        else:
            # Place obstacle on the floor but ensure it's off-screen
            new_obstacle = Obstacle(
                obstacle_x, 
                PLAY_AREA_HEIGHT - 20 - obstacle_height,
                obstacle_width,
                obstacle_height
            )
            obstacles.append(new_obstacle)
            generated_obstacles.append(new_obstacle)
            
        # At higher difficulties, add a chance for a second obstacle
        if difficulty_factor > 0.3 and random.random() < difficulty_factor * 0.5:
            second_obstacle_x = obstacle_x + random.randint(100, 200)
            
            # Apply the same size logic to the second obstacle
            if random.random() < difficulty_factor:
                # Big obstacle - biased towards maximum size at higher difficulties
                min_size = max(BASE_OBSTACLE_SIZE, int(BASE_OBSTACLE_SIZE + 20 * difficulty_factor))
                second_obstacle_width = random.randint(min_size, base_width)
                second_obstacle_height = random.randint(min_size, base_width)
            else:
                # Regular obstacle - standard size range
                second_obstacle_width = random.randint(BASE_OBSTACLE_SIZE, max(BASE_OBSTACLE_SIZE + 30, int(base_width * 0.7)))
                second_obstacle_height = random.randint(BASE_OBSTACLE_SIZE, max(BASE_OBSTACLE_SIZE + 30, int(base_width * 0.7)))
            
            # Add a chance for extra large obstacles at high difficulties
            if difficulty_factor > 0.6 and random.random() < difficulty_factor * 0.3:
                # Extra large obstacle
                size_boost = int(BASE_OBSTACLE_SIZE * difficulty_factor)
                second_obstacle_width += size_boost
                second_obstacle_height += size_boost
            
            new_obstacle = Obstacle(
                second_obstacle_x, 
                PLAY_AREA_HEIGHT - 20 - second_obstacle_height,
                second_obstacle_width,
                second_obstacle_height
            )
            obstacles.append(new_obstacle)
            generated_obstacles.append(new_obstacle)

    # Function to check if a position would overlap with any obstacle
    def would_overlap_with_obstacle(x, y, width, height):
        test_rect = pygame.Rect(x, y, width, height)
        for obs in generated_obstacles:
            obs_rect = pygame.Rect(obs.x, obs.y, obs.width, obs.height)
            # Add a small buffer around obstacles (10 pixels)
            buffer = 10
            expanded_obs_rect = pygame.Rect(
                obs.x - buffer, 
                obs.y - buffer, 
                obs.width + 2*buffer, 
                obs.height + 2*buffer
            )
            if test_rect.colliderect(expanded_obs_rect):
                return True
        return False

    # Coin
    if random.random() < 0.4:
        # Try up to 5 times to place a coin that doesn't overlap with obstacles
        for _ in range(5):
            coin_x = new_x + random.randint(0, new_width - 20)
            coin_y = PLAY_AREA_HEIGHT - 70
            
            if not would_overlap_with_obstacle(coin_x, coin_y, 20, 20):  # Assuming coin size is 20x20
                coins.append(Coin(coin_x, coin_y))
                break

    # Power-up
    if random.random() < 0.1:
        # Try up to 5 times to place a power-up that doesn't overlap with obstacles
        for _ in range(5):
            powerup_x = new_x + random.randint(0, new_width - 20)
            powerup_y = PLAY_AREA_HEIGHT - 70
            
            if not would_overlap_with_obstacle(powerup_x, powerup_y, 20, 20):  # Assuming power-up size is 20x20
                power_ups.append(PowerUp(
                    powerup_x,
                    powerup_y,
                    random.choice(['speed', 'flying', 'invincibility'])
                ))
                break

# Remove old objects
def remove_old_objects():
    global floors, platforms, obstacles, coins, power_ups, player
    # Calculate dynamic left boundary based on furthest right position
    dynamic_left_boundary = max(0, player.furthest_right_position - MAX_BACKTRACK_DISTANCE - 100)
    
    # Keep objects that are within the potential view range (from dynamic left boundary to current view)
    floors = [f for f in floors if f.x + f.width > dynamic_left_boundary]
    platforms = [p for p in platforms if p.x + p.width > dynamic_left_boundary]
    obstacles = [o for o in obstacles if o.x + o.width > dynamic_left_boundary]
    coins = [c for c in coins if c.x + c.width > dynamic_left_boundary]
    power_ups = [p for p in power_ups if p.x + p.width > dynamic_left_boundary]

# Add a function to draw a gradient background
def draw_gradient_background():
    # Create a gradient from light blue at the top to a slightly darker blue at the bottom
    top_color = LIGHT_BLUE
    bottom_color = (135, 206, 235)  # Sky blue
    
    for y in range(PLAY_AREA_HEIGHT):
        # Calculate the color for this line by interpolating between top and bottom colors
        ratio = y / PLAY_AREA_HEIGHT
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        color = (r, g, b)
        
        # Draw a horizontal line with this color
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))

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
player_has_moved = False  # Track if the player has moved
player.start_invincibility(from_damage=False)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        # Game logic
        handle_input(player)
        
        # Check if player has moved
        if not player_has_moved and (player.vx != 0 or player.vy != 0):
            player_has_moved = True
            
        player.update(floors, platforms, obstacles, coins, power_ups)
        update_scroll(player)
        if camera_x + WIDTH > rightmost_floor_end - 300:
            generate_new_segment()
        remove_old_objects()

        # Draw background
        draw_gradient_background()
        for floor in floors:
            floor.draw(camera_x)
        for platform in platforms:
            platform.draw(camera_x)
        for obstacle in obstacles:
            obstacle.draw(camera_x)
        for coin in coins:
            coin.draw(camera_x)
        for power_up in power_ups:
            power_up.draw(camera_x)
        player.draw(camera_x)
        draw_status_bar(player)
        
        # Draw debug info if enabled
        if show_debug:
            draw_debug_info(player)
            
        # Draw welcome text if player hasn't moved yet
        if not player_has_moved:
            font = pygame.font.Font(None, 72)
            text = font.render("Welcome to Dasher", True, (30, 144, 255))  # Using BLUE color
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            screen.blit(text, text_rect)
            
            # Add a smaller instruction text
            font_small = pygame.font.Font(None, 36)
            instruction = font_small.render("Press arrow keys to move", True, BLACK)
            instruction_rect = instruction.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
            screen.blit(instruction, instruction_rect)

    if game_over:
        font = pygame.font.Font(None, 72)
        text = font.render("Game Over", True, RED)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.wait(2000)
        running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()