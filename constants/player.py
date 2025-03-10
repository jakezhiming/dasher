"""Player-related constants for the Dasher game."""

# Import screen constants for player initial position calculation
from constants.screen import PLAY_AREA_HEIGHT

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