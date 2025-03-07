import pygame

# Font path
FONT_PATH = "fonts/press-start-2p.ttf"

# Screen dimensions
WIDTH = 800
HEIGHT = 600
STATUS_BAR_HEIGHT = 100
PLAY_AREA_HEIGHT = HEIGHT - STATUS_BAR_HEIGHT

# Physics constants
GRAVITY = 0.45
JUMP_VELOCITY = -10
BASE_MOVE_SPEED = 6
SPEED_BOOST_MULTIPLIER = 1.25
INVINCIBILITY_DURATION = 2000  # milliseconds
IMMOBILIZED_DURATION = 1000
MAX_BACKTRACK_DISTANCE = 1000  # How far left the player can go from their furthest right position

# Difficulty scaling constants
DIFFICULTY_START_DISTANCE = 1000  # Distance at which difficulty starts increasing
DIFFICULTY_MAX_DISTANCE = 20000   # Distance at which difficulty reaches maximum
BASE_OBSTACLE_SIZE = 25           # Base size of obstacles
MAX_OBSTACLE_CHANCE = 0.9         # Maximum chance of obstacles at highest difficulty
MAX_PIT_CHANCE = 0.5              # Maximum chance of pits at highest difficulty
MIN_PIT_WIDTH = 200               # Minimum pit width at lowest difficulty
MAX_PIT_WIDTH = 500               # Maximum pit width at highest difficulty
MIN_PLATFORM_CHANCE = 0.8         # Minimum chance of platforms over pits at highest difficulty

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GREY = (64, 64, 64)
RED = (220, 60, 60)        # Softer red for player
DARK_RED = (180, 0, 0)     # Darker red for damage invincibility
GREEN = (76, 187, 23)      # Vibrant green for floors/platforms
YELLOW = (255, 215, 0)     # Gold for coins
BLUE = (30, 144, 255)      # Dodger blue for speed power-up
CYAN = (0, 191, 255)       # Deep sky blue for flying power-up
MAGENTA = (218, 112, 214)  # Orchid for other power-ups
GRAY = (128, 128, 128)     # Medium gray
ORANGE = (255, 140, 0)     # Dark orange for obstacles
PURPLE = (147, 112, 219)   # Medium purple for invincibility flashing
LIGHT_BLUE = (173, 216, 230) # Light blue for background

# Game states
GAME_RUNNING = 0
GAME_LOST_MESSAGE = 1
GAME_OVER = 2 