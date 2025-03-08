import pygame
import os

# Initialize pygame
pygame.init()

# Create the sprites directory if it doesn't exist
os.makedirs("assets/images/powerups", exist_ok=True)

# Set up colors
YELLOW = (255, 215, 0)  # Gold for coin
BLUE = (0, 0, 255)      # Speed power-up
CYAN = (0, 255, 255)    # Flying power-up
MAGENTA = (255, 0, 255) # Invincibility power-up
RED = (255, 0, 0)       # Life power-up
BLACK = (0, 0, 0)       # Outline
WHITE = (255, 255, 255) # Highlight

# Function to create a sprite surface
def create_sprite(size, color, sprite_type):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    if sprite_type == "coin":
        # Draw a retro coin (circle with details)
        pygame.draw.circle(surface, YELLOW, (size//2, size//2), size//2 - 1)
        pygame.draw.circle(surface, BLACK, (size//2, size//2), size//2 - 1, 1)  # Outline
        # Add a highlight
        pygame.draw.circle(surface, WHITE, (size//3, size//3), size//6)
        # Add a dollar sign
        font = pygame.font.SysFont('Arial', size//2)
        text = font.render('$', True, BLACK)
        text_rect = text.get_rect(center=(size//2, size//2))
        surface.blit(text, text_rect)
    
    elif sprite_type.startswith("powerup"):
        power_type = sprite_type.split("_")[1]
        
        if power_type == "speed":
            main_color = BLUE
            symbol = "S"
        elif power_type == "flying":
            main_color = CYAN
            symbol = "F"
        elif power_type == "invincibility":
            main_color = MAGENTA
            symbol = "I"
        elif power_type == "life":
            main_color = RED
            symbol = "♥"
        
        # Draw a retro power-up (diamond shape with details)
        points = [
            (size//2, 0),           # Top
            (size-1, size//2),      # Right
            (size//2, size-1),      # Bottom
            (0, size//2)            # Left
        ]
        pygame.draw.polygon(surface, main_color, points)
        pygame.draw.polygon(surface, BLACK, points, 1)  # Outline
        
        # Add a highlight
        highlight_points = [
            (size//2, size//5),
            (size//5, size//2),
            (size//2, size*2//5)
        ]
        pygame.draw.polygon(surface, WHITE, highlight_points)
        
        # Add the symbol
        font = pygame.font.SysFont('Arial', size//2)
        text = font.render(symbol, True, WHITE)
        text_rect = text.get_rect(center=(size//2, size//2))
        surface.blit(text, text_rect)
    
    return surface

# Create and save sprites
def save_sprite(sprite, filename):
    full_path = os.path.join("assets/images/powerups", filename)
    pygame.image.save(sprite, full_path)
    print(f"Created {full_path}")

# Create coin sprite
coin_sprite = create_sprite(32, YELLOW, "coin")
save_sprite(coin_sprite, "coin.png")

# Create power-up sprites
powerup_types = ['speed', 'flying', 'invincibility', 'life']
for p_type in powerup_types:
    powerup_sprite = create_sprite(32, None, f"powerup_{p_type}")
    save_sprite(powerup_sprite, f"powerup_{p_type}.png")

print("All sprites created successfully!")
pygame.quit() 