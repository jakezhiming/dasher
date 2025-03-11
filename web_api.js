/**
 * JavaScript functions for handling LLM API calls in the web environment
 * Note: For security reasons, API keys are never used directly in the web version.
 * All API calls are routed through a proxy server.
 */

window.llmResponse = null;

window.getProxyUrl = function() {
    if (window.ENV && window.ENV.OPENAI_PROXY_URL) {
        console.log("Using proxy URL from environment variables:", window.ENV.OPENAI_PROXY_URL);
        return window.ENV.OPENAI_PROXY_URL;
    }
    
    // Add a fallback mechanism to check if the environment.js file is loaded
    console.log("No proxy URL found in window.ENV. Current window.ENV:", window.ENV);
    
    // Check if we're in a development environment and use a default URL
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
        const defaultProxyUrl = "http://localhost:5000/api/openai";
        console.log("Using default development proxy URL:", defaultProxyUrl);
        return defaultProxyUrl;
    }
    
    console.log("No proxy URL found in environment variables and not in development mode");
    return null;
};

window.fetchLLMResponse = async function(url, payload_json) {
    // Handle case where url is the only argument (backwards compatibility)
    if (arguments.length === 1 && typeof url === 'string' && !payload_json) {
        payload_json = url;  // Assume single argument is the payload
        url = null;          // Let getProxyUrl() provide the URL
    }
    
    if (!url) {
        url = window.getProxyUrl();
        if (!url) {
            console.error("No proxy URL provided and none found in environment variables");
            window.llmResponse = "Error: No proxy URL available";
            return;
        }
    }
    
    console.log("Fetching LLM response from proxy server:", url);
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