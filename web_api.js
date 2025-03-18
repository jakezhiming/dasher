/**
 * JavaScript functions for handling LLM API calls in the web environment
 * Note: For security reasons, API keys are never used directly in the web version.
 * All API calls are routed through a proxy server.
 */

const BaseUrl = "https://dasher-30lv.onrender.com/"; 
// Base URL for the server: "http://localhost:10000/" for local development 
// or your Render URL (e.g., "https://dasher-api.onrender.com/")

const _tokenParts = [
    "MWEzZWI3OTkt",
    "OWQxMC00ZjQ2",
    "LWE1MGEtMzJj",
    "YmRjYjVhZWQy"
];

function getProxyToken() {
    try {
        return atob(_tokenParts.join(''));
    } catch (e) {
        console.error("Failed to decode token:", e);
        return null;
    }
}

window.llmResponse = null;
window.leaderboardData = null;

// Fetch leaderboard data
window.fetchLeaderboard = async function(limit = 10) {
    try {
        console.log("Fetching leaderboard data from server...");
        const response = await fetch(`${BaseUrl}leaderboard?limit=${limit}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Leaderboard data received:", data);
        window.leaderboardData = data;
        return data;
    } catch (error) {
        console.error("Error fetching leaderboard:", error);
        // Don't clear existing data on error
        return window.leaderboardData || null;
    }
};

// Submit a new score
window.submitScore = async function(playerName, score) {
    try {
        console.log(`Submitting score: ${playerName} - ${score}`);
        const token = getProxyToken();
        if (!token) {
            throw new Error("Failed to authenticate with proxy");
        }

        // Store the pre-submission state for comparison
        const oldLeaderboardData = JSON.stringify(window.leaderboardData || []);

        const response = await fetch(`${BaseUrl}leaderboard`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Token': token
            },
            body: JSON.stringify({
                player_name: playerName,
                score: score
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        console.log("Score submitted successfully, refreshing leaderboard");
        
        // Refresh leaderboard after submitting score
        const newData = await window.fetchLeaderboard();
        
        // Check if the data actually changed
        const newLeaderboardData = JSON.stringify(newData || []);
        if (oldLeaderboardData === newLeaderboardData) {
            console.warn("Leaderboard data didn't change after score submission, forcing refresh");
            // Force a timeout and retry to ensure the server had time to process
            await new Promise(resolve => setTimeout(resolve, 500));
            await window.fetchLeaderboard();
        }
        
        return newData;
    } catch (error) {
        console.error("Error submitting score:", error);
        return false;
    }
};

window.fetchLLMResponse = async function(payload_json) {
    try {
        // Validate payload_json
        if (!payload_json || typeof payload_json !== 'string') {
            console.error("Invalid payload_json:", payload_json);
            window.llmResponse = "DasherError: Invalid or missing payload";
            return;
        }
        
        try {
            payload = JSON.parse(payload_json);
        } catch (e) {
            console.error("Failed to parse payload_json:", e.message);
            window.llmResponse = "DasherError: Invalid payload JSON - " + e.message;
            return;
        }
        
        // Get the token at runtime
        const token = getProxyToken();
        if (!token) {
            window.llmResponse = "DasherError: Failed to authenticate with proxy";
            return;
        }
        
        // Fetch the LLM response
        const response = await fetch(`${BaseUrl}api/openai`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-API-Token': token },
            body: payload_json
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error("Error fetching LLM response:", response.status, errorText);
            window.llmResponse = `DasherError: ${response.status} - ${errorText}`;
            return;
        }
        
        const text = await response.text();
        
        // Parse the response
        let message = text;
        try {
            const data = JSON.parse(text);
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
                window.llmResponse = "DasherError: Empty or invalid response from proxy";
                return;
            }
            message = text;
        }
        
        window.llmResponse = message;
    } catch (error) {
        console.error("Error in fetchLLMResponse:", error);
        window.llmResponse = "DasherError: " + error.message;
    }
};

// Create a namespace for our web APIs
window.DASHER_WEB_API = {
    // Provide a better random number generator for the web version
    getRandomNumber: function() {
        const array = new Uint32Array(1);
        window.crypto.getRandomValues(array);
        return array[0] / 4294967295;
    },
    
    // Initialize the API
    init: async function() {
        console.log("DASHER_WEB_API initialized");
        try {
            // Fetch initial leaderboard data
            console.log("Fetching initial leaderboard data...");
            const data = await window.fetchLeaderboard();
            console.log("Initial leaderboard data loaded:", data);
        } catch (e) {
            console.error("Error loading initial leaderboard data:", e);
        }
    }
};

// Initialize the API
window.DASHER_WEB_API.init();