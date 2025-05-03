import React from "react";
import ReactDOM from "react-dom/client"; // Correct import for React 18+
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import LoginPage from "./pages/LoginPage.jsx"; // Correct import
import RegisterPage from "./pages/RegisterPage.jsx"; // Correct import
import ChatPage from "./pages/ChatPage.jsx"; // Correct import

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected Chat Route */}
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatPage /> {/* Use the imported ChatPage component */}
              </ProtectedRoute>
            }
          />

          {/* Redirect base path */}
          <Route path="/" element={<Navigate replace to="/chat" />} />

          {/* Fallback route */}
          <Route path="*" element={<Navigate replace to="/login" />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
