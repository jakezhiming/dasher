from pygame_compat import pygame, is_web_environment
from constants.player import PLAYER_WIDTH, PLAYER_HEIGHT
from constants.paths import (
    FONT_PATH, HEART_SPRITE_PATH, 
    SKY_PATH, CLOUDS_BG_PATH, MOUNTAINS_PATH, CLOUDS_MG_3_PATH, 
    CLOUDS_MG_2_PATH, CLOUD_LONELY_PATH, CLOUDS_MG_1_PATH,
    PLAYER_IDLE_PATH, PLAYER_RUN_PATH, PLAYER_JUMP_PATH, PLAYER_HURT_PATH,
    PLAYER_DEATH_PATH, PLAYER_WALK_PATH, PLAYER_CLIMB_PATH, PLAYER_ATTACK1_PATH,
    PLAYER_ATTACK2_PATH, PLAYER_THROW_PATH, PLAYER_PUSH_PATH, PLAYER_WALK_ATTACK_PATH,
    PLAYER_DUST_WALK_PATH, PLAYER_DUST_DOUBLE_JUMP_PATH,
    GROUND_TEXTURE_PATH, PLATFORM_TEXTURE_PATH, COIN_PATH,
    POWERUP_SPEED_PATH, POWERUP_FLYING_PATH, POWERUP_INVINCIBILITY_PATH, POWERUP_LIFE_PATH,
    SPIKES_PATH, FIRE_PATH, SAW_PATH, BOMB_DIR_PATH, EXPLOSION_DIR_PATH
)
from constants.game_objects import COIN_SIZE, POWERUP_SIZE
from constants.screen import PLAY_AREA_HEIGHT
from logger import get_module_logger

logger = get_module_logger('assets_loader')

# Check if we're in web environment for optimizations
IS_WEB = is_web_environment()

# ===== FONT CACHE =====
font_cache = {}

# ===== PLAYER SPRITES =====
player_sprites = {
    'idle': None,
    'run': None,
    'jump': None,
    'hurt': None,
    'death': None,
    'walk': None,
    'climb': None,
    'attack1': None,
    'attack2': None,
    'throw': None,
    'push': None,
    'walk_attack': None,
    'dust_walk': None,
    'dust_double_jump': None
}

# Dictionary to store animation frames for each action
player_frames = {
    'idle_right': [],
    'idle_left': [],
    'run_right': [],
    'run_left': [],
    'jump_right': [],
    'jump_left': [],
    'double_jump_right': [],
    'double_jump_left': [],
    'hurt_right': [],
    'hurt_left': [],
    'death_right': [],
    'death_left': [],
    'flying_right': [],
    'flying_left': [],
    'invincible_right': [],
    'invincible_left': [],
    'speed_boost_right': [],
    'speed_boost_left': [],
    'dust_walk': [],
    'dust_double_jump': []
}

# ===== BACKGROUND ASSETS =====
background_layers = []
background_widths = []

# ===== CLOUD IMAGE =====
cloud_image = None

# ===== GAME OBJECT ASSETS =====
ground_texture = None
platform_texture = None
coin_sprite = None
powerup_sprites = {}
obstacle_sprites = {}
fire_animation_frames = []
saw_animation_frames = []
bomb_animation_frames = []
explosion_animation_frames = []

# ===== UI ASSETS =====
heart_sprite = None

# Target size for player sprites (should match player's collision box)
PLAYER_SPRITE_WIDTH = PLAYER_WIDTH
PLAYER_SPRITE_HEIGHT = PLAYER_HEIGHT

def load_all_assets():
    """Load all game assets."""
    try:
        # Web optimization: Load fewer assets in web environment
        if IS_WEB:
            logger.info("Loading assets for web environment (optimized)")
            # Load essential assets first
            load_fonts()
            load_player_sprites()
            load_ui_assets()
            
            # Load simplified background for web
            load_simplified_background()
            
            # Load game objects with reduced quality for web
            load_game_object_textures(web_optimized=True)
            
            logger.info("Web-optimized assets loaded successfully!")
        else:
            # Load all assets for desktop environment
            load_player_sprites()
            load_fonts()
            load_background_assets()
            load_cloud_image()
            load_game_object_textures()
            load_ui_assets()
            logger.info("All assets loaded successfully!")
    except SystemExit:
        # This will be triggered when one of the asset loading functions calls exit()
        logger.error("Asset loading failed. Exiting game.")
        exit()

def load_fonts():
    """Load and cache the game fonts."""
    try:
        # Load the default font size (we'll cache other sizes as needed)
        get_font(16)
    except Exception as e:
        logger.error(f"Error loading fonts: {e}")
        exit()

