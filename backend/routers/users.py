"""
Users Router
User profile, leaderboard, and notifications
"""

import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User
from schemas import UserOut, LeaderboardEntry, NotificationOut
from utils.auth import get_current_user
from utils.rewards import get_leaderboard

router = APIRouter()


@router.get("/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get the current user's profile and points"""
    return current_user


@router.get("/leaderboard")
def leaderboard(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get top users ranked by points.
    Everyone can see the leaderboard - it encourages participation!
    """
    return get_leaderboard(db, limit=limit)


@router.get("/notifications")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all notifications for the current user"""
    try:
        notifications = json.loads(current_user.notifications or "[]")
    except:
        notifications = []

    return {"notifications": notifications, "unread_count": len(notifications)}


@router.delete("/notifications")
def clear_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all notifications for the current user"""
    user = db.query(User).filter(User.id == current_user.id).first()
    user.notifications = "[]"
    db.commit()
    return {"message": "Notifications cleared."}
