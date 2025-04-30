import os
from pydantic_settings import BaseSettings
from pathlib import Path

# Define the base directory of the project
# This assumes config.py is in app/core/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # Groq API Key
    groq_api_key: str = "YOUR_DEFAULT_KEY_IF_NOT_IN_ENV"

    # Database URL
    database_url: str = "sqlite:///./default_chat.db" # Default to SQLite if not set

    # RAG Settings
    embedding_model_name: str = "all-MiniLM-L6-v2"
    vector_store_path: str = str(BASE_DIR / "vector_store_data") # Use absolute path
    faiss_index_file: str = "faiss_index.bin"
    faiss_metadata_file: str = "faiss_metadata.pkl"

    class Config:
        # Load variables from .env file located in the base directory
        env_file = BASE_DIR / ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore' # Ignore extra fields not defined in the model

# Create a single instance of the settings to be imported elsewhere
settings = Settings()

# Ensure vector store directory exists
vector_store_dir = Path(settings.vector_store_path)
vector_store_dir.mkdir(parents=True, exist_ok=True)