// src/pages/LoginPage.jsx
import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { loginUser, getCurrentUser } from "../api";
import { useNavigate, Link } from "react-router-dom"; // For redirection and linking
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  Container,
  Paper,
} from "@mui/material"; // Using MUI

function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate(); // Hook for programmatic navigation

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      // 1. Attempt to get the token
      const loginResponse = await loginUser(username, password);
      const accessToken = loginResponse.data.access_token;

      if (accessToken) {
        // 2. Store token temporarily to fetch user data
        localStorage.setItem("authToken", accessToken); // Needed for the *next* API call

        // 3. Fetch user details using the new token
        const userResponse = await getCurrentUser(); // This uses the token via interceptor

        // 4. Update auth context with token and user data
        login(accessToken, userResponse.data);

        // 5. Redirect to chat page
        navigate("/chat"); // Navigate to the main chat interface
      } else {
        throw new Error("Login successful but no token received.");
      }
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail ||
        err.message ||
        "Login failed. Please check credentials.";
      console.error("Login error:", err);
      setError(errorMsg);
      localStorage.removeItem("authToken"); // Clean up token if login fails partially
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Paper
        elevation={3}
        sx={{
          marginTop: 8,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          padding: 3,
        }}
      >
        <Typography component="h1" variant="h5">
          Sign In
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
          {error && (
            <Alert severity="error" sx={{ width: "100%", mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            margin="normal"
            required
            fullWidth
            id="username"
            label="Username"
            name="username"
            autoComplete="username"
            autoFocus
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
          />
          <TextField
            margin="normal"
            required
            fullWidth
            name="password"
            label="Password"
            type="password"
            id="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={loading}
          >
            {loading ? "Signing In..." : "Sign In"}
          </Button>
          <Typography variant="body2" align="center">
            Don't have an account?{" "}
            <Link to="/register" style={{ textDecoration: "none" }}>
              Sign Up
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
}

export default LoginPage;
