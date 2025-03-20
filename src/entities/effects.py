from src.utils.compat import random
import pygame
import math
from src.constants.colors import BLUE, MAGENTA, CYAN, GOLD, RED, WHITE
from src.utils.logger import get_module_logger

logger = get_module_logger("effects")


class CollectionEffect:
    """Base class for collection effects when player collects items"""

    def __init__(self, x, y, color, lifetime=1.0):
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = lifetime  # Effect duration in seconds
        self.age = 0  # Current age of the effect
        self.active = True

    def update(self, dt):
        self.age += dt
        if self.age >= self.lifetime:
            self.active = False

    def draw(self, screen, camera_x):
        pass  # Implemented by subclasses


class ParticleEffect(CollectionEffect):
    """Particle explosion effect for collecting items"""

    def __init__(
        self,
        x,
        y,
        color,
        particle_count=20,
        lifetime=1.0,
        size_range=(2, 5),
        speed_range=(50, 150),
    ):
        super().__init__(x, y, color, lifetime)
        self.particles = []

        # Create particles
        for _ in range(particle_count):
            # Random angle and speed
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(speed_range[0], speed_range[1])

            # Calculate velocity components
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Random size and fade rate
            size = random.uniform(size_range[0], size_range[1])
            fade_rate = random.uniform(0.5, 1.0)

            self.particles.append(
                {
                    "x": self.x,
                    "y": self.y,
                    "vx": vx,
                    "vy": vy,
                    "size": size,
                    "fade_rate": fade_rate,
                    "alpha": 255,
                }
            )

    def update(self, dt):
        super().update(dt)

        # Update each particle
        for p in self.particles:
            # Update position
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt

            # Apply gravity
            p["vy"] += 200 * dt  # Gravity effect

            # Fade out
            p["alpha"] -= p["fade_rate"] * 255 * dt / self.lifetime
            if p["alpha"] < 0:
                p["alpha"] = 0

    def draw(self, screen, camera_x):
        for p in self.particles:
            # Skip if fully transparent
            if p["alpha"] <= 0:
                continue

            # Create a surface for the particle with alpha
            particle_surface = pygame.Surface(
                (p["size"] * 2, p["size"] * 2), pygame.SRCALPHA
            )

            # Draw the particle with alpha
            pygame.draw.circle(
                particle_surface,
                (*self.color, int(p["alpha"])),
                (p["size"], p["size"]),
                p["size"],
            )

            # Draw on screen
            screen.blit(
                particle_surface,
                (int(p["x"] - p["size"] - camera_x), int(p["y"] - p["size"])),
            )


