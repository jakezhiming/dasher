// Web configuration
window.ENV = window.ENV || {};
// Note: For security reasons, API keys are not included in web version
window.ENV.OPENAI_PROXY_URL = "http://localhost:5000/api/openai";
console.log("Proxy URL configured:", window.ENV.OPENAI_PROXY_URL);
