"""
Compatibility layer for handling different pygame versions.
This module provides a unified interface for both pygame and pygame_ce, and
handles dotenv imports in both desktop and web environments.
"""

import os
from logger import get_module_logger
import random
import sys

logger = get_module_logger('compat')

# Check if we're running in a web environment (Pygbag)
def is_web_environment():
    """Check if running in a web environment (Pygbag)."""
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

# In web environment, use the built-in pygame
# In desktop environment, use pygame_ce
if is_web_environment():
    try:
        import pygame
        logger.info("Using built-in pygame in web environment")
    except ImportError:
        logger.info("Failed to import pygame in web environment")
        raise
else:
    try:
        import pygame_ce as pygame
        logger.info("Using pygame_ce in desktop environment")
    except ImportError:
        try:
            import pygame
            logger.info("Falling back to regular pygame in desktop environment")
        except ImportError:
            logger.info("Failed to import any pygame version")
            raise

def fallback_load_dotenv(dotenv_path=None, stream=None, verbose=False, override=False):
    """
    Fallback implementation of load_dotenv that does nothing but log a message.
    Used when python-dotenv is not available.
    """
    logger.info("Warning: python-dotenv not available, using fallback implementation")
    return False

# Try to import the real load_dotenv function
try:
    try:
        # Try the standard import first
        from dotenv import load_dotenv
        logger.info("Successfully imported dotenv")
    except ImportError:
        # If that fails, try the python-dotenv import
        from python_dotenv import load_dotenv
        logger.info("Successfully imported python-dotenv")
except ImportError:
    # If both fail, use the fallback
    load_dotenv = fallback_load_dotenv
    logger.info("Using fallback dotenv implementation")

# Check if we're running in a browser environment (via pygbag)
IS_WEB = sys.platform == 'emscripten'

# If we're in a web environment, set up browser-specific random functions
if IS_WEB:
    import js
    
    # Create a wrapper for the browser's crypto.getRandomValues
    class WebRandom:
        """Random number generator that uses the browser's crypto API when in web mode."""
        
        def __init__(self):
            self.original_random = random
            
        def random(self):
            """Return a random float in [0.0, 1.0)."""
            try:
                # Use the browser's crypto API via our web_api.js
                return js.window.DASHER_WEB_API.getRandomNumber()
            except Exception as e:
                logger.error(f"Error using web random: {e}, falling back to Python random")
                return self.original_random.random()
        
        def uniform(self, a, b):
            """Return a random float in [a, b)."""
            return a + (b - a) * self.random()
        
        def randint(self, a, b):
            """Return a random integer in [a, b]."""
            return int(self.uniform(a, b + 1))
        
        def choice(self, seq):
            """Return a random element from seq."""
            return seq[self.randint(0, len(seq) - 1)]
        
        def choices(self, population, weights=None, *, cum_weights=None, k=1):
            """Return k-sized list of elements chosen from population with replacement.
            
            If weights is specified, selections are made according to the relative weights.
            """
            if weights is None and cum_weights is None:
                # Simple case: uniform selection
                return [self.choice(population) for _ in range(k)]
            
            # Handle weighted selection
            if cum_weights is None:
                # Convert weights to cumulative weights
                cum_weights = []
                total = 0
                for w in weights:
                    total += w
                    cum_weights.append(total)
            else:
                total = cum_weights[-1]
            
            # Select k items
            result = []
            for _ in range(k):
                r = self.uniform(0, total)
                for i, cw in enumerate(cum_weights):
                    if r <= cw:
                        result.append(population[i])
                        break
            
            return result
    
    # Replace the standard random module functions with our web-compatible versions
    web_random = WebRandom()
    random.random = web_random.random
    random.uniform = web_random.uniform
    random.randint = web_random.randint
    random.choice = web_random.choice
    random.choices = web_random.choices
    
    logger.info("Using web-compatible random number generator")
else:
    logger.info("Using standard Python random number generator")

__all__ = ['load_dotenv', 'pygame', 'is_web_environment', 'IS_WEB', 'random'] 