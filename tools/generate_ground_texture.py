import pygame
import os
import random

# Initialize pygame
pygame.init()

# Texture dimensions
TEXTURE_WIDTH = 64
TEXTURE_HEIGHT = 20

# Colors for retro ground texture
DARK_BROWN = (101, 67, 33)
MEDIUM_BROWN = (139, 69, 19)
LIGHT_BROWN = (160, 82, 45)
HIGHLIGHT = (205, 133, 63)
PIXEL_DETAIL = (222, 184, 135)  # Burlywood for pixel details

# Create the texture surface
ground_texture = pygame.Surface((TEXTURE_WIDTH, TEXTURE_HEIGHT))

# Fill with base color
ground_texture.fill(MEDIUM_BROWN)

# Create a brick pattern
brick_width = 16
brick_height = 10
offset = 0

for y in range(0, TEXTURE_HEIGHT, brick_height):
    offset = 0 if y % (brick_height * 2) == 0 else brick_width // 2
    for x in range(-offset, TEXTURE_WIDTH, brick_width):
        # Draw brick rectangle
        brick_rect = pygame.Rect(x, y, brick_width - 1, brick_height - 1)
        pygame.draw.rect(ground_texture, LIGHT_BROWN, brick_rect)
        
        # Draw brick outline
        pygame.draw.rect(ground_texture, DARK_BROWN, brick_rect, 1)
        
        # Add some random pixel noise within each brick
        for i in range(3):
            px = random.randint(x + 2, x + brick_width - 3)
            py = random.randint(y + 2, y + brick_height - 3)
            if 0 <= px < TEXTURE_WIDTH and 0 <= py < TEXTURE_HEIGHT:
                ground_texture.set_at((px, py), DARK_BROWN)

# Add some highlights at the top
for x in range(TEXTURE_WIDTH):
    if x % 4 == 0:  # Pixelated highlight pattern
        ground_texture.set_at((x, 0), HIGHLIGHT)
        if random.random() < 0.3:
            ground_texture.set_at((x, 1), HIGHLIGHT)

# Add some pixel details for a retro look
for i in range(8):
    x = random.randint(0, TEXTURE_WIDTH - 2)
    y = random.randint(2, TEXTURE_HEIGHT - 2)
    # Draw a small pixel detail
    ground_texture.set_at((x, y), PIXEL_DETAIL)

# Ensure the directory exists
os.makedirs("assets/images/textures", exist_ok=True)

# Save the texture
pygame.image.save(ground_texture, "assets/images/textures/ground_texture.png")
print("Enhanced ground texture generated successfully!") 