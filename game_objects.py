import pygame
from constants import (
    BROWN, GREEN, YELLOW, BLUE, CYAN, MAGENTA, RED,
    PLAY_AREA_HEIGHT, WIDTH, FLOOR_HEIGHT, COIN_SIZE,
    POWERUP_SIZE, DEFAULT_OBSTACLE_SIZE
)
import math
import random

# Global texture variables
ground_texture = None
platform_texture = None
coin_sprite = None
powerup_sprites = {}
obstacle_sprites = []  # List to store different obstacle sprite variations

def load_textures():
    """Load textures for game objects."""
    global ground_texture, platform_texture, coin_sprite, powerup_sprites, obstacle_sprites
    
    try:
        # Load ground texture
        ground_path = "assets/images/textures/ground_texture.png"
        ground_texture = pygame.image.load(ground_path).convert()
        
        # Load platform texture
        platform_path = "assets/images/textures/platform_texture.png"
        platform_texture = pygame.image.load(platform_path).convert()
        
        # Load coin sprite
        try:
            coin_path = "assets/images/powerups/coin.png"
            coin_sprite = pygame.image.load(coin_path).convert_alpha()
            # Resize to match the game's dimensions if needed
            if coin_sprite.get_width() != COIN_SIZE or coin_sprite.get_height() != COIN_SIZE:
                coin_sprite = pygame.transform.scale(coin_sprite, (COIN_SIZE, COIN_SIZE))
            print("Successfully loaded coin sprite")
        except Exception as e:
            print(f"Error loading coin sprite: {e}")
            coin_sprite = None
            
        # Load power-up sprites
        try:
            powerup_types = ['speed', 'flying', 'invincibility', 'life']
            for p_type in powerup_types:
                path = f"assets/images/powerups/powerup_{p_type}.png"
                powerup_sprites[p_type] = pygame.image.load(path).convert_alpha()
                # Resize to match the game's dimensions if needed
                if powerup_sprites[p_type].get_width() != POWERUP_SIZE or powerup_sprites[p_type].get_height() != POWERUP_SIZE:
                    powerup_sprites[p_type] = pygame.transform.scale(powerup_sprites[p_type], (POWERUP_SIZE, POWERUP_SIZE))
            print("Successfully loaded power-up sprites")
        except Exception as e:
            print(f"Error loading power-up sprites: {e}")
            exit()
            
        # Load obstacle sprites
        try:
            # Load multiple obstacle variations
            obstacle_types = ['rock', 'crate', 'spikes', 'lava', 'saw']
            for o_type in obstacle_types:
                path = f"assets/images/obstacles/obstacle_{o_type}.png"
                try:
                    sprite = pygame.image.load(path).convert_alpha()
                    obstacle_sprites.append(sprite)
                except Exception as e:
                    print(f"Error loading obstacle sprite {o_type}: {e}")
                    # Create a fallback colored square if sprite loading fails
                    fallback = pygame.Surface((DEFAULT_OBSTACLE_SIZE, DEFAULT_OBSTACLE_SIZE))
                    fallback.fill(GREEN)
                    obstacle_sprites.append(fallback)
            
            # If no obstacle sprites were loaded successfully, create a default one
            if not obstacle_sprites:
                default = pygame.Surface((DEFAULT_OBSTACLE_SIZE, DEFAULT_OBSTACLE_SIZE))
                default.fill(GREEN)
                obstacle_sprites.append(default)
                
            print("Successfully loaded obstacle sprites")
        except Exception as e:
            print(f"Error loading obstacle sprites: {e}")
            exit()
        
        print("Successfully loaded all textures and sprites")
    except Exception as e:
        print(f"Error loading textures: {e}")
        exit()

class Floor:
    def __init__(self, x, width):
        self.x = x
        self.width = width
        self.height = FLOOR_HEIGHT
        self.y = PLAY_AREA_HEIGHT - self.height

    def draw(self, screen, camera_x):
        global ground_texture
        
        # Load textures if not loaded yet
        if ground_texture is None:
            load_textures()
            
        # Draw textured floor by tiling the texture
        rect = pygame.Rect(self.x - camera_x, self.y, self.width, self.height)
        
        # Calculate how many complete tiles we need
        texture_width = ground_texture.get_width()
        num_complete_tiles = self.width // texture_width
        remaining_width = self.width % texture_width
        
        # Draw complete tiles
        for i in range(num_complete_tiles):
            tile_x = self.x - camera_x + (i * texture_width)
            # Only draw tiles that are visible on screen
            if -texture_width < tile_x < WIDTH:
                screen.blit(ground_texture, (tile_x, self.y))
        
        # Draw the partial tile at the end if needed
        if remaining_width > 0:
            tile_x = self.x - camera_x + (num_complete_tiles * texture_width)
            if -texture_width < tile_x < WIDTH:
                # Create a subsurface of the texture for the partial tile
                partial_texture = ground_texture.subsurface((0, 0, remaining_width, ground_texture.get_height()))
                screen.blit(partial_texture, (tile_x, self.y))

