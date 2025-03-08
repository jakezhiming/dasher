import pygame
import os

# Dictionary to store all loaded sprite sheets
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

# Target size for player sprites (should match player's collision box)
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 50

def load_player_sprites():
    """Load all player sprite sheets and extract animation frames."""
    global player_sprites, player_frames
    
    # Define sprite sheet paths
    sprite_paths = {
        'idle': "assets/images/player/Dude_Monster_Idle_4.png",
        'run': "assets/images/player/Dude_Monster_Run_6.png",
        'jump': "assets/images/player/Dude_Monster_Jump_8.png",
        'hurt': "assets/images/player/Dude_Monster_Hurt_4.png",
        'death': "assets/images/player/Dude_Monster_Death_8.png",
        'walk': "assets/images/player/Dude_Monster_Walk_6.png",
        'climb': "assets/images/player/Dude_Monster_Climb_4.png",
        'attack1': "assets/images/player/Dude_Monster_Attack1_4.png",
        'attack2': "assets/images/player/Dude_Monster_Attack2_6.png",
        'throw': "assets/images/player/Dude_Monster_Throw_4.png",
        'push': "assets/images/player/Dude_Monster_Push_6.png",
        'walk_attack': "assets/images/player/Dude_Monster_Walk+Attack_6.png",
        'dust_walk': "assets/images/player/Walk_Run_Push_Dust_6.png",
        'dust_double_jump': "assets/images/player/Double_Jump_Dust_5.png"
    }
    
    # Load sprite sheets
    for action, path in sprite_paths.items():
        try:
            player_sprites[action] = pygame.image.load(path).convert_alpha()
            print(f"Successfully loaded sprite sheet: {path}")
        except pygame.error as e:
            print(f"Error loading sprite sheet {path}: {e}")
            # Use a placeholder if sprite can't be loaded
            player_sprites[action] = pygame.Surface((32, 32), pygame.SRCALPHA)
    
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
    player_frames['flying_right'] = apply_color_overlay(player_frames['jump_right'], (0, 191, 255, 100))
    player_frames['flying_left'] = apply_color_overlay(player_frames['jump_left'], (0, 191, 255, 100))
    
    # Invincible animation (use run frames with color overlay)
    player_frames['invincible_right'] = apply_color_overlay(player_frames['run_right'], (218, 112, 214, 100))
    player_frames['invincible_left'] = apply_color_overlay(player_frames['run_left'], (218, 112, 214, 100))
    
    # Speed boost animation (use run frames with blue color overlay)
    player_frames['speed_boost_right'] = apply_color_overlay(player_frames['run_right'], (0, 191, 255, 100))
    player_frames['speed_boost_left'] = apply_color_overlay(player_frames['run_left'], (0, 191, 255, 100))
    
    # Extract dust effect frames
    extract_dust_frames('dust_walk', 6)
    extract_dust_frames('dust_double_jump', 5)
    
    print(f"Successfully loaded all player sprites and animations")

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
            new_width = PLAYER_WIDTH
            new_height = int(PLAYER_WIDTH / aspect_ratio)
        else:  # Taller than wide or square
            new_height = PLAYER_HEIGHT
            new_width = int(PLAYER_HEIGHT * aspect_ratio)
        
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
        new_width = int(PLAYER_WIDTH * dust_scale)
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
        placeholder = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        placeholder.fill((255, 0, 255))  # Fill with magenta for visibility
        return placeholder 