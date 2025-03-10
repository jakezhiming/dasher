"""Difficulty scaling constants for the Dasher game."""

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
MAX_SPIKES = 5
MAX_FIRES = 5
MAX_SAW_SIZE = 120