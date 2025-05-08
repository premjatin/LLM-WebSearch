# LLM-WebSearch - AI Chat Assistant with RAG & Web Search

This project is an AI-powered chat assistant built with Python (FastAPI, LangGraph) for the backend and React for the frontend. It features user authentication, conversation history, and an agent capable of using a Retrieval Augmented Generation (RAG) system with a local FAISS vector store, as well as performing live web searches to answer user queries.

## Features

*   **Conversational AI Agent:** Utilizes LangGraph to create a ReAct-style agent.
*   **User Authentication:** Secure user registration and login using JWT (JSON Web Tokens).
*   **Persistent Conversation History:** Chat history is saved per user in a PostgreSQL database.
*   **Retrieval Augmented Generation (RAG):**
    *   Uses a local FAISS vector store for efficient similarity search.
    *   Ingests custom documents to provide context-specific answers.
    *   Uses Sentence Transformers for embeddings.
*   **Web Search Capability:** Falls back to DuckDuckGo web search for up-to-date information or topics not covered by RAG.
*   **Modern Tech Stack:**
    *   **Backend:** FastAPI, LangGraph, LangChain, SQLAlchemy, Groq (for LLM access).
    *   **Frontend:** React (with Vite), Material UI (MUI) for styling, Axios for API calls.
    *   **Database:** PostgreSQL.
*   **Interactive Frontend:** User-friendly chat interface built with React and MUI.

## Tech Stack

*   **Backend:**
    *   Python 3.10+
    *   FastAPI
    *   Uvicorn (ASGI server)
    *   LangChain & LangGraph
    *   `langchain-groq` for LLM access (Llama 3 models)
    *   SQLAlchemy (ORM for PostgreSQL)
    *   `psycopg2-binary` (PostgreSQL adapter)
    *   `python-jose[cryptography]` & `passlib[bcrypt]` (for JWT auth)
    *   FAISS (`faiss-cpu` or `faiss-gpu`)
    *   Sentence Transformers (`sentence-transformers`)
    *   DuckDuckGo Search (`duckduckgo-search`)
    *   `python-dotenv` & `pydantic-settings`
*   **Frontend:**
    *   Node.js & npm/yarn
    *   React (with Vite)
    *   Material UI (MUI)
    *   Axios
    *   `react-router-dom`
*   **Database:**
    *   PostgreSQL

## Setup and Installation

### Prerequisites

*   Python 3.10 or higher
*   Node.js and npm (or yarn)
*   PostgreSQL server installed and running
*   Git

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/premjatin/LLM-WebSearch.git
    cd LLM-WebSearch
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install backend dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up PostgreSQL Database:**
    *   Create a PostgreSQL database (e.g., `chat_db`).
    *   Create a PostgreSQL user and grant it permissions to the database.

5.  **Configure Backend Environment Variables:**
    *   Create a `.env` file in the project root by copying `.env.example` (if you create one) or create it manually.
    *   Update the `.env` file with your settings:
        ```dotenv
        GROQ_API_KEY="your_groq_api_key"
        DATABASE_URL="postgresql+psycopg2://YOUR_PG_USER:YOUR_PG_PASSWORD@localhost:5432/chat_db"
        JWT_SECRET_KEY="your_very_strong_random_secret_key_for_jwt" # Generate a strong key!
        JWT_ALGORITHM="HS256"
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

        # RAG Settings (defaults are usually fine)
        EMBEDDING_MODEL_NAME="all-MiniLM-L6-v2"
        VECTOR_STORE_PATH="./vector_store_data"
        FAISS_INDEX_FILE="faiss_index.bin"
        FAISS_METADATA_FILE="faiss_metadata.pkl"
        ```

6.  **Initialize Database Tables:**
    *   The application is configured to create tables on startup. Ensure your `DATABASE_URL` is correct.

7.  **(Optional) Ingest Data for RAG:**
    *   Place your source documents (e.g., `.txt` files) into a directory (e.g., `data/my_documents`).
    *   Run the ingestion script:
        ```bash
        python scripts/load_rag_data.py ./data/my_documents
        ```
    *   This will create the FAISS index in the `vector_store_data/` directory.

8.  **Run the Backend Server:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The backend API will be available at `http://localhost:8000`.

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install frontend dependencies:**
    ```bash
    npm install
    # Or: yarn install
    ```

3.  **Configure Frontend Environment Variables:**
    *   Create a `.env` file inside the `frontend` directory (e.g., `frontend/.env`).
    *   Add the backend API URL:
        ```dotenv
        VITE_API_BASE_URL=http://localhost:8000/api/v1
        ```

4.  **Run the Frontend Development Server:**
    ```bash
    npm run dev
    # Or: yarn dev
    ```
    The frontend application will typically be available at `http://localhost:5173`.

## Usage

1.  Ensure both backend and frontend servers are running.
2.  Open your browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
3.  Register a new user account or log in if you already have one.
4.  You will be redirected to the chat interface.
5.  Start chatting with the AI! It will use RAG or web search as needed based on your queries and the system prompt.

## API Endpoints

The backend exposes the following key API endpoints (base URL `http://localhost:8000/api/v1`):

*   **Authentication:**
    *   `POST /auth/register`: Register a new user.
    *   `POST /auth/token`: Log in and get a JWT access token.
    *   `GET /auth/users/me`: Get current logged-in user's details (protected).
*   **Chat:**
    *   `POST /chat`: Send a message to the chat agent and get a response (protected).

Refer to `http://localhost:8000/docs` for interactive API documentation (Swagger UI) when the backend is running.

## Future Enhancements (Ideas)

*   OCR Integration for Document Q&A or Grading.
*   More sophisticated RAG strategies (e.g., re-ranking, query expansion).
*   Streaming responses for a more real-time chat feel.
*   User ability to manage/select different RAG knowledge bases.
*   Admin interface for user management.
*   Deployment using Docker and a cloud platform.


Built by premjatin
