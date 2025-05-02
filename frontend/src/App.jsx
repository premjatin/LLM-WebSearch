import { useState, useEffect, useRef } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import Box from "@mui/material/Box";
import Container from "@mui/material/Container"; // Use Container for content width management
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import SendIcon from "@mui/icons-material/Send";

// API URL remains the same
const API_URL = "http://localhost:8000/chat";

// Theme remains the same
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

function App() {
  // State hooks remain the same
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const messagesEndRef = useRef(null);

  // Scroll to bottom effect remains the same
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle sending message logic remains the same
  const handleSendMessage = async (event) => {
    if (event) event.preventDefault();
    const userMessageText = inputValue.trim();
    if (!userMessageText || isLoading) return;

    const newUserMessage = { sender: "user", text: userMessageText };
    setMessages((prevMessages) => [...prevMessages, newUserMessage]);
    setInputValue("");
    setIsLoading(true);
    setError(null);

    try {
      const payload = {
        user_message: userMessageText,
        conversation_id: conversationId,
      };
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Unknown API error" }));
        throw new Error(
          `HTTP error ${response.status}: ${
            errorData.detail || response.statusText
          }`
        );
      }

      const data = await response.json();
      const newAiMessage = { sender: "ai", text: data.ai_response };
      setMessages((prevMessages) => [...prevMessages, newAiMessage]);
      setConversationId(data.conversation_id);
    } catch (err) {
      console.error("Failed to send message:", err);
      setError(`Error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      {/* Outer Box: Takes full viewport height and width */}
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          height: "100vh", // Full viewport height is key
          bgcolor: "background.default", // Apply background color here
        }}
      >
        {/* Container: Centers content and sets max width for readability */}
        <Container
          maxWidth="md" // Adjust max width: 'sm', 'md', 'lg', 'xl', or false to disable
          sx={{
            display: "flex",
            flexDirection: "column",
            flexGrow: 1, // Allow container to grow vertically
            py: 2, // Add vertical padding inside the container
            overflow: "hidden", // Prevent container itself from scrolling
          }}
        >
          <Typography
            variant="h5"
            component="h1"
            sx={{ textAlign: "center", mb: 2, color: "text.primary" }}
          >
            AI Chat Assistant
          </Typography>

          {/* Message List Area */}
          <Paper
            elevation={2}
            sx={{
              flexGrow: 1, // Take available vertical space within Container
              overflowY: "auto", // Enable scrolling *only* for messages
              mb: 1,
              p: 2,
              bgcolor: "background.paper",
              // Scrollbar styling (optional)
              "&::-webkit-scrollbar": { width: "8px" },
              "&::-webkit-scrollbar-track": {
                backgroundColor: "background.default",
              },
              "&::-webkit-scrollbar-thumb": {
                backgroundColor: "action.disabled",
                borderRadius: "4px",
              },
            }}
          >
            <List sx={{ padding: 0 }}>
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
                        msg.sender === "user" ? "primary.main" : "grey.700",
                      color:
                        msg.sender === "user"
                          ? "primary.contrastText"
                          : "common.white",
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
            sx={{ display: "flex", gap: 1, alignItems: "center", pt: 1 }} // Add slight padding top
          >
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
              sx={{ height: "40px" }} // Match TextField height
            >
              Send
            </Button>
          </Box>
        </Container>{" "}
        {/* End of Content Container */}
      </Box>{" "}
      {/* End of Full Height/Width Box */}
    </ThemeProvider>
  );
}

export default App;
