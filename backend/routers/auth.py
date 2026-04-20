"""
Authentication Router
Handles user registration and login
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserRegister, UserLogin, Token, UserOut
from utils.auth import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/register", response_model=Token, status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Returns a JWT token so user is logged in immediately after registration.
    """
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=400,
            detail="Username already taken. Please choose another."
        )

    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered. Try logging in."
        )

    # Create new user with hashed password
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        hashed_password=hash_password(user_data.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create JWT token for immediate login
    token = create_access_token({"user_id": new_user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user
    }


@router.post("/register-admin", response_model=Token, status_code=201)
def register_admin(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register an admin account (uses a special endpoint).
    In production, this should be protected by a secret key.
    """
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken.")

    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")

    new_admin = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        hashed_password=hash_password(user_data.password),
        is_admin=True,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    token = create_access_token({"user_id": new_admin.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_admin
    }


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with username and password.
    Returns a JWT token used for all subsequent requests.
    """
    # Find user by username
    user = db.query(User).filter(User.username == credentials.username).first()

    # Verify credentials
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password."
        )

    # Check if blocked
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been blocked due to repeated misuse."
        )

    # Create and return JWT token
    token = create_access_token({"user_id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserOut)
def get_me(db: Session = Depends(get_db), current_user: User = Depends(lambda: None)):
    """Get current user's profile"""
    return current_user
