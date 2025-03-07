# Dasher

A 2D side-scrolling platformer game built with Pygame where you run, jump, and dash through an endless procedurally generated world.

## Game Overview

In Dasher, you control a character that must navigate through an endless world filled with:
- Platforms to jump on
- Obstacles to avoid
- Pits to cross
- Coins to collect
- Power-ups to enhance your abilities

The game features progressive difficulty - the further you go, the more challenging the obstacles and terrain become.

## Controls

- **Left/Right Arrow Keys**: Move left/right
- **Space**: Jump
- **Down Arrow**: Drop through platforms
- **S Key**: Dash (when power-up is active)

## Game Features

- **Procedurally Generated World**: Every playthrough is unique with randomly generated terrain
- **Power-ups**:
  - Speed boost
  - Invincibility
  - Jump boost
  - And more!
- **Lives System**: Collect coins to earn extra lives
- **Difficulty Scaling**: The game gets progressively harder the further you go

## Requirements

- Python 3.x
- Pygame

## Installation

1. Ensure you have Python installed on your system
2. Install Pygame:
```
pip install pygame
```
3. Clone or download this repository
4. Run the game:
```
python main.py
```

## Game Mechanics

- **Collision Detection**: Precise collision handling for platforms, obstacles, and collectibles
- **Camera System**: Dynamic camera that follows the player
- **Invincibility**: Temporary protection after taking damage
- **Score System**: Based on distance traveled and coins collected

## Development

This game was developed using:
- Python
- Pygame for rendering and game logic

## Future Enhancements

- Additional power-ups and obstacles
- Different character skins
- High score leaderboard
- Background music and improved sound effects
- More varied environments