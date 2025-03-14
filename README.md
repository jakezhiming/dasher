# Dasher

A 2D side-scrolling platformer game built with Pygame where you run, jump, and dash through an endless procedurally generated world.

## Game Overview

In Dasher, you control a character that must navigate through an endless world filled with:
- Platforms to jump on
- Obstacles to avoid
- Pits to cross
- Coins to collect
- Power-ups to enhance your abilities

The game features progressive difficulty - the further you go, the more challenging the obstacles and terrain become.

## Controls

- **Left/Right Arrow Keys**: Move left/right
- **Space**: Jump

## Game Features

- **Procedurally Generated World**: Every playthrough is unique with randomly generated terrain
- **Power-ups**:
  - Speed boost
  - Invincibility
  - Flying
  - Extra life
  - And more!
- **Difficulty Scaling**: The game gets progressively harder the further you go
- **AI-Powered Messages**: Game messages are rephrased by an AI in different personalities (pirate, robot, wizard, etc.) using OpenAI's GPT-4o-mini model
- **Comprehensive Logging System**: Detailed logging for debugging and monitoring game events

## AI Message System

Dasher features an AI-powered message system that adds personality to the game's status messages. Each time you start the game, a random personality is chosen (pirate, robot, medieval knight, etc.), and all game messages are rephrased in that style.

### Setup

To use the AI message system:

1. Rename `.envexample` to `.env`
2. Add your OpenAI API key to the `.env` file
3. Make sure you have the required dependencies installed (see Installation section)

If no API key is provided, the game will fall back to using the original messages without AI rephrasing.

## Logging System

Dasher includes a comprehensive logging system that records game events, errors, and performance metrics. This is useful for debugging and monitoring game behavior.

### Logging Configuration

You can configure the logging system by setting the following variables in your `.env` file:

```
# Logging configuration
# Available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
LOG_TO_FILE=True
LOG_TO_CONSOLE=True
```

- **LOG_LEVEL**: Sets the minimum level of messages to log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **LOG_TO_FILE**: When set to True, logs are saved to files in the `logs` directory
- **LOG_TO_CONSOLE**: When set to True, logs are displayed in the console

### Log Files

Log files are stored in the `logs` directory with timestamps in their filenames. The system uses rotating file handlers to limit file size and automatically creates new log files when needed.

## Requirements

- Python 3.x
- Pygame

## Installation

1. Ensure you have Python installed on your system
2. Install Pygame:
```
pip install pygame
```
3. Clone or download this repository
4. Run the game:
```
python main.py
```

## Game Mechanics

- **Collision Detection**: Precise collision handling for platforms, obstacles, and collectibles
- **Camera System**: Dynamic camera that follows the player
- **Invincibility**: Temporary protection after taking damage
- **Score System**: Based on distance traveled and coins collected

## Development

This game was developed using:
- Python
- Pygame for rendering and game logic

## Building for Web with Pygbag