def get_font(size):
    """Load a font with the specified size, using cache for efficiency."""
    # Check if the font size is already in the cache
    if size in font_cache:
        return font_cache[size]
    
    # Font not in cache, load it
    try:
        font = pygame.font.Font(FONT_PATH, size)
    except Exception as e:
        logger.error(f"Error: Could not load font {FONT_PATH}: {e}")
        exit()
    
    # Cache the font for future use
    font_cache[size] = font
    return font

def load_background_assets():
    """Load background layers for parallax scrolling."""
    global background_layers, background_widths
    
    background_layers = []
    background_widths = []
    
    # List of background layer paths in order from back to front
    bg_paths = [
        SKY_PATH,
        CLOUDS_BG_PATH,
        MOUNTAINS_PATH,
        CLOUDS_MG_3_PATH,
        CLOUDS_MG_2_PATH,
        CLOUD_LONELY_PATH,
        CLOUDS_MG_1_PATH
    ]
    
    try:
        for path in bg_paths:
            try:
                # Load the layer
                layer = pygame.image.load(path).convert_alpha()
                
                # Get original dimensions
                orig_width = layer.get_width()
                orig_height = layer.get_height()
                
                # Calculate scale factor to match play area height
                scale_factor = PLAY_AREA_HEIGHT / orig_height
                new_width = int(orig_width * scale_factor)
                
                # Scale the layer
                scaled_layer = pygame.transform.scale(layer, (new_width, PLAY_AREA_HEIGHT))
                
                # Store the layer and its width
                background_layers.append(scaled_layer)
                background_widths.append(new_width)
            except Exception as e:
                logger.error(f"Error loading background layer {path}: {e}")
                exit()
    except Exception as e:
        logger.error(f"Error loading background assets: {e}")
        exit()

def load_player_sprites():
    """Load all player sprite sheets and extract animation frames."""
    global player_sprites, player_frames
    
    # Define sprite sheet paths
    sprite_paths = {
        'idle': PLAYER_IDLE_PATH,
        'run': PLAYER_RUN_PATH,
        'jump': PLAYER_JUMP_PATH,
        'hurt': PLAYER_HURT_PATH,
        'death': PLAYER_DEATH_PATH,
        'walk': PLAYER_WALK_PATH,
        'climb': PLAYER_CLIMB_PATH,
        'attack1': PLAYER_ATTACK1_PATH,
        'attack2': PLAYER_ATTACK2_PATH,
        'throw': PLAYER_THROW_PATH,
        'push': PLAYER_PUSH_PATH,
        'walk_attack': PLAYER_WALK_ATTACK_PATH,
        'dust_walk': PLAYER_DUST_WALK_PATH,
        'dust_double_jump': PLAYER_DUST_DOUBLE_JUMP_PATH
    }
    
    # Load sprite sheets
    for action, path in sprite_paths.items():
        try:
            player_sprites[action] = pygame.image.load(path).convert_alpha()
        except pygame.error as e:
            logger.error(f"Error loading sprite sheet {path}: {e}")
            exit()
    
    # Extract frames from sprite sheets
    # Idle animation (4 frames)
    extract_frames('idle', 4, 'idle_right', 'idle_left')
    
    # Run animation (6 frames)
    extract_frames('run', 6, 'run_right', 'run_left')
    
    # Jump animation (8 frames)
    extract_frames('jump', 8, 'jump_right', 'jump_left')
    # Use the first 4 frames for regular jump and last 4 for double jump
    player_frames['double_jump_right'] = player_frames['jump_right'][4:]
    player_frames['double_jump_left'] = player_frames['jump_left'][4:]
    player_frames['jump_right'] = player_frames['jump_right'][:4]
    player_frames['jump_left'] = player_frames['jump_left'][:4]
    
    # Hurt animation (4 frames)
    extract_frames('hurt', 4, 'hurt_right', 'hurt_left')
    
    # Death animation (8 frames)
    extract_frames('death', 8, 'death_right', 'death_left')
    
    # Flying animation (use jump frames with color overlay)
    player_frames['flying_right'] = player_frames['jump_right'].copy()
    player_frames['flying_left'] = player_frames['jump_left'].copy()
    
    # Invincible animation (use regular run frames without color overlay)
    player_frames['invincible_right'] = player_frames['run_right'].copy()
    player_frames['invincible_left'] = player_frames['run_left'].copy() 
    
    # Speed boost animation (use regular run frames without color overlay)
    player_frames['speed_boost_right'] = player_frames['run_right'].copy()
    player_frames['speed_boost_left'] = player_frames['run_left'].copy()
    
    # Extract dust effect frames
    extract_dust_frames('dust_walk', 6)
    extract_dust_frames('dust_double_jump', 5)

