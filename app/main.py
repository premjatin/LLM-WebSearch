from fastapi import FastAPI, Depends, HTTPException, APIRouter # Added APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# --- Database Imports ---
from app.db.database import SessionLocal, engine, init_db, get_db
from app.db import models, crud

# --- Schema Imports ---
from app.schemas import ChatMessageInput, ChatMessageOutput, User # Added User

# --- Agent Imports ---
from app.agent.agent_executor import run_agent

# --- Auth Imports ---
from app.core.deps import get_current_active_user # Import dependency
from app.api.v1.endpoints import auth # Import the auth router

# --- Config Imports (Optional here) ---
# from app.core.config import settings

# --- Create DB Tables (Manage with migrations later) ---
# try:
#     print("Attempting to create database tables...")
#     models.Base.metadata.create_all(bind=engine)
#     print("Database tables checked/created.")
# except Exception as e:
#     print(f"Error creating database tables: {e}")
#     # Consider raising error or logging more severely

app = FastAPI(title="LangGraph RAG Agent API")

# --- CORS Middleware ---
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
api_router_v1 = APIRouter(prefix="/api/v1")

# Include the authentication router
api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# --- Protected Chat Endpoint (Now under /api/v1) ---
@api_router_v1.post("/chat", response_model=ChatMessageOutput, tags=["Chat"])
async def chat_endpoint(
    chat_input: ChatMessageInput,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user) # PROTECTED!
):
    """Handles chat interactions for the authenticated user."""
    try:
        # 1. Get or create conversation FOR THE CURRENT USER
        conversation = crud.get_or_create_conversation(
            db, user_id=current_user.id, conversation_id=chat_input.conversation_id
        )
        if not conversation:
             raise HTTPException(status_code=500, detail="Could not get or create conversation")

        # 2. Run agent logic, passing user_id for context if needed by agent later
        # Note: run_agent itself doesn't use user_id directly now, but uses it via conversation_id checks in crud
        ai_response = await run_agent(
            input_message=chat_input.user_message,
            conversation_id=conversation.id,
            user_id=current_user.id, # Pass the authenticated user's ID
            db=db
        )

        # 3. Return response
        return ChatMessageOutput(
            ai_response=ai_response,
            conversation_id=conversation.id
        )

    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        # import traceback; traceback.print_exc() # Uncomment for detailed trace
        raise HTTPException(status_code=500, detail=f"An internal server error occurred.")


# --- Include the main API router in the app ---
app.include_router(api_router_v1)


# --- Health Check (Optional, kept at root) ---
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}


# --- Startup Event (Optional) ---
@app.on_event("startup")
async def startup_event():
    print("Application startup...")
    # Create tables on startup if they don't exist (dev convenience)
    try:
        print("Attempting to create database tables...")
        models.Base.metadata.create_all(bind=engine)
        print("Database tables checked/created.")
    except Exception as e:
        print(f"Database connection/table creation error: {e}")

    from app.rag.vector_store import vector_store
    if not vector_store.is_ready(): print("WARNING: RAG vector store not loaded/empty.")
    else: print("RAG vector store seems ready.")
    print("Startup complete.")