// src/api.js
import axios from "axios";

// Get the base URL from environment variables if set, otherwise default
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
// Add a console log to verify
console.log("API Base URL:", API_BASE_URL);

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Interceptor to add the Authorization token to requests if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("authToken"); // Get token from local storage
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Authentication endpoints
export const loginUser = (username, password) => {
  // FastAPI's OAuth2PasswordRequestForm expects form data
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  return apiClient.post("/auth/token", formData, {
    headers: {
      // Override content type for this specific request
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
};

export const registerUser = (username, password, email = null) => {
  const payload = { username, password };
  if (email) {
    payload.email = email;
  }
  return apiClient.post("/auth/register", payload);
};

export const getCurrentUser = () => {
  return apiClient.get("/auth/users/me");
};

// Chat endpoint
export const sendMessage = (user_message, conversation_id = null) => {
  const payload = { user_message, conversation_id };
  return apiClient.post("/chat", payload);
};

export default apiClient; // Export the configured axios instance if needed elsewhere
