/**
 * Web Configuration for Dasher Game
 * 
 * This file contains all configuration settings for the web version of the game.
 * It replaces the need for .env.web and environment.js by consolidating all
 * web-specific configuration in one place.
 */

// Initialize the global ENV object if it doesn't exist
window.ENV = window.ENV || {};

// API Configuration
// Note: For security reasons, API keys are not included in web version
window.ENV.OPENAI_PROXY_URL = "http://localhost:5000/api/openai";

// Game Configuration
window.ENV.GAME_TITLE = "Dasher";
window.ENV.DEBUG_MODE = false;

// Add any other configuration settings your game needs
// window.ENV.SOME_SETTING = "some value";

// Web-specific utilities
window.DASHER_WEB_API = window.DASHER_WEB_API || {};

// Random number generation for web environment
window.DASHER_WEB_API.getRandomNumber = function() {
    // Use the browser's crypto API for better randomness
    const array = new Uint32Array(1);
    window.crypto.getRandomValues(array);
    return array[0] / 4294967295; // Convert to [0, 1)
};

// Log that configuration has been loaded
console.log("Web configuration loaded:", window.ENV);
