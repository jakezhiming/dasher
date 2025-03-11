"""
Pygame compatibility layer for handling different pygame versions.
This module provides a unified interface for both pygame and pygame_ce.
"""

import sys
import os

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
        print("Using built-in pygame in web environment")
    except ImportError:
        print("Failed to import pygame in web environment")
        raise
else:
    try:
        import pygame_ce as pygame
        print("Using pygame_ce in desktop environment")
    except ImportError:
        try:
            import pygame
            print("Falling back to regular pygame in desktop environment")
        except ImportError:
            print("Failed to import any pygame version")
            raise

# Export the pygame module
__all__ = ['pygame'] 