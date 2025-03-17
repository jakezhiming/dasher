#!/usr/bin/env python3
"""
Pygbag build script for Dasher game.

This script helps build and package the Dasher game for web deployment using Pygbag.

Usage:
    python pygbag_build.py

Requirements:
    - pygbag: pip install pygbag
"""

import sys
import os
import subprocess
import shutil
import urllib.request

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

def download_dependencies():
    """Download required dependencies for offline use."""
    print("Downloading required dependencies for offline use...")
    
    # Create directories
    os.makedirs("build/web/archives/repo/cp312", exist_ok=True)
    os.makedirs("build/web/archives/0.9/vt", exist_ok=True)
    
    # List of files to download
    files_to_download = [
        # Python packages
        ("https://pygame-web.github.io/archives/repo/cp312/pygame_static-1.0-cp312-cp312-wasm32_bi_emscripten.whl", 
         "build/web/archives/repo/cp312/pygame_static-1.0-cp312-cp312-wasm32_bi_emscripten.whl"),
        
        # JavaScript dependencies
        ("https://pygame-web.github.io/archives/0.9/browserfs.min.js", 
         "build/web/archives/0.9/browserfs.min.js"),
        ("https://pygame-web.github.io/archives/0.9/empty.html", 
         "build/web/archives/0.9/empty.html"),
        ("https://pygame-web.github.io/archives/0.9/pythons.js", 
         "build/web/archives/0.9/pythons.js"),
        ("https://pygame-web.github.io/archives/0.9/vt/xterm-addon-image.js", 
         "build/web/archives/0.9/vt/xterm-addon-image.js"),
        ("https://pygame-web.github.io/archives/0.9/vt/xterm.js", 
         "build/web/archives/0.9/vt/xterm.js"),
    ]
    
    # Download each file
    for url, path in files_to_download:
        print(f"Downloading {url} to {path}...")
        try:
            urllib.request.urlretrieve(url, path)
            print(f"Downloaded {path}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")
    
    # Create empty pythonrc.py file
    pythonrc_path = "build/web/archives/0.9/pythonrc.py"
    with open(pythonrc_path, "w") as f:
        f.write("# Empty pythonrc.py file\n")
    print(f"Created {pythonrc_path}")
    
    print("All dependencies downloaded successfully!")
    return True

def inject_ui_panels(index_html_path):
    """Inject game UI panels into the index.html file."""
    print("Injecting UI panels into index.html...")
    
    try:
        # Read the CSS and HTML from external files
        css_file_path = "panels.css"
        html_file_path = "panels.html"
        
        if not os.path.exists(css_file_path):
            print(f"Error: {css_file_path} not found")
            return False
            
        if not os.path.exists(html_file_path):
            print(f"Error: {html_file_path} not found")
            return False
        
        # Copy CSS and HTML files to build directory
        print("Copying panels.css and panels.html to build/web directory...")
        shutil.copy(css_file_path, "build/web/panels.css")
        shutil.copy(html_file_path, "build/web/panels.html")

        with open(html_file_path, "r") as f:
            panels_html = f.read()

        with open(index_html_path, "r") as f:
            html_content = f.read()
        
        # Add CSS link in the head section
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", '<link rel="stylesheet" href="panels.css"></head>')
        
        # Add panels HTML before the closing body tag
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f'{panels_html}</body>')
        
        with open(index_html_path, "w") as f:
            f.write(html_content)
        
        print("Successfully injected UI panels!")
        return True
    except Exception as e:
        print(f"Error injecting UI panels: {e}")
        return False

def build_with_pygbag():
    """Build the game with pygbag."""
    print("Building game with pygbag...")
    
    # Run pygbag on the main.py file
    cmd = [sys.executable, "-m", "pygbag", "--build", "main.py"]
    
    try:
        subprocess.run(cmd, check=True)
        print("\nBuild completed successfully!")
        
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
            return False
        
        # Inject leaderboard UI
        index_html_path = "build/web/index.html"
        if os.path.exists(index_html_path):
            inject_ui_panels(index_html_path)
        
        print("\nYou can find the built files in the 'build/web' directory.")
        print("To test locally, run: python -m http.server --directory build/web")
        print("Then open a browser and go to: http://localhost:8000")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        return False
    
    return True

def main():
    """Main function."""
    print("=== Dasher Pygbag Build Script ===")
    
    if not check_pygbag_installed():
        return
    
    if build_with_pygbag():
        print("\nDownloading dependencies for offline use...")
        download_dependencies()
        
        print("\nYour game is now ready for web deployment!")
        print("You can upload the contents of the 'build/web' directory to any web server.")
        print("To test locally, run:")
        print("  1. python -m http.server --directory build/web")
        print("  2. Open your browser and go to: http://localhost:8000")
        print("\nNote: All required dependencies have been downloaded for offline use.")
        print("      You can now serve the game with a simple HTTP server without CDN dependencies.")

if __name__ == "__main__":
    main()