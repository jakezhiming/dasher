from pygame_compat import pygame
import os

class ApiKeyInput:
    """Input field for API key in web environment."""
    
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.active = False
        self.color = pygame.Color('lightskyblue3')
        self.font = pygame.font.SysFont(None, 24)
        self.saved = False
        self.testing = False
        
    def handle_event(self, event):
        """Handle keyboard events for text input."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle active state
            self.active = self.rect.collidepoint(event.pos)
            self.color = pygame.Color('dodgerblue2') if self.active else pygame.Color('lightskyblue3')
            return True
            
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                # Save API key
                self.saved = True
                self.testing = True
                self.active = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < 50:  # Limit length
                    self.text += event.unicode
            return True
            
        return False
    
    async def _test_api_key(self):
        """Test if the API key works."""
        # Simulate API test (in a real implementation, this would make an API call)
        self.testing = False
        self.color = pygame.Color('lightgreen')  # Assume success for simplicity
        return True
        
    def draw(self, screen):
        """Draw the input field and text."""
        # Draw rectangle
        pygame.draw.rect(screen, self.color, self.rect, 2)
        
        # Draw text
        text_surface = self.font.render(self.text if len(self.text) == 0 else "*" * len(self.text), True, pygame.Color('white'))
        
        # Draw label
        label = self.font.render("Enter OpenAI API Key:", True, pygame.Color('white'))
        screen.blit(label, (self.rect.x, self.rect.y - 30))
        
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))

        # Draw status if saved
        if self.saved:
            status = "Testing..." if self.testing else "API Key Saved!"
            status_surface = self.font.render(status, True, pygame.Color('green'))
            screen.blit(status_surface, (self.rect.x, self.rect.y + self.rect.height + 10))


def is_web_environment():
    """Check if running in a web environment (Pygbag)."""
    # More robust detection for web environment
    try:
        import platform
        if platform.system() == 'Emscripten':
            return True
    except:
        pass
    
    # Fallback to environment variable checks
    return ('PYODIDE_PACKAGE_ABI' in os.environ or 
            '__PYGBAG__' in os.environ or 
            'EMSCRIPTEN' in os.environ or
            os.path.exists('/.emscripten'))


def load_api_key_from_storage():
    """Load API key from web storage."""
    # In a real implementation, this would use JavaScript interop to access localStorage
    # For simplicity, we'll just return None
    return None