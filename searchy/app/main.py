from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, engine, init_db, get_db
from app.db import models, crud
from app.schemas import ChatMessageInput, ChatMessageOutput
from app.agent.agent_executor import run_agent
from app.core.config import settings # Import settings if needed elsewhere

# Create database tables if they don't exist
# You might want to manage migrations separately in a real app (e.g., with Alembic)
# init_db() # Uncomment this line to create tables on startup if needed

app = FastAPI(title="LangGraph RAG Agent API")

# Configure CORS
origins = [
    "http://localhost:3000",  # Allow your React frontend (adjust port if needed)
    "http://localhost:8000",  # Allow the API itself (optional)
    # Add any other origins if necessary
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.on_event("startup")
async def startup_event():
    # You can add startup logic here, like initializing models or connections
    print("Application startup...")
    # Example: Check if RAG store is loaded (optional)
    from app.rag.vector_store import vector_store
    if not vector_store.is_ready():
         print("WARNING: RAG vector store is not loaded or is empty.")
    else:
         print("RAG vector store seems ready.")
    # Ensure DB tables exist (safer than calling init_db() directly here sometimes)
    try:
        models.Base.metadata.create_all(bind=engine)
        print("Database tables checked/created.")
    except Exception as e:
        print(f"Error creating database tables: {e}")


@app.post("/chat", response_model=ChatMessageOutput)
async def chat_endpoint(
    chat_input: ChatMessageInput,
    db: Session = Depends(get_db) # Inject DB session
):
    """
    Endpoint to handle chat interactions.
    Receives user message, optional conversation ID.
    Returns AI response and conversation ID.
    """
    try:
        # 1. Get or create conversation
        conversation = crud.get_or_create_conversation(db, chat_input.conversation_id)
        if not conversation:
             # This shouldn't happen with get_or_create, but defensive check
             raise HTTPException(status_code=500, detail="Could not get or create conversation")

        # 2. Run the agent logic
        ai_response = await run_agent(
            input_message=chat_input.user_message,
            conversation_id=conversation.id,
            db=db
        )

        # 3. Return the response
        return ChatMessageOutput(
            ai_response=ai_response,
            conversation_id=conversation.id
        )

    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        # Log the full exception traceback here in production
        # import traceback
        # traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}

# Add other utility endpoints if needed, e.g., to manage conversations