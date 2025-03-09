import pygame
import math
import random
from constants import WIDTH, HEIGHT

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
    def __init__(self, x, y, color, particle_count=20, lifetime=1.0, size_range=(2, 5), speed_range=(50, 150)):
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
            
            self.particles.append({
                'x': self.x,
                'y': self.y,
                'vx': vx,
                'vy': vy,
                'size': size,
                'fade_rate': fade_rate,
                'alpha': 255
            })
    
    def update(self, dt):
        super().update(dt)
        
        # Update each particle
        for p in self.particles:
            # Update position
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            
            # Apply gravity
            p['vy'] += 200 * dt  # Gravity effect
            
            # Fade out
            p['alpha'] -= p['fade_rate'] * 255 * dt / self.lifetime
            if p['alpha'] < 0:
                p['alpha'] = 0
    
    def draw(self, screen, camera_x):
        for p in self.particles:
            # Skip if fully transparent
            if p['alpha'] <= 0:
                continue
                
            # Create a surface for the particle with alpha
            particle_surface = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            
            # Draw the particle with alpha
            pygame.draw.circle(
                particle_surface, 
                (*self.color, int(p['alpha'])), 
                (p['size'], p['size']), 
                p['size']
            )
            
            # Draw on screen
            screen.blit(
                particle_surface, 
                (int(p['x'] - p['size'] - camera_x), int(p['y'] - p['size']))
            )

class TextPopup(CollectionEffect):
    """Text popup effect for showing points or power-up name"""
    def __init__(self, x, y, text, color, lifetime=1.0, size=20, rise_speed=50):
        super().__init__(x, y, color, lifetime)
        self.text = text
        self.size = size
        self.rise_speed = rise_speed
        self.font = pygame.font.SysFont('Arial', size, bold=True)
        
    def update(self, dt):
        super().update(dt)
        # Move text upward
        self.y -= self.rise_speed * dt
        
    def draw(self, screen, camera_x):
        # Calculate alpha based on lifetime
        alpha = 255
        if self.age > self.lifetime * 0.7:  # Start fading after 70% of lifetime
            fade_percent = (self.age - (self.lifetime * 0.7)) / (self.lifetime * 0.3)
            alpha = 255 * (1 - fade_percent)
        
        # Render text with alpha
        text_surface = self.font.render(self.text, True, self.color)
        text_surface.set_alpha(max(0, min(255, alpha)))
        
        # Calculate position
        text_rect = text_surface.get_rect(center=(int(self.x - camera_x), int(self.y)))
        
        # Draw on screen
        screen.blit(text_surface, text_rect)

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
                2  # Line thickness
            )
        
        # Draw on screen
        screen.blit(
            shine_surface, 
            (int(self.x - size // 2 - camera_x), int(self.y - size // 2))
        )

# Collection effect manager
class CollectionEffectManager:
    def __init__(self):
        self.effects = []
        
        # Define colors for different effects
        self.coin_color = (255, 215, 0)  # Gold
        self.powerup_colors = {
            'speed': (30, 144, 255),      # Blue
            'flying': (0, 200, 255),      # Cyan
            'invincibility': (255, 50, 255),  # Magenta
            'life': (255, 60, 60)         # Red
        }
    
    def create_coin_effect(self, x, y):
        """Create effects for coin collection"""
        # Particle explosion with reduced lifetime and range
        self.effects.append(ParticleEffect(
            x + 16, y + 16,  # Center of the coin
            self.coin_color,
            particle_count=10,  # Reduced from 15
            lifetime=0.4,      # Reduced from 0.8
            size_range=(1, 3), # Reduced from (2, 4)
            speed_range=(30, 100) # Reduced from (50, 150)
        ))
        
        # Shine effect with reduced lifetime and size
        self.effects.append(ShineEffect(
            x + 16, y + 16,  # Center of the coin
            self.coin_color,
            lifetime=0.3,    # Reduced from 0.5
            max_radius=20    # Reduced from 30
        ))
        
        # Removed text popup
    
    def create_powerup_effect(self, x, y, powerup_type):
        """Create effects for powerup collection"""
        color = self.powerup_colors.get(powerup_type, (255, 255, 255))
        
        # Particle explosion with reduced lifetime and range
        self.effects.append(ParticleEffect(
            x + 16, y + 16,  # Center of the powerup
            color,
            particle_count=15,  # Reduced from 25
            lifetime=0.5,       # Reduced from 1.0
            size_range=(2, 4),  # Reduced from (3, 6)
            speed_range=(40, 120) # Reduced from (50, 150)
        ))
        
        # Shine effect with reduced lifetime and size
        self.effects.append(ShineEffect(
            x + 16, y + 16,  # Center of the powerup
            color,
            lifetime=0.4,    # Reduced from 0.7
            max_radius=30    # Reduced from 50
        ))
        
        # Removed text popup
    
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