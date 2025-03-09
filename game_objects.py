import pygame
from constants import (
    BROWN, GREEN, YELLOW, BLUE, CYAN, MAGENTA, RED,
    PLAY_AREA_HEIGHT, WIDTH, FLOOR_HEIGHT, COIN_SIZE,
    POWERUP_SIZE, DEFAULT_OBSTACLE_SIZE
)
import math
import random
import os
import input_handler  # Import input_handler for debug toggle

# Global texture variables
ground_texture = None
platform_texture = None
coin_sprite = None
powerup_sprites = {}
obstacle_sprites = {}  # Dictionary to store different obstacle sprites
fire_animation_frames = []  # List to store fire animation frames
saw_animation_frames = []  # List to store saw animation frames
bomb_animation_frames = []  # List to store bomb animation frames
explosion_animation_frames = []  # List to store explosion animation frames

def load_textures():
    """Load textures for game objects."""
    global ground_texture, platform_texture, coin_sprite, powerup_sprites, obstacle_sprites
    global fire_animation_frames, saw_animation_frames, bomb_animation_frames, explosion_animation_frames
    
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
            # Load spikes
            try:
                spikes_path = "assets/images/obstacles/spikes.png"
                obstacle_sprites['spikes'] = pygame.image.load(spikes_path).convert_alpha()
                print("Successfully loaded spikes sprite")
            except Exception as e:
                print(f"Error loading spikes sprite: {e}")
                fallback = pygame.Surface((30, 20))
                fallback.fill(RED)
                obstacle_sprites['spikes'] = fallback
            
            # Load fire animation frames (sprite sheet with 3 frames)
            try:
                fire_path = "assets/images/obstacles/fire.png"
                fire_sprite_sheet = pygame.image.load(fire_path).convert_alpha()
                
                # Get the dimensions of the sprite sheet
                sheet_width = fire_sprite_sheet.get_width()
                sheet_height = fire_sprite_sheet.get_height()
                
                # Assuming the fire sprite sheet has 3 frames horizontally
                frame_width = sheet_width // 3
                
                # Extract each frame from the sprite sheet
                for i in range(3):
                    # Create a subsurface for each frame
                    frame_rect = pygame.Rect(i * frame_width, 0, frame_width, sheet_height)
                    frame = fire_sprite_sheet.subsurface(frame_rect)
                    fire_animation_frames.append(frame)
                
                # Store the first frame as the base sprite
                obstacle_sprites['fire'] = fire_animation_frames[0]
                print("Successfully loaded fire sprite sheet with 3 frames")
            except Exception as e:
                print(f"Error loading fire sprite: {e}")
                fallback = pygame.Surface((40, 30))
                fallback.fill((255, 100, 0))  # Orange for fire
                obstacle_sprites['fire'] = fallback
                fire_animation_frames = [fallback] * 3  # Create 3 identical frames as fallback
            
            # Load saw animation frames (sprite sheet with 8 frames)
            try:
                saw_path = "assets/images/obstacles/saw.png"
                saw_sprite_sheet = pygame.image.load(saw_path).convert_alpha()
                
                # Get the dimensions of the sprite sheet
                sheet_width = saw_sprite_sheet.get_width()
                sheet_height = saw_sprite_sheet.get_height()
                
                # Assuming the saw sprite sheet has 8 frames horizontally
                frame_width = sheet_width // 8
                
                # Extract each frame from the sprite sheet
                for i in range(8):
                    # Create a subsurface for each frame
                    frame_rect = pygame.Rect(i * frame_width, 0, frame_width, sheet_height)
                    frame = saw_sprite_sheet.subsurface(frame_rect)
                    saw_animation_frames.append(frame)
                
                # Store the first frame as the base sprite
                obstacle_sprites['saw'] = saw_animation_frames[0]
                print("Successfully loaded saw sprite sheet with 8 frames")
            except Exception as e:
                print(f"Error loading saw sprite: {e}")
                fallback = pygame.Surface((30, 30))
                fallback.fill((200, 200, 200))  # Gray for saw
                obstacle_sprites['saw'] = fallback
                saw_animation_frames = [fallback] * 8  # Create 8 identical frames as fallback
            
            # Load bomb animation frames
            bomb_dir = "assets/images/obstacles/bomb"
            for i in range(1, 11):  # 10 frames
                path = f"{bomb_dir}/{i}.png"
                try:
                    frame = pygame.image.load(path).convert_alpha()
                    bomb_animation_frames.append(frame)
                except Exception as e:
                    print(f"Error loading bomb frame {i}: {e}")
            
            # Load explosion animation frames
            explosion_dir = "assets/images/obstacles/bomb_explosion"
            for i in range(1, 10):  # 9 frames
                path = f"{explosion_dir}/{i}.png"
                try:
                    frame = pygame.image.load(path).convert_alpha()
                    explosion_animation_frames.append(frame)
                except Exception as e:
                    print(f"Error loading explosion frame {i}: {e}")
                
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
    def __init__(self, x, y, width=DEFAULT_OBSTACLE_SIZE, height=DEFAULT_OBSTACLE_SIZE, obstacle_type=None, difficulty_factor=0.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.difficulty_factor = difficulty_factor
        
        # Define available obstacle types
        self.available_types = ['spikes', 'fire', 'saw', 'bomb']
        
        # Choose obstacle type if not specified
        if obstacle_type is None:
            # Use weighted random selection based on dimensions and difficulty
            weights = [1, 1, 1, 1]  # Start with equal weights
            
            # Adjust weights based on dimensions and difficulty
            if height < width * 0.5:  # Very flat obstacles
                weights[self.available_types.index('spikes')] += 3
            if height < width and height > 0:  # Wider than tall
                weights[self.available_types.index('fire')] += 2
            if abs(width - height) < 10:  # Square-ish obstacles
                weights[self.available_types.index('saw')] += 2
            if difficulty_factor > 0.5:  # More bombs at higher difficulty
                weights[self.available_types.index('bomb')] += 2 * difficulty_factor
            
            # Choose type based on weights
            total_weight = sum(weights)
            r = random.uniform(0, total_weight)
            cumulative_weight = 0
            
            for i, weight in enumerate(weights):
                cumulative_weight += weight
                if r <= cumulative_weight:
                    self.type = self.available_types[i]
                    break
            else:
                # Fallback
                self.type = 'spikes'
        else:
            self.type = obstacle_type
            
        # Animation properties
        self.animation_time = 0
        self.animation_speed = random.uniform(0.5, 1.5)  # Random speed for variety
        self.frame_index = 0
        self.exploded = False
        self.explosion_time = 0
        self.explosion_started = False
        self.explosion_frame_index = 0
        self.explosion_timer = 5.0  # 5 seconds until explosion
        self.timer_started = False  # Flag to track if the bomb timer has started
        self.active = True  # Whether the obstacle is active (not exploded)
        self.visible_once = False  # Flag to track if the bomb has been visible
        
        # Calculate the number of duplications needed for spikes and fire
        self.calculate_duplications()
        
        # Adjust collision box based on type
        self.adjust_collision_box()
        
    def calculate_duplications(self):
        """Calculate how many times to duplicate the base sprite for width-based obstacles"""
        self.duplications = 1  # Default is 1 (no duplication)
        
        if self.type == 'spikes' and 'spikes' in obstacle_sprites:
            # Calculate how many spikes to place side by side
            spike_width = obstacle_sprites['spikes'].get_width()
            if spike_width > 0:
                self.duplications = max(1, int(self.width / spike_width))
                # Adjust width to match actual duplications
                self.width = spike_width * self.duplications
        
        elif self.type == 'fire' and len(fire_animation_frames) > 0:
            # Calculate how many fire sprites to place side by side
            fire_width = fire_animation_frames[0].get_width()
            if fire_width > 0:
                self.duplications = max(1, int(self.width / fire_width))
                # Adjust width to match actual duplications
                self.width = fire_width * self.duplications
        
    def adjust_collision_box(self):
        """Adjust the collision box based on obstacle type"""
        self.collision_x = self.x
        self.collision_y = self.y
        self.collision_width = self.width
        self.collision_height = self.height
        
        if self.type == 'spikes':
            # Spikes have no height for collision (only the base)
            self.collision_height = 5
            self.collision_y = self.y + self.height - 5
        elif self.type == 'fire':
            # Fire collision box is half the height of the fire image
            self.collision_height = self.height / 2
            self.collision_y = self.y + self.height - self.collision_height
        elif self.type == 'bomb':
            if self.exploded:
                # When exploded, remove the collision box
                self.collision_width = 0
                self.collision_height = 0
            else:
                self.collision_width = self.width / 2
                self.collision_height = self.height / 2
                self.collision_x = self.x + self.width / 4
                self.collision_y = self.y + self.height / 2 + 2 # Position collision box lower to the ground
            
    def get_collision_rect(self):
        """Return the collision rectangle for this obstacle"""
        # If the obstacle is not active, return an empty rectangle
        if not self.active:
            return pygame.Rect(0, 0, 0, 0)
            
        if self.type == 'bomb' and self.exploded:
            # Only return explosion collision during the active explosion frames
            # Once the explosion is complete, return an empty rectangle
            if self.explosion_frame_index < len(explosion_animation_frames):
                # Explosion has a blast radius of 3x the bomb size
                blast_radius = self.width * 3
                return pygame.Rect(
                    self.x - blast_radius/2 + self.width/2,
                    self.y - blast_radius/2 + self.height/2,
                    blast_radius,
                    blast_radius
                )
            else:
                # Explosion animation is complete, no collision
                return pygame.Rect(0, 0, 0, 0)
        else:
            return pygame.Rect(
                self.collision_x,
                self.collision_y,
                self.collision_width,
                self.collision_height
            )

    def update(self, dt):
        # Update animation based on obstacle type
        self.animation_time += dt
        
        if self.type == 'saw':
            # Update saw animation frame
            if self.animation_time >= 0.1:
                self.animation_time = 0
                self.frame_index = (self.frame_index + 1) % len(saw_animation_frames)
        
        elif self.type == 'fire':
            # Update fire animation frame
            if self.animation_time >= 0.15:
                self.animation_time = 0
                self.frame_index = (self.frame_index + 1) % len(fire_animation_frames)
        
        elif self.type == 'bomb':
            if not self.exploded:
                # Update bomb animation
                if self.animation_time >= 0.1:
                    self.animation_time = 0
                    self.frame_index = (self.frame_index + 1) % len(bomb_animation_frames)
                
                # Update explosion timer only if it has started
                if self.timer_started:
                    self.explosion_timer -= dt
                    if self.explosion_timer <= 0 and not self.explosion_started:
                        self.start_explosion()
            else:
                # Update explosion animation
                self.explosion_time += dt
                if self.explosion_time >= 0.1:
                    self.explosion_time = 0
                    self.explosion_frame_index += 1
                    if self.explosion_frame_index >= len(explosion_animation_frames):
                        self.active = False  # Explosion finished
                        # Ensure collision box is completely removed
                        self.collision_width = 0
                        self.collision_height = 0
    
    def check_visibility(self, camera_x):
        """Check if the obstacle is visible on screen and start bomb timer if needed"""
        if self.type == 'bomb' and not self.timer_started:
            # Calculate if the bomb is visible on screen
            screen_x = self.x - camera_x
            if 0 <= screen_x <= WIDTH:
                self.timer_started = True
                self.visible_once = True
    
    def start_explosion(self):
        """Start the explosion animation for a bomb"""
        self.exploded = True
        self.explosion_started = True
        self.explosion_frame_index = 0
        self.explosion_time = 0
        
        # Immediately remove the collision box for the bomb itself
        if self.type == 'bomb':
            self.collision_width = 0
            self.collision_height = 0
        
        # Adjust collision box for explosion
        self.adjust_collision_box()
    
    def handle_collision(self):
        """Handle collision with player"""
        if self.type == 'bomb' and not self.exploded:
            self.start_explosion()
            # Immediately remove the collision box for the bomb itself
            self.collision_width = 0
            self.collision_height = 0
            return False  # Don't damage player on initial bomb contact
        return True  # Damage player for other obstacle types

    def draw(self, screen, camera_x):
        # Skip drawing if not active
        if not self.active:
            return
        
        # Check if bomb is visible and start timer if needed
        if self.type == 'bomb':
            self.check_visibility(camera_x)
            
        # Draw based on obstacle type
        if self.type == 'spikes':
            # Draw spikes by duplicating the sprite horizontally
            if 'spikes' in obstacle_sprites:
                spike_sprite = obstacle_sprites['spikes']
                spike_width = spike_sprite.get_width()
                
                # Draw each spike side by side
                for i in range(self.duplications):
                    x_pos = self.x - camera_x + (i * spike_width)
                    # Scale vertically if needed, but keep original width
                    if spike_sprite.get_height() != self.height:
                        scaled_sprite = pygame.transform.scale(
                            spike_sprite, 
                            (spike_width, self.height)
                        )
                        screen.blit(scaled_sprite, (x_pos, self.y))
                    else:
                        screen.blit(spike_sprite, (x_pos, self.y))
            else:
                # Fallback
                pygame.draw.rect(screen, RED, (self.x - camera_x, self.y, self.width, self.height))
                
        elif self.type == 'fire':
            # Draw fire by duplicating the current animation frame horizontally
            if fire_animation_frames and len(fire_animation_frames) > 0:
                # Get the current animation frame
                fire_frame = fire_animation_frames[self.frame_index]
                fire_width = fire_frame.get_width()
                
                # Draw each fire sprite side by side
                for i in range(self.duplications):
                    x_pos = self.x - camera_x + (i * fire_width)
                    # Scale vertically if needed, but keep original width
                    if fire_frame.get_height() != self.height:
                        scaled_frame = pygame.transform.scale(
                            fire_frame, 
                            (fire_width, self.height)
                        )
                        screen.blit(scaled_frame, (x_pos, self.y))
                    else:
                        screen.blit(fire_frame, (x_pos, self.y))
            else:
                # Fallback
                pygame.draw.rect(screen, (255, 100, 0), (self.x - camera_x, self.y, self.width, self.height))
                
        elif self.type == 'saw':
            # Draw animated saw - just one frame at a time
            if saw_animation_frames and len(saw_animation_frames) > 0:
                # Get the current animation frame
                saw_frame = saw_animation_frames[self.frame_index]
                
                # Scale the frame to match the obstacle's dimensions
                # For saw, we want to maintain aspect ratio
                original_size = saw_frame.get_width()  # Assuming it's square
                if original_size > 0:
                    scaled_frame = pygame.transform.scale(
                        saw_frame, 
                        (self.width, self.height)
                    )
                    
                    # Draw the saw at its position
                    screen.blit(scaled_frame, (self.x - camera_x, self.y))
                else:
                    # Fallback if frame has no size
                    pygame.draw.rect(screen, (200, 200, 200), (self.x - camera_x, self.y, self.width, self.height))
            else:
                # Fallback
                pygame.draw.rect(screen, (200, 200, 200), (self.x - camera_x, self.y, self.width, self.height))
                
        elif self.type == 'bomb':
            if not self.exploded:
                # Draw bomb
                if bomb_animation_frames and len(bomb_animation_frames) > 0:
                    frame = bomb_animation_frames[self.frame_index]
                    scaled_frame = pygame.transform.scale(frame, (self.width, self.height))
                    # Position the bomb closer to the ground by adding an offset to y
                    bomb_y_offset = self.height / 5  # Move down by 1/5 of its height (changed from 1/4)
                    screen.blit(scaled_frame, (self.x - camera_x, self.y + bomb_y_offset))
                else:
                    # Fallback
                    pygame.draw.rect(screen, (0, 0, 0), (self.x - camera_x, self.y + self.height / 5, self.width, self.height))
            else:
                # Draw explosion
                if explosion_animation_frames and len(explosion_animation_frames) > 0 and self.explosion_frame_index < len(explosion_animation_frames):
                    frame = explosion_animation_frames[self.explosion_frame_index]
                    # Explosion is 3x the size of the bomb
                    explosion_size = self.width * 3
                    scaled_frame = pygame.transform.scale(frame, (explosion_size, explosion_size))
                    # Center the explosion on the bomb, accounting for the bomb's offset
                    bomb_y_offset = self.height / 5  # Changed from 1/4 to 1/5
                    explosion_x = self.x - camera_x - (explosion_size - self.width) / 2
                    explosion_y = self.y + bomb_y_offset - (explosion_size - self.height) / 2
                    screen.blit(scaled_frame, (explosion_x, explosion_y))
                    
                    # Debug: Draw explosion blast radius collision box when debug mode is enabled
                    if input_handler.show_debug and self.explosion_frame_index < len(explosion_animation_frames):
                        # Use the same calculation as in get_collision_rect method
                        blast_radius = self.width * 3
                        explosion_rect = pygame.Rect(
                            self.x - blast_radius/2 + self.width/2 - camera_x,
                            self.y - blast_radius/2 + self.height/2,
                            blast_radius,
                            blast_radius
                        )
                        pygame.draw.rect(screen, (255, 0, 0), explosion_rect, 1)
                else:
                    # Fallback
                    pygame.draw.circle(screen, (255, 0, 0), (self.x - camera_x + self.width//2, self.y + self.height//2), self.width)
        else:
            # Fallback for unknown types
            pygame.draw.rect(screen, GREEN, (self.x - camera_x, self.y, self.width, self.height))
            
        # Debug: Draw collision box only when debug mode is enabled
        if input_handler.show_debug:
            pygame.draw.rect(screen, (255, 0, 0), (self.collision_x - camera_x, self.collision_y, self.collision_width, self.collision_height), 1)

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