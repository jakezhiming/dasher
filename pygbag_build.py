#!/usr/bin/env python3
"""
Pygbag build script for Dasher game.

This script helps build and package the Dasher game for web deployment using Pygbag.

Usage:
    python pygbag_build.py [--proxy-url URL]

Requirements:
    - pygbag: pip install pygbag
"""

import sys
import os
import subprocess
import argparse
import shutil

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
        f.write("# Note: For security reasons, API keys are not included in web version\n")
        
        # If proxy URL is provided, include it
        if proxy_url:
            f.write(f"OPENAI_PROXY_URL={proxy_url}\n")
            print(f"Configured to use proxy server at: {proxy_url}")
        else:
            f.write("# No proxy URL provided\n")
            print("WARNING: No proxy URL provided - LLM features will be disabled in web version")
    
    # Also create a web_config.js file with the proxy URL
    with open("web_config.js", "w") as f:
        f.write("// Web configuration\n")
        f.write("window.ENV = window.ENV || {};\n")
        f.write("// Note: For security reasons, API keys are not included in web version\n")
        
        if proxy_url:
            f.write(f'window.ENV.OPENAI_PROXY_URL = "{proxy_url}";\n')
            f.write('console.log("Proxy URL configured:", window.ENV.OPENAI_PROXY_URL);\n')
        else:
            f.write("// No proxy URL provided\n")
            f.write('console.log("WARNING: No proxy URL configured - LLM features will be disabled");\n')
    
    print("Created web-compatible .env file and web_config.js")

def build_with_pygbag():
    """Build the game with pygbag."""
    print("Building game with pygbag...")
    
    # Ensure .env.web is in the root directory for pygbag to include it
    if not os.path.exists(".env.web"):
        print("Warning: .env.web file not found in root directory")
    else:
        print("Found .env.web file in root directory")
    
    # Run pygbag on the main.py file
    cmd = [sys.executable, "-m", "pygbag", "--build", "main.py"]
    
    try:
        subprocess.run(cmd, check=True)
        print("\nBuild completed successfully!")
        
        # Copy the .env.web file to the build directory
        if os.path.exists(".env.web"):
            print("Copying .env.web to build/web directory...")
            shutil.copy(".env.web", "build/web/.env.web")
            print("Copied .env.web file to build directory")
            
            # Also create a JavaScript file to set environment variables
            print("Creating environment.js file...")
            with open(".env.web", "r") as env_file:
                env_content = env_file.readlines()
            
            with open("build/web/environment.js", "w") as js_file:
                js_file.write("// Environment variables for web version\n")
                js_file.write("window.ENV = {};\n")
                
                for line in env_content:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        js_file.write(f'window.ENV["{key}"] = "{value}";\n')
                
                js_file.write('console.log("Environment variables loaded:", window.ENV);\n')
            
            # Modify the index.html file to include the environment.js script
            index_html_path = "build/web/index.html"
            if os.path.exists(index_html_path):
                with open(index_html_path, "r") as f:
                    html_content = f.read()
                
                # Add the script tag before the closing </head> tag
                if "</head>" in html_content:
                    html_content = html_content.replace("</head>", '<script src="environment.js"></script></head>')
                    
                    with open(index_html_path, "w") as f:
                        f.write(html_content)
                    
                    print("Added environment.js script to index.html")
                else:
                    print("Could not find </head> tag in index.html")
            else:
                print(f"Could not find {index_html_path}")
        else:
            print(".env.web file not found")
        
        # Copy the web_config.js file to the build directory
        if os.path.exists("web_config.js"):
            print("Copying web_config.js to build/web directory...")
            shutil.copy("web_config.js", "build/web/web_config.js")
            
            # Modify the index.html file to include the web_config.js script
            index_html_path = "build/web/index.html"
            if os.path.exists(index_html_path):
                with open(index_html_path, "r") as f:
                    html_content = f.read()
                
                # Add the script tag before the closing </head> tag
                if "</head>" in html_content:
                    html_content = html_content.replace("</head>", '<script src="web_config.js"></script></head>')
                    
                    with open(index_html_path, "w") as f:
                        f.write(html_content)
                    
                    print("Added web_config.js script to index.html")
            
            print("Copied web_config.js file to build directory")
        else:
            print("web_config.js file not found")
        
        # Copy the web_api.js file to the build directory
        if os.path.exists("web_api.js"):
            print("Copying web_api.js to build/web directory...")
            shutil.copy("web_api.js", "build/web/web_api.js")
            
            # Modify the index.html file to include the web_api.js script
            index_html_path = "build/web/index.html"
            if os.path.exists(index_html_path):
                with open(index_html_path, "r") as f:
                    html_content = f.read()
                
                # Add the script tag before the closing </head> tag
                if "</head>" in html_content:
                    html_content = html_content.replace("</head>", '<script src="web_api.js"></script></head>')
                    
                    with open(index_html_path, "w") as f:
                        f.write(html_content)
                    
                    print("Added web_api.js script to index.html")
                else:
                    print("Could not find </head> tag in index.html")
            else:
                print(f"Could not find {index_html_path}")
        else:
            print("web_api.js file not found")
        
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
        print("To test locally, run:")
        print("  1. python -m http.server --directory build/web")
        print("  2. Open your browser and go to: http://localhost:8000")
        
        if not args.proxy_url:
            print("\nNOTE: You didn't specify a proxy server URL.")
            print("OpenAI API calls may fail due to CORS issues.")
            print("To use a proxy server, run:")
            print("  1. python proxy_server.py  # In a separate terminal")
            print("  2. python pygbag_build.py --proxy-url http://localhost:5000/api/openai")
            print("  3. python -m http.server --directory build/web")

if __name__ == "__main__":
    main() 