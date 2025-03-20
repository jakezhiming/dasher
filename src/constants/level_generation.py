"""Level generation constants for the Dasher game."""

# ===== LEVEL GENERATION =====
SEGMENT_LENGTH_MULTIPLIER = 3  # Generate segments 3x the screen width
GRID_CELL_SIZE = 100  # Size of collision grid cells
OBSTACLE_BUFFER = 10  # Buffer around obstacles for collision detection
MIN_PLATFORM_WIDTH = 50  # Minimum width for platforms
MAX_PLATFORM_WIDTH = 150  # Maximum width for platforms
PLATFORM_EDGE_BUFFER = 60  # Buffer from edge of pit (per side)
MIN_PLATFORM_HORIZONTAL_DISTANCE = 50  # Minimum horizontal distance between platforms
