// src/pages/RegisterPage.jsx
import React, { useState } from "react";
import { registerUser } from "../api";
import { useNavigate, Link } from "react-router-dom";
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  Container,
  Paper,
} from "@mui/material";

function RegisterPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState(""); // Optional email
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      await registerUser(username, password, email || null); // Pass email if provided
      setSuccess("Registration successful! Redirecting to login...");
      setTimeout(() => {
        navigate("/login"); // Redirect after a short delay
      }, 2000);
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail || err.message || "Registration failed.";
      console.error("Registration error:", err);
      setError(errorMsg);
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
          Sign Up
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
          {error && (
            <Alert severity="error" sx={{ width: "100%", mb: 2 }}>
              {error}
            </Alert>
          )}
          {success && (
            <Alert severity="success" sx={{ width: "100%", mb: 2 }}>
              {success}
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
          <TextField // Optional Email
            margin="normal"
            fullWidth
            id="email"
            label="Email Address (Optional)"
            name="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={loading || !!success} // Disable after success too
          >
            {loading ? "Registering..." : "Sign Up"}
          </Button>
          <Typography variant="body2" align="center">
            Already have an account?{" "}
            <Link to="/login" style={{ textDecoration: "none" }}>
              Sign In
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
}

export default RegisterPage;
