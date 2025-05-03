// src/pages/ChatPage.jsx (Previously App.jsx)
import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext"; // Import useAuth
import { sendMessage } from "../api"; // Use the centralized API call
import { ThemeProvider } from "@mui/material/styles"; // Keep theme provider if theme is defined here // Assuming theme is defined in theme.js or here
import CssBaseline from "@mui/material/CssBaseline";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import SendIcon from "@mui/icons-material/Send";
import LogoutIcon from "@mui/icons-material/Logout"; // Logout icon
import AppBar from "@mui/material/AppBar"; // For Header
import Toolbar from "@mui/material/Toolbar";
import IconButton from "@mui/material/IconButton";

// Define the dark theme here or import from a separate file
const darkTheme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#90caf9" },
    background: { default: "#121212", paper: "#1e1e1e" },
  },
  typography: {
    fontFamily: "Inter, system-ui, Avenir, Helvetica, Arial, sans-serif",
  },
});

function ChatPage() {
  const { user, logout } = useAuth(); // Get user info and logout function
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [conversationId, setConversationId] = useState(null); // Keep managing conversation ID locally
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // TODO: Add logic here to fetch user's past conversations list
  // and allow selecting one, or starting new.
  // For now, it always starts a new conversation on page load.
  useEffect(() => {
    // Reset conversation ID when the component mounts or user changes
    setConversationId(null);
    setMessages([]); // Clear messages for a clean start
    // You might fetch the last active conversation ID for the user here instead
  }, [user]); // Reset when user changes (e.g., after logout/login)

  const handleSendMessage = async (event) => {
    if (event) event.preventDefault();
    const userMessageText = inputValue.trim();
    if (!userMessageText || isLoading) return;

    const newUserMessage = { sender: "user", text: userMessageText };
    // Use functional update to ensure state consistency
    setMessages((prev) => [...prev, newUserMessage]);
    setInputValue("");
    setIsLoading(true);
    setError(null);

    try {
      // Use the imported sendMessage function which includes the token
      const response = await sendMessage(userMessageText, conversationId);
      const data = response.data; // Axios wraps response in .data

      console.log("Received from API:", data);
      const newAiMessage = { sender: "ai", text: data.ai_response };
      setMessages((prev) => [...prev, newAiMessage]);
      setConversationId(data.conversation_id); // Update conversation ID
    } catch (err) {
      // Axios errors often have response data
      const errorMsg =
        err.response?.data?.detail || err.message || "Failed to send message.";
      console.error("Failed to send message:", err);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    // Navigation to /login will happen automatically if this page
    // is wrapped in ProtectedRoute and token becomes null.
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ display: "flex", flexDirection: "column", height: "100vh" }}>
        {/* Header Bar */}
        <AppBar position="static" elevation={1}>
          <Toolbar variant="dense">
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              AI Chat Assistant
            </Typography>
            {user && (
              <Typography variant="caption" sx={{ mr: 2 }}>
                Logged in as: {user.username}
              </Typography>
            )}
            <IconButton
              color="inherit"
              onClick={handleLogout}
              aria-label="logout"
            >
              <LogoutIcon />
            </IconButton>
          </Toolbar>
        </AppBar>
        {/* Main Chat Area using Box */}
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            flexGrow: 1, // Take remaining space
            maxWidth: "900px", // Wider chat
            width: "100%",
            mx: "auto", // Center horizontally
            p: { xs: 1, sm: 2 }, // Responsive padding
            overflow: "hidden", // Prevent content spill
          }}
        >
          {/* Message List Area */}
          <Paper
            elevation={0} // Flat look for message area
            sx={{
              flexGrow: 1,
              overflowY: "auto",
              mb: 1,
              p: 2,
              bgcolor: "background.default", // Match main background or use paper
              // Scrollbar styling (optional)
              "&::-webkit-scrollbar": { width: "8px" },
              "&::-webkit-scrollbar-track": {
                backgroundColor: "background.paper",
              },
              "&::-webkit-scrollbar-thumb": {
                backgroundColor: "action.disabled",
                borderRadius: "4px",
              },
            }}
          >
            <List sx={{ padding: 0 }}>
              {/* ... (mapping messages logic remains the same as before) ... */}
              {messages.map((msg, index) => (
                <ListItem
                  key={index}
                  sx={{
                    display: "flex",
                    justifyContent:
                      msg.sender === "user" ? "flex-end" : "flex-start",
                    px: 0,
                    py: 0.5,
                  }}
                >
                  <Paper
                    elevation={1}
                    sx={{
                      px: 1.5,
                      py: 1,
                      maxWidth: "75%",
                      bgcolor:
                        msg.sender === "user" ? "primary.dark" : "grey.700",
                      color: "common.white",
                      borderRadius:
                        msg.sender === "user"
                          ? "15px 0px 15px 15px"
                          : "0px 15px 15px 15px",
                      whiteSpace: "pre-wrap",
                      wordWrap: "break-word",
                    }}
                  >
                    <Typography variant="body1">{msg.text}</Typography>
                  </Paper>
                </ListItem>
              ))}
              <ListItem ref={messagesEndRef} sx={{ height: 0, p: 0 }} />
            </List>
          </Paper>

          {/* Loading and Error Display Area */}
          <Box
            sx={{
              height: "40px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              mb: 1,
            }}
          >
            {isLoading && <CircularProgress size={24} />}
            {error && (
              <Alert
                severity="error"
                sx={{
                  width: "100%",
                  ".MuiAlert-message": { overflow: "hidden" },
                }}
              >
                {error}
              </Alert>
            )}
          </Box>

          {/* Input Area */}
          <Box
            component="form"
            onSubmit={handleSendMessage}
            sx={{ display: "flex", gap: 1, alignItems: "center", p: 1 }}
          >
            {/* ... (TextField and Button remain the same as before) ... */}
            <TextField
              fullWidth
              variant="outlined"
              size="small"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your message..."
              disabled={isLoading}
              aria-label="Chat input"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />
            <Button
              type="submit"
              variant="contained"
              disabled={isLoading || !inputValue.trim()}
              endIcon={<SendIcon />}
              sx={{ height: "40px" }}
            >
              Send
            </Button>
          </Box>
        </Box>{" "}
        {/* End Main Chat Area Box */}
      </Box>{" "}
      {/* End Full Height Box */}
    </ThemeProvider>
  );
}

// Helper function to create theme (can be moved to a separate file like src/theme.js)
import { createTheme } from "@mui/material/styles";

export default ChatPage; // Export the ChatPage component
