/**
 * JavaScript functions for handling LLM API calls in the web environment
 * Note: For security reasons, API keys are never used directly in the web version.
 * All API calls are routed through a proxy server.
 */

// Global variable to store the LLM response
window.llmResponse = null;

/**
 * Get the proxy URL from environment variables
 * @returns {string} The proxy URL or null if not found
 */
window.getProxyUrl = function() {
    // Check if we have environment variables
    if (window.ENV && window.ENV.OPENAI_PROXY_URL) {
        console.log("Using proxy URL from environment variables:", window.ENV.OPENAI_PROXY_URL);
        return window.ENV.OPENAI_PROXY_URL;
    }
    
    // Fallback to default
    console.log("No proxy URL found in environment variables");
    return null;
};

/**
 * Fetch LLM response from the proxy server
 * @param {string} url - The proxy server URL
 * @param {string} payload_json - The JSON payload as a string
 */
window.fetchLLMResponse = async function(url, payload_json) {
    // If no URL is provided, try to get it from environment variables
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
        // Parse the payload JSON
        const payload = JSON.parse(payload_json);
        console.log("Payload:", payload);
        
        // Make the fetch request
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: payload_json
        });
        
        // Check if the response is ok
        if (!response.ok) {
            console.error("Error fetching LLM response:", response.status, response.statusText);
            window.llmResponse = "Error: " + response.status + " " + response.statusText;
            return;
        }
        
        // Parse the response JSON
        const data = await response.json();
        console.log("LLM response:", data);
        
        // Extract the message content
        let message = "";
        if (data.choices && data.choices.length > 0) {
            if (data.choices[0].message) {
                message = data.choices[0].message.content;
            } else if (data.choices[0].text) {
                message = data.choices[0].text;
            }
        }
        
        // Store the response
        window.llmResponse = message || JSON.stringify(data);
        console.log("Stored LLM response:", window.llmResponse);
    } catch (error) {
        console.error("Error in fetchLLMResponse:", error);
        window.llmResponse = "Error: " + error.message;
    }
}; 