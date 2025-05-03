// src/components/ProtectedRoute.jsx
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function ProtectedRoute({ children }) {
  const { token, loading } = useAuth();
  const location = useLocation(); // Get current location

  // If still loading initial auth state, don't render anything yet (or show a spinner)
  if (loading) {
    return null; // Or your loading component
  }

  // If not loading and no token, redirect to login
  if (!token) {
    // Redirect them to the /login page, but save the current location they were
    // trying to go to in the state of the location object. This allows us to
    // send them back to that page after they login, which is a nicer user experience
    // than dropping them off on the home page.
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If token exists and not loading, render the requested component (e.g., ChatPage)
  return children;
}

export default ProtectedRoute;
