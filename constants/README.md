# Constants Package

This package contains all the constants used in the Dasher game, organized into modules by category.

## Structure

- `__init__.py` - Package initialization
- `paths.py` - File and asset path constants
- `screen.py` - Screen dimension constants
- `player.py` - Player-related constants (dimensions, physics, states)
- `camera.py` - Camera behavior constants
- `difficulty.py` - Difficulty scaling constants
- `level_generation.py` - Level generation constants
- `game_objects.py` - Game object dimension constants
- `ui.py` - UI-related constants
- `animation.py` - Animation-related constants
- `colors.py` - Color constants
- `game_states.py` - Game state constants

## Usage

Import only the constants you need from the specific modules:

```python
from constants.player import PLAYER_WIDTH, GRAVITY
from constants.colors import RED
```

This approach:
1. Makes imports more explicit and easier to understand
2. Reduces import overhead
3. Avoids circular import issues
4. Makes it clearer which constants are related to which aspects of the game 