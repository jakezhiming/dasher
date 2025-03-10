import pygame
import os
import math

# Initialize pygame
pygame.init()

# Create the sprites directory if it doesn't exist
os.makedirs("assets/images/powerups", exist_ok=True)

# Set up colors
YELLOW = (255, 215, 0)      # Gold for coin
YELLOW_DARK = (220, 185, 0)  # Darker gold for gradient
BLUE = (30, 144, 255)       # Speed power-up (dodger blue)
BLUE_DARK = (0, 90, 200)    # Darker blue for gradient
CYAN = (0, 200, 255)        # Flying power-up
CYAN_DARK = (0, 150, 200)   # Darker cyan for gradient
MAGENTA = (255, 50, 255)    # Invincibility power-up
MAGENTA_DARK = (200, 0, 200) # Darker magenta for gradient
RED = (255, 60, 60)         # Life power-up
RED_DARK = (200, 0, 0)      # Darker red for gradient
BLACK = (0, 0, 0)           # Outline
WHITE = (255, 255, 255)     # Highlight

# Global settings
OUTLINE_THICKNESS = 3       # Thickness for all outlines

# Function to create a sprite surface with improved quality
def create_sprite(size, color, sprite_type):
    # Create a larger surface for better quality
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    if sprite_type == "coin":
        # Draw a high-quality coin with gradient
        radius = size//2 - 2
        center = (size//2, size//2)
        
        # Draw base circle with gradient
        for r in range(radius, 0, -1):
            ratio = r / radius
            current_color = (
                int(YELLOW[0] * ratio + YELLOW_DARK[0] * (1-ratio)),
                int(YELLOW[1] * ratio + YELLOW_DARK[1] * (1-ratio)),
                int(YELLOW[2] * ratio + YELLOW_DARK[2] * (1-ratio))
            )
            pygame.draw.circle(surface, current_color, center, r)
        
        # Add a thicker outline
        pygame.draw.circle(surface, BLACK, center, radius, OUTLINE_THICKNESS)
        
        # Add highlights
        highlight_radius = size//5
        highlight_pos = (center[0] - radius//3, center[1] - radius//3)
        for r in range(highlight_radius, 0, -1):
            alpha = 150 - (r * 100 // highlight_radius)
            highlight = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(highlight, (255, 255, 255, alpha), (r, r), r)
            surface.blit(highlight, (highlight_pos[0]-r, highlight_pos[1]-r))
        
        # Add a smaller highlight
        small_highlight_pos = (center[0] + radius//4, center[1] + radius//4)
        small_highlight_radius = size//10
        for r in range(small_highlight_radius, 0, -1):
            alpha = 100 - (r * 80 // small_highlight_radius)
            highlight = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(highlight, (255, 255, 255, alpha), (r, r), r)
            surface.blit(highlight, (small_highlight_pos[0]-r, small_highlight_pos[1]-r))
    
    elif sprite_type.startswith("powerup"):
        power_type = sprite_type.split("_")[1]
        
        if power_type == "speed":
            main_color = BLUE
            dark_color = BLUE_DARK
        elif power_type == "flying":
            main_color = CYAN
            dark_color = CYAN_DARK
        elif power_type == "invincibility":
            main_color = MAGENTA
            dark_color = MAGENTA_DARK
        elif power_type == "life":
            main_color = RED
            dark_color = RED_DARK
        
        # Draw a high-quality power-up (rounded diamond shape with gradient)
        center = (size//2, size//2)
        radius = size//2 - 2
        
        # Create a diamond shape with rounded corners
        points = []
        corner_radius = size//10
        
        # Define the main diamond points
        diamond_points = [
            (center[0], center[1] - radius),  # Top
            (center[0] + radius, center[1]),  # Right
            (center[0], center[1] + radius),  # Bottom
            (center[0] - radius, center[1])   # Left
        ]
        
        # Draw the main shape with gradient
        for i in range(radius, 0, -1):
            ratio = i / radius
            current_color = (
                int(main_color[0] * ratio + dark_color[0] * (1-ratio)),
                int(main_color[1] * ratio + dark_color[1] * (1-ratio)),
                int(main_color[2] * ratio + dark_color[2] * (1-ratio))
            )
            
            # Scale the diamond points based on the current radius
            scaled_points = [
                (center[0], center[1] - i),  # Top
                (center[0] + i, center[1]),  # Right
                (center[0], center[1] + i),  # Bottom
                (center[0] - i, center[1])   # Left
            ]
            
            pygame.draw.polygon(surface, current_color, scaled_points)
        
        # Add a subtle outline
        pygame.draw.polygon(surface, BLACK, diamond_points, OUTLINE_THICKNESS)
        
        # Add a highlight effect (top-left quadrant)
        highlight_points = [
            (center[0], center[1] - radius//2),
            (center[0] - radius//2, center[1]),
            (center[0], center[1] - radius//5)
        ]
        
        # Create a semi-transparent highlight
        highlight_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(highlight_surface, (255, 255, 255, 100), highlight_points)
        surface.blit(highlight_surface, (0, 0))
        
        # Add a subtle glow effect
        glow_radius = radius + 4
        glow_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        for r in range(glow_radius, radius, -1):
            alpha = 10 - (r - radius) * 2
            if alpha > 0:
                pygame.draw.polygon(glow_surface, (*main_color, alpha), [
                    (center[0], center[1] - r),  # Top
                    (center[0] + r, center[1]),  # Right
                    (center[0], center[1] + r),  # Bottom
                    (center[0] - r, center[1])   # Left
                ])
        surface.blit(glow_surface, (0, 0))
    
    return surface

# Create and save sprites
def save_sprite(sprite, filename):
    full_path = os.path.join("assets/images/powerups", filename)
    pygame.image.save(sprite, full_path)
    print(f"Created {full_path}")

# Default size increased for better quality
DEFAULT_SIZE = 64

# Create coin sprite
coin_sprite = create_sprite(DEFAULT_SIZE, YELLOW, "coin")
save_sprite(coin_sprite, "coin.png")

# Create power-up sprites
powerup_types = ['speed', 'flying', 'invincibility', 'life']
for p_type in powerup_types:
    powerup_sprite = create_sprite(DEFAULT_SIZE, None, f"powerup_{p_type}")
    save_sprite(powerup_sprite, f"powerup_{p_type}.png")

print("All sprites created successfully!")
pygame.quit() 