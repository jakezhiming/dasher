# ===== PATHS =====
FONT_PATH = "assets/fonts/press-start-2p.ttf"
HEART_SPRITE_PATH = "assets/images/stats/heart pixel art 32x32.png"

# ===== SCREEN DIMENSIONS =====
WIDTH = 800
HEIGHT = 600
STATUS_BAR_HEIGHT = 100
PLAY_AREA_HEIGHT = HEIGHT - STATUS_BAR_HEIGHT

# ===== PLAYER CONSTANTS =====
# Player dimensions
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 50
PLAYER_INITIAL_X = 100
PLAYER_INITIAL_Y = PLAY_AREA_HEIGHT - PLAYER_HEIGHT - 20

# Player physics
GRAVITY = 0.45
FLYING_GRAVITY_REDUCTION = 0.66  # Flying reduces gravity by 33%
JUMP_VELOCITY = -10
BASE_MOVE_SPEED = 6
SPEED_BOOST_MULTIPLIER = 1.25
SPEED_BOOST_DURATION = 5000  # ms - how long the speed boost lasts

# Player states
INITIAL_LIVES = 3
HURT_ANIMATION_DURATION = 500  # ms
DEATH_ANIMATION_DURATION = 1500  # ms

# Invincibility
INVINCIBILITY_FROM_DAMAGE_DURATION = 2000  # ms
INVINCIBILITY_DURATION = 5000  # ms
IMMOBILIZED_DURATION = 1000  # ms
MAX_BACKTRACK_DISTANCE = 1000  # How far left the player can go from their furthest right position

# ===== CAMERA CONSTANTS =====
CAMERA_RIGHT_BOUNDARY_FACTOR = 0.5  # Player position at 50% of screen width when moving right
CAMERA_LEFT_BOUNDARY_FACTOR = 0.3   # Player position at 30% of screen width when moving left

# ===== DIFFICULTY SCALING =====
DIFFICULTY_START_DISTANCE = 1000  # Distance at which difficulty starts increasing
DIFFICULTY_MAX_DISTANCE = 20000   # Distance at which difficulty reaches maximum
BASE_OBSTACLE_CHANCE = 0.5        # Base chance of obstacles at lowest difficulty
MAX_OBSTACLE_CHANCE = 0.9         # Maximum chance of obstacles at highest difficulty
BASE_PIT_CHANCE = 0.2             # Base chance of pits at lowest difficulty
MAX_PIT_CHANCE = 0.5              # Maximum chance of pits at highest difficulty
MIN_PIT_WIDTH = 200               # Minimum pit width at lowest difficulty
MAX_PIT_WIDTH = 500               # Maximum pit width at highest difficulty
BASE_POWERUP_CHANCE = 0.05        # Base chance of power-ups at lowest difficulty

# ===== LEVEL GENERATION =====
SEGMENT_LENGTH_MULTIPLIER = 3     # Generate segments 3x the screen width
GRID_CELL_SIZE = 100              # Size of collision grid cells
OBSTACLE_BUFFER = 10              # Buffer around obstacles for collision detection
MIN_PLATFORM_WIDTH = 50           # Minimum width for platforms
MAX_PLATFORM_WIDTH = 150          # Maximum width for platforms
PLATFORM_EDGE_BUFFER = 60         # Buffer from edge of pit (per side)

# ===== GAME OBJECT DIMENSIONS =====
FLOOR_HEIGHT = 20
COIN_SIZE = 20
POWERUP_SIZE = 20
DEFAULT_OBSTACLE_SIZE = 30

# ===== UI CONSTANTS =====
HEART_SPRITE_SIZE = 32
MESSAGE_CHAR_DELAY = 5            # ms between characters in scrolling text
DEFAULT_MESSAGE_DELAY = 5000      # ms between default messages
WELCOME_MESSAGE = "Welcome to Dasher! Use arrow keys to move and SPACE to jump."
CONTROLS_MESSAGE = "Press 'D' to toggle debug info."
CONTROLS_MESSAGE_DELAY = 3000     # ms delay before showing controls message

# ===== ANIMATION CONSTANTS =====
PLAYER_ANIMATION_SPEED = 0.2      # Frames per second
DEATH_ANIMATION_FRAME_DELAY = 150 # ms between death animation frames
SPEED_BOOST_ANIMATION_FACTOR = 0.6 # Speed boost makes animation 40% faster

# ===== COLORS =====
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GREY = (64, 64, 64)
RED = (220, 60, 60)        # Softer red for player
DARK_RED = (180, 0, 0)     # Darker red for damage invincibility
GREEN = (0, 100, 0)        # Dark green for obstacles
YELLOW = (255, 215, 0)     # Gold for coins
BLUE = (20, 120, 230)      # Dodger blue for background text and speed power-up
CYAN = (0, 191, 255)       # Deep sky blue for flying power-up
MAGENTA = (218, 112, 214)  # Orchid for other power-ups
GRAY = (128, 128, 128)     # Medium gray
PURPLE = (147, 112, 219)   # Medium purple for invincibility flashing
LIGHT_BLUE = (135, 206, 255) # Light blue
BROWN = (139, 69, 19)      # Brown for floor and platforms
WHITE_OVERLAY = (255, 255, 255, 128)  # Semi-transparent white for flashing effects

# ===== GAME STATES =====
GAME_RUNNING = 0
GAME_LOST_MESSAGE = 1
GAME_OVER = 2
GAME_OVER_DISPLAY_DURATION = 3000  # ms to display game over screen 