from compat import pygame, random
from constants.screen import PLAY_AREA_HEIGHT
from constants.difficulty import (
    DIFFICULTY_START_DISTANCE, DIFFICULTY_MAX_DISTANCE,
    BASE_OBSTACLE_CHANCE, MAX_OBSTACLE_CHANCE, 
    BASE_PIT_CHANCE, MAX_PIT_CHANCE,
    MIN_PIT_WIDTH, MAX_PIT_WIDTH, BASE_POWERUP_CHANCE,
    MAX_SPIKES, MAX_FIRES, MAX_SAW_SIZE
)
from constants.level_generation import (
    SEGMENT_LENGTH_MULTIPLIER, GRID_CELL_SIZE, OBSTACLE_BUFFER,
    MIN_PLATFORM_WIDTH, MAX_PLATFORM_WIDTH, PLATFORM_EDGE_BUFFER,
    MIN_PLATFORM_HORIZONTAL_DISTANCE
)
from constants.game_objects import FLOOR_HEIGHT
from constants.player import MAX_BACKTRACK_DISTANCE
from game_objects import Floor, Platform, Obstacle, Coin, PowerUp
from logger import get_module_logger

logger = get_module_logger('level_generator')

def generate_new_segment(player, floors, platforms, obstacles, coins, power_ups, camera_x, width):
    """Generate a new segment of the level with floors, platforms, obstacles, and collectibles."""
    last_floor = floors[-1]
    new_x = last_floor.x + last_floor.width
    
    # Calculate difficulty factor (0.0 to 1.0) based on player's progress
    progress = max(0, player.furthest_right_position - DIFFICULTY_START_DISTANCE)
    difficulty_factor = min(1.0, progress / (DIFFICULTY_MAX_DISTANCE - DIFFICULTY_START_DISTANCE))
    
    # Generate a larger segment at once (3x the previous size)
    segment_length = width * SEGMENT_LENGTH_MULTIPLIER
    segment_end_x = new_x + segment_length
    
    # Pre-calculate the visible right edge
    visible_right_edge = camera_x + width
    
    # Track generated obstacles for collision detection
    generated_obstacles = []
    
    # Create a spatial grid for faster collision detection
    collision_grid = {}
    
    def add_to_collision_grid(obj, x, y, w, h):
        """Add an object to the collision grid for faster lookups"""
        # Calculate grid cells this object occupies
        start_cell_x = int(x // GRID_CELL_SIZE)
        end_cell_x = int((x + w) // GRID_CELL_SIZE)
        start_cell_y = int(y // GRID_CELL_SIZE)
        end_cell_y = int((y + h) // GRID_CELL_SIZE)
        
        # Add object to all cells it occupies
        for cell_x in range(start_cell_x, end_cell_x + 1):
            for cell_y in range(start_cell_y, end_cell_y + 1):
                cell_key = (cell_x, cell_y)
                if cell_key not in collision_grid:
                    collision_grid[cell_key] = []
                collision_grid[cell_key].append((obj, pygame.Rect(x, y, w, h)))
    
    def would_overlap_with_obstacle(x, y, width, height):
        """Check if a rectangle would overlap with any obstacle using the grid"""
        test_rect = pygame.Rect(x, y, width, height)
        
        # Calculate grid cells to check
        start_cell_x = int(x // GRID_CELL_SIZE)
        end_cell_x = int((x + width) // GRID_CELL_SIZE)
        start_cell_y = int(y // GRID_CELL_SIZE)
        end_cell_y = int((y + height) // GRID_CELL_SIZE)
        
        # Check for collisions in relevant grid cells only
        for cell_x in range(start_cell_x, end_cell_x + 1):
            for cell_y in range(start_cell_y, end_cell_y + 1):
                cell_key = (cell_x, cell_y)
                if cell_key in collision_grid:
                    for _, obs_rect in collision_grid[cell_key]:
                        # Add a small buffer around obstacles
                        buffer = OBSTACLE_BUFFER
                        expanded_obs_rect = pygame.Rect(
                            obs_rect.x - buffer, 
                            obs_rect.y - buffer, 
                            obs_rect.width + 2*buffer, 
                            obs_rect.height + 2*buffer
                        )
                        if test_rect.colliderect(expanded_obs_rect):
                            return True
        return False
    
    def is_too_close_to_existing_platforms(x, width):
        """Check if a new platform would be too close horizontally to existing platforms"""
        # Since new platforms are generated to the right, we primarily need to check
        # if the left edge of the new platform (x) is too close to the right edge
        # of any existing platform (platform.x + platform.width)
        
        # Calculate the right edge of the new platform
        right_edge = x + width
        
        # Check against all existing platforms
        for platform in platforms:
            # Check for overlapping platforms (where the new platform starts before an existing platform ends)
            if (x <= platform.x + platform.width and right_edge >= platform.x):
                return True
                
            # Calculate the distance from the right edge of an existing platform to the left edge of the new platform
            distance = x - (platform.x + platform.width)
            
            # If the distance is less than the minimum and positive (meaning the new platform is to the right),
            # the platforms are too close
            if 0 <= distance < MIN_PLATFORM_HORIZONTAL_DISTANCE:
                return True
                
        return False
    
    # Generate floor segments to fill the entire new segment
    current_x = new_x
    while current_x < segment_end_x:
        # Scale pit chance and width based on difficulty
        pit_chance = BASE_PIT_CHANCE + (MAX_PIT_CHANCE - BASE_PIT_CHANCE) * difficulty_factor
        
        # Determine if there will be a pit
        has_pit = random.random() < pit_chance
        if has_pit:
            # Scale pit width based on difficulty
            max_pit_width = 300 + int((MAX_PIT_WIDTH - 300) * difficulty_factor)
            pit_width = random.randint(MIN_PIT_WIDTH, max_pit_width)
            current_x += pit_width
            
            # Always add a platform above the pit for the player to use
            # Ensure the platform width is appropriate for the pit width
            max_platform_width = min(MAX_PLATFORM_WIDTH, pit_width - 2*PLATFORM_EDGE_BUFFER)  # Ensure there's at least buffer space on each side
            min_platform_width = min(MIN_PLATFORM_WIDTH, max_platform_width)  # Ensure min_platform_width is not greater than max_platform_width
            
            if max_platform_width >= min_platform_width:
                platform_width = random.randint(min_platform_width, max_platform_width)
                
                # Calculate valid range for platform placement
                min_x_position = current_x - pit_width + PLATFORM_EDGE_BUFFER  # Buffer from left edge of pit
                max_x_position = current_x - platform_width - PLATFORM_EDGE_BUFFER  # Buffer from right edge of pit
                
                # Ensure we have a valid range
                if max_x_position > min_x_position:
                    platform_x = random.randint(min_x_position, max_x_position)
                else:
                    # If no valid range, place platform in the middle of the pit
                    platform_x = current_x - pit_width/2 - platform_width/2
                    
                platform_y = random.randint(100, PLAY_AREA_HEIGHT - 150)
                new_platform = Platform(platform_x, platform_y, platform_width)
                
                # Only add the platform if it's not too close to existing platforms
                if not is_too_close_to_existing_platforms(platform_x, platform_width):
                    platforms.append(new_platform)
                    add_to_collision_grid(new_platform, platform_x, platform_y, platform_width, 20)  # Changed from 10 to 20 to match Platform.height
            else:
                # If pit is too narrow for a platform, place a wider platform that extends beyond the pit
                platform_width = 150
                platform_x = current_x - pit_width - PLATFORM_EDGE_BUFFER  # Place it starting before the pit
                platform_y = random.randint(100, PLAY_AREA_HEIGHT - 150)
                new_platform = Platform(platform_x, platform_y, platform_width + 100)
                
                # Only add the platform if it's not too close to existing platforms
                if not is_too_close_to_existing_platforms(platform_x, platform_width + 100):
                    platforms.append(new_platform)
                    add_to_collision_grid(new_platform, platform_x, platform_y, platform_width + 100, 20)  # Changed from 10 to 20
        
        # Add a floor segment
        floor_width = random.randint(100, 300)
        if current_x + floor_width > segment_end_x:
            floor_width = max(100, segment_end_x - current_x)  # Ensure minimum width of 100px
        
        new_floor = Floor(current_x, floor_width)
        floors.append(new_floor)
        current_x += floor_width
        
        # Platform (additional platforms besides the ones over pits)
        if random.random() < 0.5:
            # Ensure floor_width is large enough for a platform
            if floor_width >= 100:
                platform_x = current_x - floor_width + random.randint(0, floor_width - 100)
                platform_y = random.randint(100, PLAY_AREA_HEIGHT - 100)
                platform_width = random.randint(50, 150)
                new_platform = Platform(platform_x, platform_y, platform_width)
                
                # Only add the platform if it's not too close to existing platforms
                if not is_too_close_to_existing_platforms(platform_x, platform_width):
                    platforms.append(new_platform)
                    add_to_collision_grid(new_platform, platform_x, platform_y, platform_width, 20)  # Changed from 10 to 20
        
        # Only generate obstacles and collectibles if they'll be off-screen
        if current_x > visible_right_edge:
            # Obstacle (on floor or platform)
            obstacle_chance = BASE_OBSTACLE_CHANCE + (MAX_OBSTACLE_CHANCE - BASE_OBSTACLE_CHANCE) * difficulty_factor
            
            if random.random() < obstacle_chance and floor_width >= 100:
                # Determine obstacle type based on difficulty and randomness
                obstacle_types = ['spikes', 'fire', 'saw', 'bomb']
                
                # Adjust weights based on difficulty
                # As difficulty increases, more dangerous obstacles become more common
                if difficulty_factor < 0.3:
                    # Early game: more spikes, less of other types
                    weights = [0.7, 0.2, 0.1, 0.0]  # No bombs early on
                elif difficulty_factor < 0.6:
                    # Mid game: balanced distribution
                    weights = [0.4, 0.3, 0.2, 0.1]  # Introduce bombs
                else:
                    # Late game: more dangerous obstacles
                    weights = [0.25, 0.25, 0.25, 0.25]  # Equal distribution
                
                # Choose obstacle type based on weights
                obstacle_type = random.choices(obstacle_types, weights=weights)[0]
                
                # Determine obstacle size based on type and difficulty
                if obstacle_type == 'spikes':
                    # For spikes, we'll set the width based on the number of duplications we want
                    # The actual width will be adjusted in the Obstacle class based on the sprite width
                    num_spikes = 1 + int((MAX_SPIKES-1) * difficulty_factor)
                    obstacle_width = num_spikes * 40  # Use actual spike width (30px) instead of approximate
                    obstacle_height = 35  # Fixed height for spikes
                
                elif obstacle_type == 'fire':
                    # For fire, we'll set the width based on the number of duplications we want
                    # The actual width will be adjusted in the Obstacle class based on the sprite width
                    num_fires = 1 + int((MAX_FIRES-1) * difficulty_factor)
                    obstacle_width = num_fires * 30  # Use actual fire width (30px) instead of approximate
                    obstacle_height = 30  # Fixed height for fire
                
                elif obstacle_type == 'saw':
                    # Saw gets bigger with difficulty
                    min_size = 50 + int(20 * difficulty_factor)  # 50 to 70
                    max_size = 60 + int((MAX_SAW_SIZE-60) * difficulty_factor)  # 60 to 100
                    size = random.randint(min_size, max_size)
                    obstacle_width = size
                    obstacle_height = size  # Keep it square for better rotation
                
                elif obstacle_type == 'bomb':
                    # Bombs are consistent in size
                    obstacle_width = 75
                    obstacle_height = 75
                
                # Flag to track if we successfully created an obstacle
                obstacle_created = False
                
                # Place obstacle on floor or platform
                if random.random() < 0.25 and platforms:
                    # Find suitable platforms that are wide enough for the obstacle
                    suitable_platforms = [p for p in platforms if p.width >= obstacle_width + 20]  # Add 20px buffer
                    
                    if suitable_platforms:
                        # Choose the most recently added suitable platform
                        p = suitable_platforms[-1]
                        
                        # Ensure obstacle is fully on the platform by constraining its position
                        # Calculate valid range for obstacle placement
                        min_x = p.x + 10  # 10px buffer from left edge
                        max_x = p.x + p.width - obstacle_width - 10  # 10px buffer from right edge
                        
                        # If valid placement range exists
                        if min_x <= max_x:
                            # Set the obstacle y position
                            obstacle_y = p.y - obstacle_height
                            
                            # Try to find a non-overlapping position
                            max_attempts = 10  # Limit the number of attempts to avoid infinite loops
                            found_valid_position = False
                            
                            for _ in range(max_attempts):
                                obstacle_x = random.randint(int(min_x), int(max_x))
                                # Check if this position would overlap with any existing obstacle
                                if not would_overlap_with_obstacle(obstacle_x, obstacle_y, obstacle_width, obstacle_height):
                                    found_valid_position = True
                                    break
                            
                            # If we found a valid position, create the obstacle
                            if found_valid_position:
                                new_obstacle = Obstacle(
                                    obstacle_x,
                                    obstacle_y,
                                    obstacle_width,
                                    obstacle_height,
                                    obstacle_type,
                                    difficulty_factor
                                )
                                obstacle_created = True
                        else:
                            # Platform too small, but we can resize spikes and fire to fit
                            if obstacle_type in ['spikes', 'fire']:
                                # Calculate maximum possible width with buffers
                                max_possible_width = p.width - 20  # 10px buffer on each side
                                
                                if max_possible_width > 0:
                                    # Adjust number of duplications to fit the platform
                                    if obstacle_type == 'spikes':
                                        # Recalculate number of spikes to fit
                                        num_spikes = max(1, int(max_possible_width / 30))
                                        obstacle_width = num_spikes * 30
                                    else:  # fire
                                        # Recalculate number of fires to fit
                                        num_fires = max(1, int(max_possible_width / 30))
                                        obstacle_width = num_fires * 30
                                    
                                    # Place the resized obstacle
                                    obstacle_x = p.x + 10  # 10px from left edge
                                    obstacle_y = p.y - obstacle_height
                                    
                                    # Check if this position would overlap with any existing obstacle
                                    if not would_overlap_with_obstacle(obstacle_x, obstacle_y, obstacle_width, obstacle_height):
                                        new_obstacle = Obstacle(
                                            obstacle_x,
                                            obstacle_y,
                                            obstacle_width,
                                            obstacle_height,
                                            obstacle_type,
                                            difficulty_factor
                                        )
                                        obstacle_created = True
                                else:
                                    # Platform too small even for a single sprite, try placing on floor instead
                                    pass
                            else:
                                # For other obstacle types, try placing on floor instead
                                pass
                
                # If we haven't created an obstacle yet, try placing it on the floor
                if not obstacle_created:
                    # Place obstacle on the floor
                    obstacle_y = PLAY_AREA_HEIGHT - 20 - obstacle_height
                    
                    # Ensure obstacle is fully on the floor
                    min_x = current_x - floor_width + 10  # 10px buffer from left edge
                    max_x = current_x - obstacle_width - 10  # 10px buffer from right edge
                    
                    # Check if we have a valid range
                    if min_x <= max_x:
                        # Try to find a non-overlapping position
                        max_attempts = 10  # Limit the number of attempts to avoid infinite loops
                        found_valid_position = False
                        
                        for _ in range(max_attempts):
                            obstacle_x = random.randint(int(min_x), int(max_x))
                            # Check if this position would overlap with any existing obstacle
                            if not would_overlap_with_obstacle(obstacle_x, obstacle_y, obstacle_width, obstacle_height):
                                found_valid_position = True
                                break
                        
                        # If we found a valid position, create the obstacle
                        if found_valid_position:
                            new_obstacle = Obstacle(
                                obstacle_x, 
                                obstacle_y,
                                obstacle_width,
                                obstacle_height,
                                obstacle_type,
                                difficulty_factor
                            )
                            obstacle_created = True
                
                # If we successfully created an obstacle, add it to the lists and collision grid
                if obstacle_created:
                    # Additional check to ensure obstacle is off-screen
                    if new_obstacle.x > visible_right_edge:
                        obstacles.append(new_obstacle)
                        generated_obstacles.append(new_obstacle)
                        
                        # Use the collision box for grid collision detection
                        collision_rect = new_obstacle.get_collision_rect()
                        add_to_collision_grid(
                            new_obstacle, 
                            collision_rect.x, 
                            collision_rect.y, 
                            collision_rect.width, 
                            collision_rect.height
                        )
            
            # Coin generation - with platform placement similar to power-ups
            coin_chance = 0.4  # Higher chance than power-ups
            
            if random.random() < coin_chance and floor_width >= 30:
                # Similar to power-ups, increase chance of placing on platform vs floor as difficulty increases
                coin_platform_placement_chance = 0.3 + (0.5 * difficulty_factor)  # Scales from 0.3 to 0.8
                
                # Decide whether to place on platform or floor
                if platforms and random.random() < coin_platform_placement_chance:
                    # Place on a platform
                    # Only consider platforms that are off-screen
                    off_screen_platforms = [p for p in platforms if p.x > visible_right_edge]
                    
                    if off_screen_platforms:
                        # Choose from recent off-screen platforms
                        p = random.choice(off_screen_platforms[-3:] if len(off_screen_platforms) > 3 else off_screen_platforms)
                        
                        # Ensure platform is wide enough
                        if p.width >= 30:
                            coin_x = p.x + random.randint(10, p.width - 20)
                            coin_y = p.y - 30  # Place above the platform
                            
                            if not would_overlap_with_obstacle(coin_x, coin_y, 20, 20):
                                new_coin = Coin(coin_x, coin_y)
                                coins.append(new_coin)
                                add_to_collision_grid(new_coin, coin_x, coin_y, 20, 20)
                else:
                    # Place on the floor (original behavior)
                    coin_x = current_x - floor_width + random.randint(0, floor_width - 20)
                    coin_y = PLAY_AREA_HEIGHT - FLOOR_HEIGHT - 30  # 30px above the floor, matching platform placement
                    
                    if not would_overlap_with_obstacle(coin_x, coin_y, 20, 20) and coin_x > visible_right_edge:
                        new_coin = Coin(coin_x, coin_y)
                        coins.append(new_coin)
                        add_to_collision_grid(new_coin, coin_x, coin_y, 20, 20)
            
            # Power-up generation - with increased platform placement as difficulty increases
            powerup_chance = BASE_POWERUP_CHANCE + (0.2 * difficulty_factor)  # Scales from 0.1 to 0.3
            
            if random.random() < powerup_chance and floor_width >= 30:
                # As difficulty increases, increase chance of placing on platform vs floor
                platform_placement_chance = 0.3 + (0.5 * difficulty_factor)  # Scales from 0.3 to 0.8
                
                # Decide whether to place on platform or floor
                if platforms and random.random() < platform_placement_chance:
                    # Place on a platform
                    # Only consider platforms that are off-screen
                    off_screen_platforms = [p for p in platforms if p.x > visible_right_edge]
                    
                    if off_screen_platforms:
                        # Choose from recent off-screen platforms
                        p = random.choice(off_screen_platforms[-3:] if len(off_screen_platforms) > 3 else off_screen_platforms)
                        
                        # Ensure platform is wide enough
                        if p.width >= 30:
                            powerup_x = p.x + random.randint(10, p.width - 20)
                            powerup_y = p.y - 30  # Place above the platform
                            
                            if not would_overlap_with_obstacle(powerup_x, powerup_y, 20, 20):
                                new_powerup = PowerUp(
                                    powerup_x,
                                    powerup_y,
                                    random.choice(['speed', 'flying', 'invincibility', 'life'])
                                )
                                power_ups.append(new_powerup)
                                add_to_collision_grid(new_powerup, powerup_x, powerup_y, 20, 20)
                else:
                    # Place on the floor (original behavior)
                    powerup_x = current_x - floor_width + random.randint(0, floor_width - 20)
                    powerup_y = PLAY_AREA_HEIGHT - FLOOR_HEIGHT - 30  # 30px above the floor, matching platform placement
                    
                    if not would_overlap_with_obstacle(powerup_x, powerup_y, 20, 20) and powerup_x > visible_right_edge:
                        new_powerup = PowerUp(
                            powerup_x,
                            powerup_y,
                            random.choice(['speed', 'flying', 'invincibility', 'life'])
                        )
                        power_ups.append(new_powerup)
                        add_to_collision_grid(new_powerup, powerup_x, powerup_y, 20, 20)
    
    return segment_end_x

def remove_old_objects(player, floors, platforms, obstacles, coins, power_ups):
    """Remove objects that are far behind the player."""
    # Calculate dynamic left boundary based on furthest right position
    dynamic_left_boundary = max(0, player.furthest_right_position - MAX_BACKTRACK_DISTANCE - 100)
    
    # Keep objects that are within the potential view range (from dynamic left boundary to current view)
    floors = [f for f in floors if f.x + f.width > dynamic_left_boundary]
    platforms = [p for p in platforms if p.x + p.width > dynamic_left_boundary]
    obstacles = [o for o in obstacles if o.x + o.width > dynamic_left_boundary]
    coins = [c for c in coins if c.x + c.width > dynamic_left_boundary]
    power_ups = [p for p in power_ups if p.x + p.width > dynamic_left_boundary]
    
    return floors, platforms, obstacles, coins, power_ups 