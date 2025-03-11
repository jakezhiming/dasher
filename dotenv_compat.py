"""
Dotenv compatibility layer for handling dotenv imports in both desktop and web environments.
"""

import os
from pygame_compat import is_web_environment

# Define a fallback load_dotenv function in case the real one isn't available
def fallback_load_dotenv(dotenv_path=None, stream=None, verbose=False, override=False):
    """
    Fallback implementation of load_dotenv that does nothing but log a message.
    Used when python-dotenv is not available.
    """
    print("Warning: python-dotenv not available, using fallback implementation")
    return False

# Try to import the real load_dotenv function
try:
    try:
        # Try the standard import first
        from dotenv import load_dotenv
        print("Successfully imported dotenv")
    except ImportError:
        # If that fails, try the python-dotenv import
        from python_dotenv import load_dotenv
        print("Successfully imported python-dotenv")
except ImportError:
    # If both fail, use the fallback
    load_dotenv = fallback_load_dotenv
    print("Using fallback dotenv implementation")

# Export the load_dotenv function
__all__ = ['load_dotenv'] 