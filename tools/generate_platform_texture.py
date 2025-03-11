from compat import pygame
import os
import random

# Initialize pygame
pygame.init()

# Texture dimensions
TEXTURE_WIDTH = 64
TEXTURE_HEIGHT = 20

# Colors for retro platform texture - using a more cohesive color scheme
DARK_GRAY = (80, 80, 80)       # Dark gray for shadows and outlines
MEDIUM_GRAY = (120, 120, 120)  # Medium gray for base
LIGHT_GRAY = (160, 160, 160)   # Light gray for highlights
METAL_BLUE = (140, 160, 180)   # Slight blue tint for metallic look
HIGHLIGHT = (200, 200, 210)    # Almost white highlight
RIVET_COLOR = (60, 60, 70)     # Dark color for rivets

# Create the texture surface
platform_texture = pygame.Surface((TEXTURE_WIDTH, TEXTURE_HEIGHT))

# Fill with base color
platform_texture.fill(MEDIUM_GRAY)

# Create a metal plate pattern
plate_width = 16
plate_height = TEXTURE_HEIGHT

# Draw metal plates
for x in range(0, TEXTURE_WIDTH, plate_width):
    # Draw plate rectangle with slight gradient
    for y in range(TEXTURE_HEIGHT):
        # Create a subtle gradient from top to bottom
        gradient_factor = y / TEXTURE_HEIGHT
        color_value = int(MEDIUM_GRAY[0] + (LIGHT_GRAY[0] - MEDIUM_GRAY[0]) * (1 - gradient_factor))
        platform_texture.set_at((x + plate_width//2, y), (color_value, color_value, color_value + 10))
    
    # Draw plate outline
    plate_rect = pygame.Rect(x, 0, plate_width, plate_height)
    pygame.draw.rect(platform_texture, DARK_GRAY, plate_rect, 1)
    
    # Add horizontal line for a metal plate look
    pygame.draw.line(platform_texture, DARK_GRAY, (x, TEXTURE_HEIGHT//2), (x + plate_width, TEXTURE_HEIGHT//2), 1)

# Add rivets at the corners of each plate
for x in range(0, TEXTURE_WIDTH, plate_width):
    # Top rivets
    pygame.draw.circle(platform_texture, RIVET_COLOR, (x + 2, 2), 2)
    pygame.draw.circle(platform_texture, RIVET_COLOR, (x + plate_width - 3, 2), 2)
    
    # Bottom rivets
    pygame.draw.circle(platform_texture, RIVET_COLOR, (x + 2, TEXTURE_HEIGHT - 3), 2)
    pygame.draw.circle(platform_texture, RIVET_COLOR, (x + plate_width - 3, TEXTURE_HEIGHT - 3), 2)
    
    # Middle rivets
    pygame.draw.circle(platform_texture, RIVET_COLOR, (x + 2, TEXTURE_HEIGHT//2), 2)
    pygame.draw.circle(platform_texture, RIVET_COLOR, (x + plate_width - 3, TEXTURE_HEIGHT//2), 2)

# Add some highlights at the top edge
for x in range(TEXTURE_WIDTH):
    platform_texture.set_at((x, 0), HIGHLIGHT)
    if x % 3 == 0:  # Pixelated highlight pattern
        platform_texture.set_at((x, 1), HIGHLIGHT)

# Add some scratches for a worn metal look
for i in range(12):
    x = random.randint(0, TEXTURE_WIDTH - 5)
    y = random.randint(3, TEXTURE_HEIGHT - 3)
    length = random.randint(3, 8)
    
    # Draw a small scratch line
    for j in range(length):
        if x + j < TEXTURE_WIDTH:
            platform_texture.set_at((x + j, y), LIGHT_GRAY)

# Ensure the directory exists
os.makedirs("assets/images/textures", exist_ok=True)

# Save the texture
pygame.image.save(platform_texture, "assets/images/textures/platform_texture.png")
print("Redesigned platform texture generated successfully!")