def extract_frames(action, num_frames, right_key, left_key):
    """Extract individual frames from a sprite sheet and create flipped versions."""
    if player_sprites[action] is None:
        return
    
    # Get the sprite sheet dimensions
    sheet_width = player_sprites[action].get_width()
    sheet_height = player_sprites[action].get_height()
    
    # Calculate frame width
    frame_width = sheet_width // num_frames
    
    # Extract each frame
    for i in range(num_frames):
        # Extract the frame
        frame_rect = pygame.Rect(i * frame_width, 0, frame_width, sheet_height)
        frame = pygame.Surface((frame_width, sheet_height), pygame.SRCALPHA)
        frame.blit(player_sprites[action], (0, 0), frame_rect)
        
        # Scale the frame to match the player's collision box
        # Preserve aspect ratio by scaling proportionally
        aspect_ratio = frame_width / sheet_height
        
        # Calculate new dimensions that maintain aspect ratio
        if aspect_ratio > 1:  # Wider than tall
            new_width = PLAYER_SPRITE_WIDTH
            new_height = int(PLAYER_SPRITE_WIDTH / aspect_ratio)
        else:  # Taller than wide or square
            new_height = PLAYER_SPRITE_HEIGHT
            new_width = int(PLAYER_SPRITE_HEIGHT * aspect_ratio)
        
        # Scale the frame
        scaled_frame = pygame.transform.scale(frame, (new_width, new_height))
        
        # Add the frame to the right-facing animation
        player_frames[right_key].append(scaled_frame)
        
        # Create and add the flipped frame for left-facing animation
        flipped_frame = pygame.transform.flip(scaled_frame, True, False)
        player_frames[left_key].append(flipped_frame)

def extract_dust_frames(action, num_frames):
    """Extract dust effect frames from a sprite sheet."""
    if player_sprites[action] is None:
        return
    
    # Get the sprite sheet dimensions
    sheet_width = player_sprites[action].get_width()
    sheet_height = player_sprites[action].get_height()
    
    # Calculate frame width
    frame_width = sheet_width // num_frames
    
    # Extract each frame
    for i in range(num_frames):
        # Extract the frame
        frame_rect = pygame.Rect(i * frame_width, 0, frame_width, sheet_height)
        frame = pygame.Surface((frame_width, sheet_height), pygame.SRCALPHA)
        frame.blit(player_sprites[action], (0, 0), frame_rect)
        
        # Scale the dust effect to be proportional to the player size
        # Dust should be about 60% of player size
        dust_scale = 0.6
        new_width = int(PLAYER_SPRITE_WIDTH * dust_scale)
        new_height = int(new_width * (sheet_height / frame_width))  # Maintain aspect ratio
        
        # Scale the frame
        scaled_frame = pygame.transform.scale(frame, (new_width, new_height))
        
        # Add the frame to the animation
        player_frames[action].append(scaled_frame)

def apply_color_overlay(frames, color):
    """Apply a color overlay to a set of frames."""
    overlaid_frames = []
    
    for frame in frames:
        # Create a copy of the frame
        overlaid_frame = frame.copy()
        
        # Create a surface for the overlay
        overlay = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
        overlay.fill(color)
        
        # Apply the overlay
        overlaid_frame.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        overlaid_frames.append(overlaid_frame)
    
    return overlaid_frames

def get_frame(animation_key, frame_index):
    """Get a specific frame from an animation sequence."""
    if animation_key in player_frames and player_frames[animation_key]:
        # Ensure the frame index is within bounds
        frame_index = frame_index % len(player_frames[animation_key])
        return player_frames[animation_key][frame_index]
    else:
        # Return a placeholder if the animation doesn't exist
        placeholder = pygame.Surface((PLAYER_SPRITE_WIDTH, PLAYER_SPRITE_HEIGHT), pygame.SRCALPHA)
        placeholder.fill((255, 0, 255))  # Fill with magenta for visibility
        return placeholder

def load_cloud_image():
    """Load cloud image."""
    global cloud_image
    
    try:
        cloud_image = pygame.image.load(CLOUD_LONELY_PATH).convert_alpha()
    except Exception as e:
        logger.error(f"Error loading cloud image: {e}")
        exit()

