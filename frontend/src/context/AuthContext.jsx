// src/context/AuthContext.jsx
import React, { createContext, useState, useEffect, useContext } from "react";
import { getCurrentUser } from "../api"; // Import API function

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem("authToken")); // Initialize from local storage
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // Start loading until we verify token

  useEffect(() => {
    const verifyUser = async () => {
      if (token) {
        // If token exists, try to fetch user data
        try {
          const response = await getCurrentUser(); // Uses the interceptor to send token
          setUser(response.data);
        } catch (error) {
          console.error("Token validation failed or user fetch failed:", error);
          // Token is invalid or expired, clear it
          localStorage.removeItem("authToken");
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false); // Finished initial check
    };

    verifyUser();
  }, [token]); // Re-run effect if token changes

  const login = (newToken, userData) => {
    localStorage.setItem("authToken", newToken);
    setToken(newToken);
    setUser(userData); // Optionally store user data received after login/fetch
  };

  const logout = () => {
    localStorage.removeItem("authToken");
    setToken(null);
    setUser(null);
    // Potentially redirect to login page using useNavigate() from react-router-dom
  };

  const value = {
    token,
    user,
    loading, // Provide loading state
    login,
    logout,
  };

  // Don't render children until initial auth check is done
  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context easily
export const useAuth = () => {
  return useContext(AuthContext);
};