class Platform:
    def __init__(self, x, y, width):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20

    def draw(self, screen, camera_x):
        global platform_texture
        
        # Load textures if not loaded yet
        if platform_texture is None:
            load_textures()

        # Calculate how many complete tiles we need
        texture_width = platform_texture.get_width()
        num_complete_tiles = self.width // texture_width
        remaining_width = self.width % texture_width
        
        # Draw complete tiles
        for i in range(num_complete_tiles):
            tile_x = self.x - camera_x + (i * texture_width)
            # Only draw tiles that are visible on screen
            if -texture_width < tile_x < WIDTH:
                screen.blit(platform_texture, (tile_x, self.y))
        
        # Draw the partial tile at the end if needed
        if remaining_width > 0:
            tile_x = self.x - camera_x + (num_complete_tiles * texture_width)
            if -texture_width < tile_x < WIDTH:
                # Create a subsurface of the texture for the partial tile
                partial_texture = platform_texture.subsurface((0, 0, remaining_width, platform_texture.get_height()))
                screen.blit(partial_texture, (tile_x, self.y))

class Obstacle:
    def __init__(self, x, y, width=DEFAULT_OBSTACLE_SIZE, height=DEFAULT_OBSTACLE_SIZE):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # Define obstacle types
        self.obstacle_types = ['rock', 'crate', 'spikes', 'lava', 'saw']
        
        # Choose sprite type based on size and characteristics
        if obstacle_sprites:
            # Use a weighted random approach to ensure all types appear
            # with some size-based preferences
            
            # Calculate weights based on dimensions
            weights = [1, 1, 1, 1, 1]  # Start with equal weights
            
            # Adjust weights based on dimensions
            if height > width * 1.2:  # Taller obstacles
                weights[self.obstacle_types.index('spikes')] += 3
            if width > height * 1.2:  # Wider obstacles
                weights[self.obstacle_types.index('lava')] += 3
            if abs(width - height) < 10:  # Square-ish obstacles
                weights[self.obstacle_types.index('crate')] += 2
                weights[self.obstacle_types.index('saw')] += 2
            if width < 40 or height < 40:  # Smaller obstacles
                weights[self.obstacle_types.index('rock')] += 2
            
            # Choose sprite type based on weights
            total_weight = sum(weights)
            r = random.uniform(0, total_weight)
            cumulative_weight = 0
            
            for i, weight in enumerate(weights):
                cumulative_weight += weight
                if r <= cumulative_weight:
                    self.sprite_index = i
                    break
            else:
                # Fallback if something goes wrong
                self.sprite_index = random.randint(0, len(obstacle_sprites) - 1)
        else:
            self.sprite_index = 0
            
        # Ensure sprite_index is within bounds
        if obstacle_sprites and self.sprite_index >= len(obstacle_sprites):
            self.sprite_index = 0
            
        # Animation properties
        self.animation_time = 0
        self.rotation_angle = 0
        self.animation_speed = random.uniform(0.5, 1.5)  # Random speed for variety
        
        # Get the obstacle type based on sprite index
        if self.sprite_index < len(self.obstacle_types):
            self.type = self.obstacle_types[self.sprite_index]
        else:
            self.type = "unknown"

    def update(self, dt):
        # Update animation based on obstacle type
        self.animation_time += dt
        
        if self.type == "saw":
            # Rotate the saw blade
            self.rotation_angle = (self.rotation_angle + 360 * dt * self.animation_speed) % 360
        
        # Other animation updates can be added here for different obstacle types

    def draw(self, screen, camera_x):
        # If we have sprites loaded, use them
        if obstacle_sprites:
            # Get the original sprite
            sprite = obstacle_sprites[self.sprite_index]
            
            # Scale the sprite to match the obstacle's dimensions
            scaled_sprite = pygame.transform.scale(sprite, (self.width, self.height))
            
            # Apply animations based on obstacle type
            if self.type == "saw":
                # Rotate the saw blade
                # For saw blades, ensure they're square for better rotation
                square_size = max(self.width, self.height)
                square_sprite = pygame.transform.scale(sprite, (square_size, square_size))
                
                rotated_sprite = pygame.transform.rotate(square_sprite, self.rotation_angle)
                # Get the rect for the rotated sprite to center it properly
                rotated_rect = rotated_sprite.get_rect(center=(self.x - camera_x + self.width//2, self.y + self.height//2))
                # Draw the rotated sprite
                screen.blit(rotated_sprite, rotated_rect.topleft)
            elif self.type == "lava":
                # Add a pulsing effect for lava
                pulse = (math.sin(self.animation_time * 5) + 1) * 0.1 + 0.8  # Value between 0.8 and 1.0
                # Apply the pulse effect by scaling slightly
                pulse_width = int(self.width * pulse)
                pulse_height = int(self.height * pulse)
                pulse_x = self.x - camera_x + (self.width - pulse_width) // 2
                pulse_y = self.y + (self.height - pulse_height) // 2
                
                pulse_sprite = pygame.transform.scale(scaled_sprite, (pulse_width, pulse_height))
                screen.blit(pulse_sprite, (pulse_x, pulse_y))
            else:
                # Draw the scaled sprite normally for other obstacle types
                screen.blit(scaled_sprite, (self.x - camera_x, self.y))
        else:
            # Fallback to drawing a rectangle if no sprites are available
            pygame.draw.rect(screen, GREEN, (self.x - camera_x, self.y, self.width, self.height))

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = COIN_SIZE
        self.height = COIN_SIZE
        # Animation variables
        self.animation_frame = 0
        self.animation_speed = 0.05
        self.animation_time = 0
        self.rotation = 0
        self.rotation_speed = 5  # degrees per update

    def update(self, dt):
        # Update animation - rotate the coin
        self.animation_time += dt
        if self.animation_time >= self.animation_speed:
            self.rotation = (self.rotation + self.rotation_speed) % 360
            self.animation_time = 0

    def draw(self, screen, camera_x):
        global coin_sprite
        
        # Load textures if not loaded yet
        if coin_sprite is None:
            load_textures()
            
        # Create a rotated copy of the sprite for animation
        if self.rotation != 0:
            # Scale the sprite based on rotation to simulate 3D effect
            scale_factor = abs(0.7 + 0.3 * abs(math.cos(math.radians(self.rotation))))
            scaled_width = int(self.width * scale_factor)
            
            # Only scale if needed
            if scaled_width != self.width:
                scaled_sprite = pygame.transform.scale(coin_sprite, (scaled_width, self.height))
                # Calculate position adjustment for the scaling
                pos_adjust = (scaled_width - self.width) // 2
                screen.blit(scaled_sprite, (int(self.x - camera_x - pos_adjust), int(self.y)))
            else:
                screen.blit(coin_sprite, (int(self.x - camera_x), int(self.y)))
        else:
            # Draw the coin sprite without rotation
            screen.blit(coin_sprite, (int(self.x - camera_x), int(self.y)))

class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.width = POWERUP_SIZE
        self.height = POWERUP_SIZE
        self.radius = 10
        self.type = type
        # Keep width and height properties for existing collision detection
        self.update_center()
        # Animation variables
        self.animation_frame = 0
        self.animation_speed = 0.15
        self.animation_time = 0
        self.pulse_scale = 1.0
        self.pulse_direction = 0.05
        
    def update(self, dt):
        # Update animation - pulsing effect
        self.animation_time += dt
        if self.animation_time >= self.animation_speed:
            self.pulse_scale += self.pulse_direction
            if self.pulse_scale > 1.2:
                self.pulse_scale = 1.2
                self.pulse_direction = -0.05
            elif self.pulse_scale < 0.8:
                self.pulse_scale = 0.8
                self.pulse_direction = 0.05
            self.animation_time = 0
        
    def update_center(self):
        # Calculate center coordinates based on top-left position
        self.center_x = self.x + self.radius
        self.center_y = self.y + self.radius

    def draw(self, screen, camera_x):
        global powerup_sprites
        
        # Load textures if not loaded yet
        if not powerup_sprites:
            load_textures()
            
        # Get the sprite for this power-up type
        sprite = powerup_sprites[self.type]
        
        # Apply pulsing effect
        current_size = int(self.width * self.pulse_scale)
        if current_size != self.width:
            scaled_sprite = pygame.transform.scale(sprite, (current_size, current_size))
        else:
            scaled_sprite = sprite
            
        # Calculate position adjustments for the pulsing effect
        pos_adjust = (current_size - self.width) // 2
        
        # Draw the power-up sprite
        screen.blit(scaled_sprite, (int(self.x - camera_x - pos_adjust), int(self.y - pos_adjust)))