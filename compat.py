"""
Compatibility layer for handling different pygame versions.
This module provides a unified interface for both pygame and pygame_ce, and
handles dotenv imports in both desktop and web environments.
"""

import os
from logger import get_module_logger

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


__all__ = ['load_dotenv'] 
__all__ = ['pygame'] 