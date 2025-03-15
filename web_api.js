/**
 * JavaScript functions for handling LLM API calls in the web environment
 * Note: For security reasons, API keys are never used directly in the web version.
 * All API calls are routed through a proxy server.
 */

const ProxyUrl = "http://localhost:5000/api/openai";

window.llmResponse = null;

window.fetchLLMResponse = async function(payload_json) {
    url = ProxyUrl;

    try {
        // Validate payload_json
        if (!payload_json || typeof payload_json !== 'string') {
            console.error("Invalid payload_json:", payload_json);
            window.llmResponse = "Error: Invalid or missing payload";
            return;
        }
        
        let payload;
        try {
            payload = JSON.parse(payload_json);
        } catch (e) {
            console.error("Failed to parse payload_json:", e.message);
            window.llmResponse = "Error: Invalid payload JSON - " + e.message;
            return;
        }
        console.log("Payload:", payload);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: payload_json
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error("Error fetching LLM response:", response.status, response.statusText, errorText);
            window.llmResponse = `Error: ${response.status} ${response.statusText} - ${errorText}`;
            return;
        }
        
        const text = await response.text();
        console.log("Raw response text:", text);
        
        let message = text;
        try {
            const data = JSON.parse(text);
            console.log("Parsed JSON response:", data);
            if (data.choices && data.choices.length > 0) {
                if (data.choices[0].message) {
                    message = data.choices[0].message.content;
                } else if (data.choices[0].text) {
                    message = data.choices[0].text;
                }
            } else if (data.response) {
                message = data.response;
            }
        } catch (jsonError) {
            console.warn("Response is not valid JSON:", jsonError.message, "Using raw text instead");
            if (text === "undefined" || text === "" || text === null) {
                console.error("Received invalid or empty response:", text);
                window.llmResponse = "Error: Empty or invalid response from proxy";
                return;
            }
            message = text;
        }
        
        window.llmResponse = message;
        console.log("Stored LLM response:", window.llmResponse);
    } catch (error) {
        console.error("Error in fetchLLMResponse:", error);
        window.llmResponse = "Error: " + error.message;
    }
};

// Create a namespace for our web APIs
window.DASHER_WEB_API = {
    // Provide a better random number generator for the web version
    getRandomNumber: function() {
        // Use the browser's crypto API for better randomness
        const array = new Uint32Array(1);
        window.crypto.getRandomValues(array);
        // Return a number between 0 and 1
        return array[0] / 4294967295;
    },
    
    // Function to get multiple random numbers
    getRandomNumbers: function(count) {
        const array = new Uint32Array(count);
        window.crypto.getRandomValues(array);
        // Convert to array of numbers between 0 and 1
        return Array.from(array).map(x => x / 4294967295);
    },
    
    // Log that the web API is loaded
    init: function() {
        console.log("Dasher Web API loaded - providing crypto-based random number generation");
    }
};

// Initialize the API
window.DASHER_WEB_API.init();