class ShineEffect(CollectionEffect):
    """Radial shine effect for collecting items"""

    def __init__(self, x, y, color, lifetime=0.5, max_radius=50):
        super().__init__(x, y, color, lifetime)
        self.max_radius = max_radius

    def update(self, dt):
        super().update(dt)

    def draw(self, screen, camera_x):
        # Calculate current radius based on age
        progress = self.age / self.lifetime
        radius = self.max_radius * progress

        # Calculate alpha (fade out)
        alpha = 255 * (1 - progress)

        # Create a surface for the shine with alpha
        size = int(self.max_radius * 2)
        shine_surface = pygame.Surface((size, size), pygame.SRCALPHA)

        # Draw concentric circles with decreasing alpha
        for r in range(int(radius), 0, -2):
            circle_alpha = int(alpha * (1 - r / radius))
            if circle_alpha <= 0:
                continue

            pygame.draw.circle(
                shine_surface,
                (*self.color, circle_alpha),
                (size // 2, size // 2),
                r,
                2,  # Line thickness
            )

        # Draw on screen
        screen.blit(
            shine_surface, (int(self.x - size // 2 - camera_x), int(self.y - size // 2))
        )


class ParticleTrailEffect(CollectionEffect):
    """Speed trail particles that follow behind the player"""

    def __init__(
        self,
        x,
        y,
        color,
        lifetime=0.3,
        size_range=(1, 3),
        speed_range=(20, 60),
        continuous=True,
    ):
        super().__init__(x, y, color, lifetime)
        self.particles = []
        self.size_range = size_range
        self.speed_range = speed_range
        self.continuous = continuous  # Whether to continuously emit particles
        self.emission_timer = 0  # Timer for particle emission
        self.emission_interval = 0.05  # Time between particle emissions

        # Create initial particles
        self._create_particles(5)

    def _create_particles(self, count):
        """Create a batch of particles"""
        for _ in range(count):
            size = random.uniform(self.size_range[0], self.size_range[1])
            speed = random.uniform(self.speed_range[0], self.speed_range[1])
            angle = random.uniform(0, 2 * math.pi)  # Random direction

            # Calculate velocity components
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            # Add some upward bias to the particles
            vy -= random.uniform(10, 30)

            # Create particle
            self.particles.append(
                {
                    "x": self.x,
                    "y": self.y,
                    "vx": vx,
                    "vy": vy,
                    "size": size,
                    "alpha": 255,
                }
            )

    def update(self, dt):
        super().update(dt)

        # If continuous, emit new particles periodically
        if self.continuous:
            self.emission_timer += dt
            if self.emission_timer >= self.emission_interval:
                self._create_particles(1)  # Create one new particle
                self.emission_timer = 0

        # Update each particle
        for particle in self.particles:
            # Update position
            particle["x"] += particle["vx"] * dt
            particle["y"] += particle["vy"] * dt

            # Apply gravity
            particle["vy"] += 50 * dt

            # Fade out based on lifetime
            fade_factor = 1 - (self.age / self.lifetime)
            particle["alpha"] = 255 * fade_factor

    def draw(self, screen, camera_x):
        # Draw each particle
        for particle in self.particles:
            # Skip if fully transparent
            if particle["alpha"] <= 0:
                continue

            # Calculate screen position
            screen_x = int(particle["x"] - camera_x)
            screen_y = int(particle["y"])

            # Create surface for the particle
            size = int(particle["size"])
            if size < 1:
                continue

            particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

            # Draw the particle
            alpha = min(255, max(0, int(particle["alpha"])))
            pygame.draw.circle(
                particle_surface, (*self.color, alpha), (size, size), size
            )

            # Draw on screen
            screen.blit(particle_surface, (screen_x - size, screen_y - size))


# Collection effect manager
class CollectionEffectManager:
    def __init__(self):
        self.effects = []

        # Define colors for different effects
        self.coin_color = GOLD
        self.powerup_colors = {
            "speed": BLUE,
            "flying": CYAN,
            "invincibility": MAGENTA,
            "life": RED,
        }

    def create_coin_effect(self, x, y):
        """Create effects for coin collection"""
        # Particle explosion with reduced lifetime and range
        self.effects.append(
            ParticleEffect(
                x + 16,
                y + 16,  # Center of the coin
                self.coin_color,
                particle_count=10,  # Reduced from 15
                lifetime=0.4,  # Reduced from 0.8
                size_range=(1, 3),  # Reduced from (2, 4)
                speed_range=(30, 100),  # Reduced from (50, 150)
            )
        )

        # Shine effect with reduced lifetime and size
        self.effects.append(
            ShineEffect(
                x + 16,
                y + 16,  # Center of the coin
                self.coin_color,
                lifetime=0.3,  # Reduced from 0.5
                max_radius=20,  # Reduced from 30
            )
        )

        # Removed text popup

    def create_powerup_effect(self, x, y, powerup_type):
        """Create effects for powerup collection"""
        color = self.powerup_colors.get(powerup_type, WHITE)

        # Particle explosion with reduced lifetime and range
        self.effects.append(
            ParticleEffect(
                x + 16,
                y + 16,  # Center of the powerup
                color,
                particle_count=15,  # Reduced from 25
                lifetime=0.5,  # Reduced from 1.0
                size_range=(2, 4),  # Reduced from (3, 6)
                speed_range=(40, 120),  # Reduced from (50, 150)
            )
        )

        # Shine effect with reduced lifetime and size
        self.effects.append(
            ShineEffect(
                x + 16,
                y + 16,  # Center of the powerup
                color,
                lifetime=0.4,  # Reduced from 0.7
                max_radius=30,  # Reduced from 50
            )
        )

        # Removed text popup

    def create_speed_trail(self, x, y):
        """Create speed trail particles at the given position"""
        self.effects.append(
            ParticleTrailEffect(
                x,
                y,
                BLUE,
                lifetime=0.3,
                size_range=(1, 3),
                speed_range=(20, 60),
                continuous=True,  # Ensure continuous emission
            )
        )

    def create_invincibility_trail(self, x, y):
        """Create invincibility trail particles at the given position"""
        self.effects.append(
            ParticleTrailEffect(
                x,
                y,
                MAGENTA,
                lifetime=0.3,
                size_range=(1, 3),
                speed_range=(20, 60),
                continuous=True,  # Ensure continuous emission
            )
        )

    def create_flying_trail(self, x, y):
        """Create flying trail particles at the given position"""
        self.effects.append(
            ParticleTrailEffect(
                x,
                y,
                CYAN,
                lifetime=0.3,
                size_range=(1, 3),
                speed_range=(20, 60),
                continuous=True,  # Ensure continuous emission
            )
        )

    def update(self, dt):
        """Update all active effects"""
        # Update effects and remove inactive ones
        self.effects = [effect for effect in self.effects if effect.active]

        for effect in self.effects:
            effect.update(dt)

    def draw(self, screen, camera_x):
        """Draw all active effects"""
        for effect in self.effects:
            effect.draw(screen, camera_x)


# Global instance
effect_manager = CollectionEffectManager()
