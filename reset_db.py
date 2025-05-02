import sys
from pathlib import Path

# Add the app directory to the Python path to find modules
sys.path.append(str(Path(__file__).resolve().parent / "app"))

from app.db.database import engine, Base
from app.db import models # Import models to ensure they are registered with Base

print("About to drop and recreate all tables...")
confirm = input("Are you sure? This will delete ALL data! (yes/no): ")

if confirm.lower() == 'yes':
    try:
        print("Dropping tables...")
        # Drop tables in reverse order of creation (or handle dependencies)
        # Base.metadata.drop_all binds to specific tables, dropping individually might be safer
        # Or ensure models are loaded correctly for drop_all dependencies
        Base.metadata.drop_all(engine) # This should handle dependencies if models are loaded
        print("Tables dropped.")

        print("Creating tables...")
        Base.metadata.create_all(engine)
        print("Tables created successfully based on current models.")
    except Exception as e:
        print(f"An error occurred: {e}")
else:
    print("Database reset cancelled.")