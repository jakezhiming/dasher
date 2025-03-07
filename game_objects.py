import pygame
from constants import (
    BROWN, GREEN, YELLOW, BLUE, CYAN, MAGENTA, RED,
    PLAY_AREA_HEIGHT
)

class Floor:
    def __init__(self, x, width):
        self.x = x
        self.width = width
        self.height = 20
        self.y = PLAY_AREA_HEIGHT - self.height

    def draw(self, screen, camera_x):
        pygame.draw.rect(screen, BROWN, (self.x - camera_x, self.y, self.width, self.height))

class Platform:
    def __init__(self, x, y, width):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20

    def draw(self, screen, camera_x):
        pygame.draw.rect(screen, BROWN, (self.x - camera_x, self.y, self.width, self.height))

class Obstacle:
    def __init__(self, x, y, width=30, height=30):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, screen, camera_x):
        pygame.draw.rect(screen, GREEN, (self.x - camera_x, self.y, self.width, self.height))

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20

    def draw(self, screen, camera_x):
        pygame.draw.circle(screen, YELLOW, (int(self.x - camera_x + 10), int(self.y + 10)), 10)

class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.radius = 10  # Changed from width/height to radius
        self.type = type
        # Keep width and height properties for existing collision detection
        self.width = self.radius * 2
        self.height = self.radius * 2
        # Update center coordinates
        self.update_center()
        
    def update_center(self):
        # Calculate center coordinates based on top-left position
        self.center_x = self.x + self.radius
        self.center_y = self.y + self.radius

    def draw(self, screen, camera_x):
        if self.type == 'speed':
            color = BLUE
        elif self.type == 'flying':
            color = CYAN
        elif self.type == 'invincibility':
            color = MAGENTA
        elif self.type == 'life':
            color = RED
        else:
            color = MAGENTA
            
        # Draw a circle instead of a rectangle
        pygame.draw.circle(screen, color, (self.center_x - camera_x, self.center_y), self.radius) 