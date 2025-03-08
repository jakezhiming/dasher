import pygame
import os
import math
import random

# Initialize pygame
pygame.init()

# Create directory if it doesn't exist
os.makedirs("assets/images/obstacles", exist_ok=True)

# Define colors
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
GRAY = (128, 128, 128)
DARK_GRAY = (80, 80, 80)
RED = (255, 0, 0)
DARK_RED = (139, 0, 0)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
SILVER = (192, 192, 192)

# Function to create a rock sprite
def create_rock_sprite():
    # Create a surface for the rock (base size 30x30)
    surface = pygame.Surface((30, 30), pygame.SRCALPHA)
    
    # Draw the rock shape (irregular polygon)
    points = [(5, 15), (8, 5), (15, 2), (22, 5), (25, 15), (22, 25), (15, 28), (8, 25)]
    pygame.draw.polygon(surface, GRAY, points)
    
    # Add some shading/details
    pygame.draw.line(surface, DARK_GRAY, (10, 10), (20, 10), 2)
    pygame.draw.line(surface, DARK_GRAY, (8, 20), (22, 20), 2)
    pygame.draw.circle(surface, DARK_GRAY, (15, 15), 3)
    
    return surface

# Function to create a crate sprite
def create_crate_sprite():
    # Create a surface for the crate
    surface = pygame.Surface((30, 30), pygame.SRCALPHA)
    
    # Draw the crate (square with details)
    pygame.draw.rect(surface, BROWN, (2, 2, 26, 26))
    
    # Add wooden plank details
    pygame.draw.line(surface, DARK_BROWN, (2, 10), (28, 10), 2)
    pygame.draw.line(surface, DARK_BROWN, (2, 20), (28, 20), 2)
    pygame.draw.line(surface, DARK_BROWN, (10, 2), (10, 28), 2)
    pygame.draw.line(surface, DARK_BROWN, (20, 2), (20, 28), 2)
    
    return surface

# Function to create a spikes sprite
def create_spikes_sprite():
    # Create a surface for the spikes
    surface = pygame.Surface((30, 30), pygame.SRCALPHA)
    
    # Draw the base
    pygame.draw.rect(surface, DARK_GRAY, (0, 20, 30, 10))
    
    # Draw more prominent spikes
    for i in range(6):
        x = i * 5
        # Make spikes taller and more prominent
        pygame.draw.polygon(surface, RED, [(x, 20), (x+2.5, 3), (x+5, 20)])
        # Add highlight
        pygame.draw.line(surface, YELLOW, (x+1, 18), (x+2.5, 6), 1)
    
    return surface

# Function to create a lava pit sprite
def create_lava_sprite():
    # Create a surface for the lava
    surface = pygame.Surface((30, 30), pygame.SRCALPHA)
    
    # Draw the lava base with gradient effect
    for y in range(30):
        # Create a gradient from dark red to bright orange
        color_value = min(255, 139 + (y * 5))
        color = (color_value, max(0, min(165, y * 8)), 0)
        pygame.draw.line(surface, color, (0, y), (30, y))
    
    # Add lava bubbles and details
    for i in range(5):
        x = 3 + i * 6
        y = 5 if i % 2 == 0 else 15
        size = random.randint(2, 4)
        pygame.draw.circle(surface, YELLOW, (x, y), size)
        pygame.draw.circle(surface, ORANGE, (x, y), size-1)
    
    # Add lava surface waves
    for i in range(6):
        x = i * 5
        pygame.draw.arc(surface, YELLOW, (x, 2, 10, 10), 0, math.pi, 2)
    
    return surface

# Function to create a saw blade sprite
def create_saw_sprite():
    # Create a surface for the saw
    surface = pygame.Surface((30, 30), pygame.SRCALPHA)
    
    # Draw the saw blade base
    pygame.draw.circle(surface, SILVER, (15, 15), 14)
    pygame.draw.circle(surface, DARK_GRAY, (15, 15), 4)
    
    # Draw the saw teeth - more teeth for better visibility
    for i in range(12):
        angle = i * math.pi / 6
        x1 = 15 + 14 * math.cos(angle)
        y1 = 15 + 14 * math.sin(angle)
        x2 = 15 + 18 * math.cos(angle)
        y2 = 15 + 18 * math.sin(angle)
        pygame.draw.line(surface, DARK_GRAY, (x1, y1), (x2, y2), 3)
    
    # Add some detail to make it look more dangerous
    pygame.draw.circle(surface, RED, (15, 15), 8, 1)
    
    return surface

# Generate and save the sprites
sprites = {
    "rock": create_rock_sprite(),
    "crate": create_crate_sprite(),
    "spikes": create_spikes_sprite(),
    "lava": create_lava_sprite(),
    "saw": create_saw_sprite()
}

for name, sprite in sprites.items():
    path = f"assets/images/obstacles/obstacle_{name}.png"
    pygame.image.save(sprite, path)
    print(f"Created {path}")

print("All obstacle sprites generated successfully!") 