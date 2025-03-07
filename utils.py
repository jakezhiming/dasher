import pygame
from constants import FONT_PATH

def get_retro_font(size):
    """Load the retro font with the specified size."""
    try:
        return pygame.font.Font(FONT_PATH, size)
    except:
        # Fallback to default font if the retro font fails to load
        print("Warning: Could not load retro font, using default font instead")
        return pygame.font.Font(None, size)

def render_retro_text(text, size, color, max_width=None):
    """Render text with proper wrapping to prevent cutoff."""
    font = get_retro_font(size)
    
    # If no max width specified or text fits, render normally
    if max_width is None or font.size(text)[0] <= max_width:
        return font.render(text, True, color)
    
    # Text needs wrapping
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        # Try adding the word to the current line
        test_line = ' '.join(current_line + [word])
        test_width = font.size(test_line)[0]
        
        if test_width <= max_width:
            # Word fits, add it to the current line
            current_line.append(word)
        else:
            # Word doesn't fit, start a new line
            if current_line:  # Only add the line if it's not empty
                lines.append(' '.join(current_line))
            current_line = [word]
    
    # Add the last line if it's not empty
    if current_line:
        lines.append(' '.join(current_line))
    
    # Render each line
    line_surfaces = [font.render(line, True, color) for line in lines]
    
    # Calculate the total height needed
    line_height = font.get_linesize()
    total_height = line_height * len(line_surfaces)
    
    # Create a surface to hold all lines
    text_surface = pygame.Surface((max_width, total_height), pygame.SRCALPHA)
    
    # Blit each line onto the surface
    for i, line_surface in enumerate(line_surfaces):
        text_surface.blit(line_surface, (0, i * line_height))
    
    return text_surface

def collide(rect1, rect2):
    """Check if two rectangles collide."""
    return (rect1.x < rect2.x + rect2.width and
            rect1.x + rect1.width > rect2.x and
            rect1.y < rect2.y + rect2.height and
            rect1.y + rect1.height > rect2.y)

def draw_gradient_background(screen):
    """Draw a gradient background from light blue at the top to a slightly darker blue at the bottom."""
    from constants import LIGHT_BLUE, PLAY_AREA_HEIGHT
    
    # Create a gradient from light blue at the top to a slightly darker blue at the bottom
    top_color = LIGHT_BLUE
    bottom_color = (135, 206, 235)  # Sky blue
    
    for y in range(PLAY_AREA_HEIGHT):
        # Calculate the color for this line by interpolating between top and bottom colors
        ratio = y / PLAY_AREA_HEIGHT
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        color = (r, g, b)
        
        # Draw a horizontal line with this color
        pygame.draw.line(screen, color, (0, y), (screen.get_width(), y)) 