def load_game_object_textures(web_optimized=False):
    """Load textures for game objects."""
    global ground_texture, platform_texture, coin_sprite, powerup_sprites, obstacle_sprites
    global fire_animation_frames, saw_animation_frames, bomb_animation_frames, explosion_animation_frames
    
    # Initialize containers
    powerup_sprites = {}
    obstacle_sprites = {}
    fire_animation_frames = []
    saw_animation_frames = []
    bomb_animation_frames = []
    explosion_animation_frames = []
    
    try:
        # Load ground texture
        ground_texture = pygame.image.load(GROUND_TEXTURE_PATH).convert_alpha()
    except Exception as e:
        logger.error(f"Error loading ground texture: {e}")
        exit()
    
    try:
        # Load platform texture
        platform_texture = pygame.image.load(PLATFORM_TEXTURE_PATH).convert_alpha()
    except Exception as e:
        logger.error(f"Error loading platform texture: {e}")
        exit()
    
    try:
        # Load coin sprite
        coin_sprite = pygame.image.load(COIN_PATH).convert_alpha()
        # Resize to match the game's dimensions
        if coin_sprite.get_width() != COIN_SIZE or coin_sprite.get_height() != COIN_SIZE:
            coin_sprite = pygame.transform.scale(coin_sprite, (COIN_SIZE, COIN_SIZE))
    except Exception as e:
        logger.error(f"Error loading coin sprite: {e}")
        exit()
    
    # Web optimization: Load fewer animation frames for web
    if web_optimized:
        # Load power-ups with simplified approach
        try:
            # Only load essential power-ups for web
            powerup_paths = {
                'speed': POWERUP_SPEED_PATH,
                'life': POWERUP_LIFE_PATH
            }
            
            for p_type, path in powerup_paths.items():
                try:
                    powerup_sprites[p_type] = pygame.image.load(path).convert_alpha()
                    # Resize to match the game's dimensions if needed
                    if powerup_sprites[p_type].get_width() != POWERUP_SIZE or powerup_sprites[p_type].get_height() != POWERUP_SIZE:
                        powerup_sprites[p_type] = pygame.transform.scale(powerup_sprites[p_type], (POWERUP_SIZE, POWERUP_SIZE))
                except Exception as e:
                    logger.error(f"Error loading power-up sprite {path}: {e}")
                    exit()
        except Exception as e:
            logger.error(f"Error loading power-up sprites: {e}")
            exit()
        
        # Load simplified obstacle sprites
        try:
            # Load spikes
            obstacle_sprites['spikes'] = pygame.image.load(SPIKES_PATH).convert_alpha()
        except Exception as e:
            logger.error(f"Error loading spikes sprite: {e}")
            exit()
        
        # Load simplified fire animation (just one frame)
        try:
            fire_sprite = pygame.image.load(FIRE_PATH).convert_alpha()
            sheet_width = fire_sprite.get_width()
            frame_width = sheet_width // 3
            sheet_height = fire_sprite.get_height()
            
            # Just extract the first frame
            frame_rect = pygame.Rect(0, 0, frame_width, sheet_height)
            frame = fire_sprite.subsurface(frame_rect)
            fire_animation_frames.append(frame)
            
            # Store the first frame as the base sprite
            obstacle_sprites['fire'] = fire_animation_frames[0]
        except Exception as e:
            logger.error(f"Error loading fire sprite: {e}")
            exit()
    else:
        # Load all power-ups and animations for desktop
        try:
            # Load power-up sprites
            powerup_paths = {
                'speed': POWERUP_SPEED_PATH,
                'flying': POWERUP_FLYING_PATH,
                'invincibility': POWERUP_INVINCIBILITY_PATH,
                'life': POWERUP_LIFE_PATH
            }
            
            for p_type, path in powerup_paths.items():
                try:
                    powerup_sprites[p_type] = pygame.image.load(path).convert_alpha()
                    # Resize to match the game's dimensions if needed
                    if powerup_sprites[p_type].get_width() != POWERUP_SIZE or powerup_sprites[p_type].get_height() != POWERUP_SIZE:
                        powerup_sprites[p_type] = pygame.transform.scale(powerup_sprites[p_type], (POWERUP_SIZE, POWERUP_SIZE))
                except Exception as e:
                    logger.error(f"Error loading power-up sprite {path}: {e}")
                    # Don't exit, just log the error and continue
                    logger.warning(f"Continuing without power-up sprite {p_type}")
        except Exception as e:
            logger.error(f"Error loading power-up sprites: {e}")
            # Don't exit, just log the error and continue
            logger.warning("Continuing without power-up sprites")
        
        # Load spikes sprite
        try:
            obstacle_sprites['spikes'] = pygame.image.load(SPIKES_PATH).convert_alpha()
        except Exception as e:
            logger.error(f"Error loading spikes sprite: {e}")
            # Don't exit, just log the error and continue
            logger.warning("Continuing without spikes sprite")
        
        try:
            # Load fire animation frames (sprite sheet with 3 frames)
            fire_sprite_sheet = pygame.image.load(FIRE_PATH).convert_alpha()
            
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
            if fire_animation_frames:
                obstacle_sprites['fire'] = fire_animation_frames[0]
        except Exception as e:
            logger.error(f"Error loading fire sprite: {e}")
            # Don't exit, just log the error and continue
            logger.warning("Continuing without fire sprite")
        
        try:
            # Load saw animation frames (sprite sheet with 8 frames)
            saw_sprite_sheet = pygame.image.load(SAW_PATH).convert_alpha()
            
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
            if saw_animation_frames:
                obstacle_sprites['saw'] = saw_animation_frames[0]
        except Exception as e:
            logger.error(f"Error loading saw sprite: {e}")
            # Don't exit, just log the error and continue
            logger.warning("Continuing without saw sprite")
        
        try:
            # Load bomb animation frames
            for i in range(1, 11):  # 10 frames
                path = f"{BOMB_DIR_PATH}/{i}.png"
                try:
                    frame = pygame.image.load(path).convert_alpha()
                    bomb_animation_frames.append(frame)
                except Exception as e:
                    logger.error(f"Error loading bomb frame {i}: {e}")
                    # Don't exit, just log the error and continue
                    logger.warning(f"Continuing without bomb frame {i}")
            
            # Store the first frame as the base sprite if available
            if bomb_animation_frames:
                obstacle_sprites['bomb'] = bomb_animation_frames[0]
        except Exception as e:
            logger.error(f"Error loading bomb frames: {e}")
            # Don't exit, just log the error and continue
            logger.warning("Continuing without bomb frames")
        
        try:
            # Load explosion animation frames
            for i in range(1, 10):  # 9 frames
                path = f"{EXPLOSION_DIR_PATH}/{i}.png"
                try:
                    frame = pygame.image.load(path).convert_alpha()
                    explosion_animation_frames.append(frame)
                except Exception as e:
                    logger.error(f"Error loading explosion frame {i}: {e}")
                    # Don't exit, just log the error and continue
                    logger.warning(f"Continuing without explosion frame {i}")
        except Exception as e:
            logger.error(f"Error loading explosion frames: {e}")
            # Don't exit, just log the error and continue
            logger.warning("Continuing without explosion frames")

