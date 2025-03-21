import pygame
from src.constants.paths import FONT_PATH
from src.core.assets_loader import (
    get_font,
    get_background_layers,
    get_background_widths,
    create_cached_background,
    get_cached_background,
    IS_WEB,
    USE_CACHED_BACKGROUND,
)
from src.utils.logger import get_module_logger

logger = get_module_logger("utils")

# Font cache to store loaded fonts by size
_font_cache = {}

# Cloud image cache
_cloud_image = None


def get_cloud_image():
    """Get the cloud image, loading it if necessary."""
    global _cloud_image
    if _cloud_image is None:
        try:
            _cloud_image = pygame.image.load(
                "assets/images/background/cloud_lonely.png"
            ).convert_alpha()
        except Exception as e:
            logger.error(f"Could not load cloud_lonely.png: {e}")
            exit()
    return _cloud_image


def get_retro_font(size):
    """Load the retro font with the specified size, using cache for efficiency."""
    # Check if the font size is already in the cache
    if size in _font_cache:
        return _font_cache[size]

    # Font not in cache, load it
    try:
        font = pygame.font.Font(FONT_PATH, size)
    except:
        # Fallback to default font if the retro font fails to load
        logger.error("Could not load retro font")
        exit()

    # Store in cache for future use
    _font_cache[size] = font
    return font


def render_retro_text(text, size, color, max_width=None):
    """Render text with proper wrapping to prevent cutoff."""
    font = get_font(size)

    # If no max width specified or text fits, render normally
    if max_width is None or font.size(text)[0] <= max_width:
        return font.render(text, True, color)

    # Text needs wrapping
    words = text.split(" ")
    lines = []
    current_line = []

    for word in words:
        # Try adding the word to the current line
        test_line = " ".join(current_line + [word])
        test_width = font.size(test_line)[0]

        if test_width <= max_width:
            # Word fits, add it to the current line
            current_line.append(word)
        else:
            # Word doesn't fit, start a new line
            if current_line:  # Only add the line if it's not empty
                lines.append(" ".join(current_line))
            current_line = [word]

    # Add the last line if it's not empty
    if current_line:
        lines.append(" ".join(current_line))

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
    """Check if two rectangles collide.

    For obstacles with custom collision boxes, use their get_collision_rect method.
    """
    # Check if rect2 is an obstacle with a custom collision box
    if hasattr(rect2, "get_collision_rect"):
        collision_rect = rect2.get_collision_rect()
        return (
            rect1.x < collision_rect.x + collision_rect.width
            and rect1.x + rect1.width > collision_rect.x
            and rect1.y < collision_rect.y + collision_rect.height
            and rect1.y + rect1.height > collision_rect.y
        )

    # Standard collision check for regular objects
    return (
        rect1.x < rect2.x + rect2.width
        and rect1.x + rect1.width > rect2.x
        and rect1.y < rect2.y + rect2.height
        and rect1.y + rect1.height > rect2.y
    )


def draw_background(screen, camera_x=0):
    """Draw a parallax background using the Glacial Mountains assets."""
    screen_width = screen.get_width()

    if IS_WEB or USE_CACHED_BACKGROUND:
        cached_bg = get_cached_background()

        # If screen width changed or no cached background exists, create one
        if cached_bg is None or screen_width != cached_bg.get_width():
            cached_bg = create_cached_background(screen_width)

        # Draw the cached background if available, otherwise fall back to regular drawing
        if cached_bg:
            screen.blit(cached_bg, (0, 0))
            return
        # If cached_bg is still None, we'll fall through to the regular drawing method

    # Regular (non-cached) background drawing
    background_layers = get_background_layers()
    background_widths = get_background_widths()

    if not background_layers or not background_widths:
        logger.error("No background layers or widths loaded")
        exit()

    # Different layers move at different speeds
    # Sky is fixed (0.0), mountains move slowly, clouds move faster
    parallax_factors = [0.0, 0.05, 0.1, 0.15, 0.2, 0.225, 0.25]

    for i, layer in enumerate(background_layers):
        if i >= len(parallax_factors):
            break

        layer_offset = int(-(camera_x * parallax_factors[i])) % background_widths[i]

        # Draw the layer, potentially multiple times to cover the screen
        # First draw at the calculated offset
        screen.blit(layer, (layer_offset, 0))

        # If the first instance doesn't cover the entire screen, draw additional instances
        # Draw to the right if needed
        if layer_offset + background_widths[i] < screen_width:
            screen.blit(layer, (layer_offset + background_widths[i], 0))

        # Draw to the left if needed (for when the offset is positive)
        if layer_offset > 0:
            screen.blit(layer, (layer_offset - background_widths[i], 0))
