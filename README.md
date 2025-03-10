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

## Game Features

- **Procedurally Generated World**: Every playthrough is unique with randomly generated terrain
- **Power-ups**:
  - Speed boost
  - Invincibility
  - Flying
  - Extra life
  - And more!
- **Difficulty Scaling**: The game gets progressively harder the further you go
- **AI-Powered Messages**: Game messages are rephrased by an AI in different personalities (pirate, robot, wizard, etc.) using OpenAI's GPT-4o-mini model

## AI Message System

Dasher features an AI-powered message system that adds personality to the game's status messages. Each time you start the game, a random personality is chosen (pirate, robot, medieval knight, etc.), and all game messages are rephrased in that style.

### Setup

To use the AI message system:

1. Rename `.envexample` to `.env`
2. Add your OpenAI API key to the `.env` file
3. Make sure you have the required dependencies installed (see Installation section)

If no API key is provided, the game will fall back to using the original messages without AI rephrasing.

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