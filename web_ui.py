from compat import pygame
import os

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