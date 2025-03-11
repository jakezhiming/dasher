#!/usr/bin/env python3
"""
Pygbag build script for Dasher game.

This script helps build and package the Dasher game for web deployment using Pygbag.

Usage:
    python pygbag_build.py [--proxy-url URL]

Requirements:
    - pygbag: pip install pygbag
"""

import os
import sys
import shutil
import subprocess
import argparse

def check_pygbag_installed():
    """Check if pygbag is installed."""
    try:
        import pygbag
        # Pygbag doesn't have a __version__ attribute, so we'll just check if it's importable
        print("Pygbag is installed.")
        return True
    except ImportError:
        print("Pygbag is not installed. Please install it with: pip install pygbag")
        return False

def create_web_version(proxy_url=None):
    """Create a web-compatible version of the game."""
    # Create a .env file for web version
    with open(".env.web", "w") as f:
        f.write("# Web version environment variables\n")
        
        # If proxy URL is provided, include it
        if proxy_url:
            f.write(f"OPENAI_PROXY_URL={proxy_url}\n")
            print(f"Configured to use proxy server at: {proxy_url}")
        else:
            f.write("# No proxy URL provided - OpenAI API calls may fail due to CORS\n")
            f.write("# OPENAI_PROXY_URL=http://your-proxy-server.com/api/openai\n")
        
        # Include empty API key - will be replaced by user in the web interface
        f.write("OPENAI_API_KEY=\n")
    
    print("Created web-compatible .env file")

def build_with_pygbag():
    """Build the game with pygbag."""
    print("Building game with pygbag...")
    
    # Run pygbag on the main.py file
    cmd = [sys.executable, "-m", "pygbag", "main.py"]
    
    try:
        subprocess.run(cmd, check=True)
        print("\nBuild completed successfully!")
        print("\nYou can find the built files in the 'build/web' directory.")
        print("To test locally, run: python -m http.server --directory build/web")
        print("Then open a browser and go to: http://localhost:8000")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        return False
    
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Dasher Pygbag Build Script")
    parser.add_argument("--proxy-url", type=str, help="URL of the OpenAI proxy server")
    args = parser.parse_args()
    
    print("=== Dasher Pygbag Build Script ===")
    
    if not check_pygbag_installed():
        return
    
    create_web_version(args.proxy_url)
    
    if build_with_pygbag():
        print("\nYour game is now ready for web deployment!")
        print("You can upload the contents of the 'build/web' directory to any web server.")
        
        if not args.proxy_url:
            print("\nNOTE: You didn't specify a proxy server URL.")
            print("OpenAI API calls may fail due to CORS issues.")
            print("To use a proxy server, run:")
            print("  1. python proxy_server.py  # In a separate terminal")
            print("  2. python pygbag_build.py --proxy-url http://localhost:5000/api/openai")

if __name__ == "__main__":
    main() 