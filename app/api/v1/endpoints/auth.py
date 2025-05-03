from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # Use form data for login
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db import crud, models
from app.db.database import get_db
from app.schemas import User, UserCreate, Token
from app.core import security
from app.core.config import settings
from app.core.deps import get_current_active_user # Import the dependency function

router = APIRouter()

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user."""
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    # You might add email check here too if email is required/unique
    created_user = crud.create_user(db=db, user=user)
    return created_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends() # Inject form data
):
    """Authenticates user and returns JWT token."""
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = security.create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Optional: Endpoint to test authentication
@router.get("/users/me", response_model=User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)): 
    """Gets the current logged-in user's information."""
    return current_user