def load_ui_assets():
    """Load UI assets like heart sprite."""
    global heart_sprite
    
    try:
        heart_sprite = pygame.image.load(HEART_SPRITE_PATH).convert_alpha()
    except Exception as e:
        logger.error(f"Error loading heart sprite: {e}")
        exit()

def get_cloud_image():
    """Get the cloud image."""
    return cloud_image

def get_heart_sprite():
    """Get the heart sprite for UI."""
    return heart_sprite

def get_background_layers():
    """Get the background layers."""
    return background_layers

def get_background_widths():
    """Get the background layer widths."""
    return background_widths

def get_ground_texture():
    """Get the ground texture."""
    return ground_texture

def get_platform_texture():
    """Get the platform texture."""
    return platform_texture

def get_coin_sprite():
    """Get the coin sprite."""
    return coin_sprite

def get_powerup_sprite(type):
    """Get a powerup sprite by type."""
    return powerup_sprites.get(type)

def get_obstacle_sprite(type):
    """Get an obstacle sprite by type."""
    return obstacle_sprites.get(type)

def get_fire_animation_frames():
    """Get the fire animation frames."""
    return fire_animation_frames

def get_saw_animation_frames():
    """Get the saw animation frames."""
    return saw_animation_frames

def get_bomb_animation_frames():
    """Get the bomb animation frames."""
    return bomb_animation_frames

def get_explosion_animation_frames():
    """Get the explosion animation frames."""
    return explosion_animation_frames

def load_simplified_background():
    """Load simplified background for web environment."""
    global background_layers, background_widths
    
    background_layers = []
    background_widths = []
    
    # For web, only load the essential background layers
    bg_paths = [
        SKY_PATH,
        MOUNTAINS_PATH,
    ]
    
    try:
        for path in bg_paths:
            img = pygame.image.load(path).convert_alpha()
            
            # Web optimization: Scale down background images for better performance
            if IS_WEB:
                # Reduce the size by 25% for web
                new_width = int(img.get_width() * 0.75)
                new_height = int(img.get_height() * 0.75)
                img = pygame.transform.scale(img, (new_width, new_height))
            
            background_layers.append(img)
            background_widths.append(img.get_width())
    except Exception as e:
        logger.error(f"Error loading background assets: {e}")
        exit() 