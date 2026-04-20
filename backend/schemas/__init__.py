"""
Pydantic Schemas
Defines the shape of data coming in (requests) and going out (responses)
Think of these as "blueprints" that validate data automatically
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────
# AUTH SCHEMAS
# ─────────────────────────────────────────

class UserRegister(BaseModel):
    """Data needed to register a new user"""
    username: str
    email: str
    full_name: str
    phone: Optional[str] = None
    password: str


class UserLogin(BaseModel):
    """Data needed to log in"""
    username: str
    password: str


class UserOut(BaseModel):
    """User data we send back (never send password!)"""
    id: int
    username: str
    email: str
    full_name: str
    phone: Optional[str]
    points: int
    badge: str
    is_admin: bool
    is_blocked: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Allows reading from SQLAlchemy models


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str
    user: UserOut


# ─────────────────────────────────────────
# COMPLAINT SCHEMAS
# ─────────────────────────────────────────

class ComplaintCreate(BaseModel):
    """Data needed to create a new complaint"""
    title: str
    description: str
    category: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None


class ComplaintOut(BaseModel):
    """Complaint data sent back to user"""
    id: int
    user_id: int
    title: str
    description: str
    category: str
    image_path: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    location_name: Optional[str]
    status: str
    is_valid: Optional[bool]
    created_at: datetime
    resolved_at: Optional[datetime]
    admin_notes: Optional[str]
    user: Optional[UserOut] = None

    class Config:
        from_attributes = True


class ComplaintUpdate(BaseModel):
    """Admin uses this to update complaint status"""
    status: Optional[str] = None
    is_valid: Optional[bool] = None
    admin_notes: Optional[str] = None


# ─────────────────────────────────────────
# LEADERBOARD & NOTIFICATIONS
# ─────────────────────────────────────────

class LeaderboardEntry(BaseModel):
    """Single entry in the leaderboard"""
    rank: int
    username: str
    full_name: str
    points: int
    badge: str
    complaint_count: int


class NotificationOut(BaseModel):
    """A notification message for the user"""
    message: str
    type: str  # "success", "warning", "info"
    created_at: str