[Pygbag](https://pygame-web.github.io/pygbag/) is a tool that allows you to package and run Pygame games in web browsers using WebAssembly. This section explains how to build and deploy Dasher for the web.

### Prerequisites

1. Install Pygbag:
   ```bash
   pip install pygbag
   ```

2. Make sure your game is compatible with Pygbag:
   - The game has been updated to use asyncio for the main loop
   - OpenAI API integration has been adapted for web environment

### Building the Game

1. Run the build script:
   ```bash
   python pygbag_build.py
   ```

2. The built files will be in the `build/web` directory.

3. To test locally:
   ```bash
   python -m http.server --directory build/web
   ```
   Then open a browser and go to: http://localhost:8000

### Web Configuration

The web version of Dasher uses a single configuration file called `web_config.js` to manage all web-specific settings. This simplifies the configuration process and makes it easier to deploy the game.

#### Setting Up web_config.js

1. Create a `web_config.js` file in the root directory of your project with the following structure:

```javascript
/**
 * Web Configuration for Dasher Game
 */

// Initialize the global ENV object
window.ENV = window.ENV || {};

// API Configuration
window.ENV.OPENAI_PROXY_URL = "http://localhost:5000/api/openai";

// Game Configuration
window.ENV.GAME_TITLE = "Dasher";
window.ENV.DEBUG_MODE = false;

// Add any other configuration settings your game needs
// window.ENV.SOME_SETTING = "some value";

// Log that configuration has been loaded
console.log("Web configuration loaded:", window.ENV);
```

2. Customize the settings as needed for your deployment.

3. When you run the build script, this file will be automatically included in the web build.

#### Configuration Options

- **OPENAI_PROXY_URL**: URL of your OpenAI proxy server (for AI-powered messages)
- **GAME_TITLE**: Title of the game (displayed in the browser tab)
- **DEBUG_MODE**: Enable/disable debug mode

You can add any other configuration options your game needs by adding them to the `window.ENV` object.

### Using OpenAI API in Web Version

The web version supports OpenAI API integration for AI-powered messages. There are two ways to use this feature:

#### Option 1: Using a Proxy Server (Recommended)

This approach is more reliable and secure, as it avoids CORS issues and keeps your API key on the server.

1. Install the proxy server dependencies:
   ```bash
   pip install flask flask-cors requests
   ```

2. Start the proxy server:
   ```bash
   python proxy_server.py --port 5000 --host 0.0.0.0 --log-file proxy.log
   ```
   
   Available options:
   - `--port`: Port to run the server on (default: 5000)
   - `--host`: Host to run the server on (default: 0.0.0.0)
   - `--log-file`: Log file to write to (optional)

3. Build the game with the proxy URL:
   ```bash
   python pygbag_build.py
   ```
   
   The proxy URL should be configured in your `web_config.js` file:
   ```javascript
   window.ENV.OPENAI_PROXY_URL = "http://localhost:5000/api/openai";
   ```

4. Test the proxy server:
   ```bash
   curl http://localhost:5000/api/test
   ```
   You should see a JSON response with status "ok".

#### Option 2: Direct API Access (Browser Only)

This approach is simpler but may encounter CORS issues in some browsers.

1. Build the game normally:
   ```bash
   python pygbag_build.py
   ```

2. Configure your `web_config.js` to use direct API access or provide a UI for entering the API key.

3. When playing the game in the browser, you'll see an API key input field where you can enter your OpenAI API key.
   - The key is stored only in your browser's localStorage
   - It's sent directly to OpenAI's API (may encounter CORS issues on some browsers)
   - You can test your API key by clicking the "Test Key" button

### Deploying to a Web Server

#### Deploying the Game

1. Upload the contents of the `build/web` directory to your web server.
2. Make sure your server is configured to serve static files.
3. For Apache, you might need a .htaccess file with:
   ```
   Options -MultiViews
   RewriteEngine On
   <Files ~ "\.(wasm|data)$">
     Header set Cache-Control "no-store, no-cache, must-revalidate, max-age=0"
   </Files>
   ```

#### Deploying the Proxy Server

If you're using the proxy server approach, you'll need to deploy the proxy server as well:

1. **Using a standalone server**:
   ```bash
   python proxy_server.py --port 5000 --host 0.0.0.0 --log-file /var/log/openai_proxy.log
   ```
   
   Consider using a process manager like Supervisor or systemd to keep it running.

2. **Using a WSGI server (recommended for production)**:
   
   Create a WSGI file (e.g., `wsgi.py`):
   ```python
   import os
   from proxy_server import app
   
   # Set your API key in the environment
   os.environ["OPENAI_API_KEY"] = "your-api-key-here"
   
   if __name__ == "__main__":
       app.run()
   ```
   
   Then run with Gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
   ```

3. **Using a reverse proxy**:
   
   Configure Nginx to proxy requests to your Flask app:
   ```
   location /api/ {
       proxy_pass http://localhost:5000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

4. When building the game, configure the proxy URL in your `web_config.js` file:
   ```javascript
   window.ENV.OPENAI_PROXY_URL = "https://your-domain.com/api/openai";
   ```
   
   Then build the game:
   ```bash
   python pygbag_build.py
   ```

### Security Considerations

1. **API Key Protection**: 
   - When using the proxy server, store your API key securely on the server
   - Consider using environment variables or a secrets manager
   - Never hardcode API keys in your source code

2. **Rate Limiting**:
   - The proxy server includes basic rate limiting to prevent abuse
   - Adjust `MAX_REQUESTS_PER_MINUTE` in proxy_server.py based on your OpenAI plan

3. **HTTPS**:
   - Always use HTTPS for your proxy server in production
   - Let's Encrypt provides free SSL certificates

### Web Version Limitations

The web version has some limitations compared to the desktop version:

1. Performance may vary depending on the browser and device
2. Some browsers may block direct API calls due to CORS restrictions (use the proxy server to avoid this)
3. Local file access is restricted

### Troubleshooting

- If you encounter issues with the build, make sure you have the latest version of Pygbag installed.
- If OpenAI API calls fail, check the browser console for CORS errors and consider using the proxy server.
- Some browsers may require enabling WebAssembly support.
- If the proxy server doesn't work, make sure it's running and accessible from the browser.
- Check the proxy server logs for detailed error information.