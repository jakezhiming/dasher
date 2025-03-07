import random
import pygame
from constants import (
    PLAY_AREA_HEIGHT, DIFFICULTY_START_DISTANCE, DIFFICULTY_MAX_DISTANCE,
    BASE_OBSTACLE_SIZE, MAX_OBSTACLE_CHANCE, MAX_PIT_CHANCE,
    MIN_PIT_WIDTH, MAX_PIT_WIDTH, MIN_PLATFORM_CHANCE
)
from game_objects import Floor, Platform, Obstacle, Coin, PowerUp

def generate_new_segment(player, floors, platforms, obstacles, coins, power_ups, rightmost_floor_end, camera_x, width):
    """Generate a new segment of the level with floors, platforms, obstacles, and collectibles."""
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
        visible_right_edge = camera_x + width
        
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
                    random.choice(['speed', 'flying', 'invincibility', 'life'])
                ))
                break
    
    return rightmost_floor_end

def remove_old_objects(player, floors, platforms, obstacles, coins, power_ups):
    """Remove objects that are far behind the player."""
    from constants import MAX_BACKTRACK_DISTANCE
    
    # Calculate dynamic left boundary based on furthest right position
    dynamic_left_boundary = max(0, player.furthest_right_position - MAX_BACKTRACK_DISTANCE - 100)
    
    # Keep objects that are within the potential view range (from dynamic left boundary to current view)
    floors = [f for f in floors if f.x + f.width > dynamic_left_boundary]
    platforms = [p for p in platforms if p.x + p.width > dynamic_left_boundary]
    obstacles = [o for o in obstacles if o.x + o.width > dynamic_left_boundary]
    coins = [c for c in coins if c.x + c.width > dynamic_left_boundary]
    power_ups = [p for p in power_ups if p.x + p.width > dynamic_left_boundary]
    
    return floors, platforms, obstacles, coins, power_ups 