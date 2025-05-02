import { useState, useEffect, useRef } from "react";
import "./App.css";

// Define the API endpoint URL
const API_URL = "http://localhost:8000/chat"; // Your FastAPI backend URL

function App() {
  // State for messages in the chat [{ sender: 'user' | 'ai', text: string }]
  const [messages, setMessages] = useState([]);
  // State for the current value in the input field
  const [inputValue, setInputValue] = useState("");
  // State to store the current conversation ID
  const [conversationId, setConversationId] = useState(null);
  // State to indicate if waiting for API response
  const [isLoading, setIsLoading] = useState(false);
  // State to store potential errors
  const [error, setError] = useState(null);

  // Ref for scrolling the messages list
  const messagesEndRef = useRef(null);

  // Function to scroll to the bottom of the messages list
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Scroll to bottom whenever messages update
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Function to handle sending a message
  const handleSendMessage = async (event) => {
    // Prevent default form submission if used within a form
    if (event) event.preventDefault();

    const userMessageText = inputValue.trim();
    if (!userMessageText) return; // Don't send empty messages

    // Add user message immediately to the UI
    const newUserMessage = { sender: "user", text: userMessageText };
    setMessages((prevMessages) => [...prevMessages, newUserMessage]);

    setInputValue(""); // Clear the input field
    setIsLoading(true); // Set loading state
    setError(null); // Clear previous errors

    try {
      // Prepare payload for the API
      const payload = {
        user_message: userMessageText,
        conversation_id: conversationId, // Send null if no ID yet, backend handles creation
      };

      console.log("Sending to API:", payload); // Log the payload being sent

      // Make the API call
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        // Handle HTTP errors
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Unknown error occurred" })); // Try to parse error detail
        console.error("API Error Response:", errorData);
        throw new Error(
          `HTTP error ${response.status}: ${
            errorData.detail || response.statusText
          }`
        );
      }

      // Parse the successful JSON response
      const data = await response.json();
      console.log("Received from API:", data); // Log the response

      // Add AI response to the messages list
      const newAiMessage = { sender: "ai", text: data.ai_response };
      setMessages((prevMessages) => [...prevMessages, newAiMessage]);

      // IMPORTANT: Update the conversation ID for the next request
      setConversationId(data.conversation_id);
    } catch (err) {
      console.error("Failed to send message:", err);
      setError(`Error: ${err.message}`);
      // Optionally add an error message to the chat
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "ai", text: `Sorry, an error occurred: ${err.message}` },
      ]);
    } finally {
      setIsLoading(false); // Reset loading state
    }
  };

  return (
    <div className="chat-container">
      <div className="messages-list">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        {/* Optionally show loading indicator */}
        {isLoading && (
          <div className="loading-indicator ai">AI is thinking...</div>
        )}
        {/* Ref element to scroll to */}
        <div ref={messagesEndRef} />
      </div>
      {/* Display error message if any */}
      {error && (
        <div style={{ color: "red", padding: "0 1rem 1rem 1rem" }}>{error}</div>
      )}
      <form className="input-area" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading} // Disable input while loading
          aria-label="Chat input"
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? "Sending..." : "Send"}
        </button>
      </form>
    </div>
  );
}

export default App;
