"""
Reward & Penalty System
Handles points, badges, and user blocking logic
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session

from models import User, Complaint


# ─── Points Configuration ───
POINTS_VALID_COMPLAINT = 10       # Complaint marked as valid
POINTS_COMPLAINT_RESOLVED = 20    # Complaint gets resolved
POINTS_BONUS_DUPLICATE = 5        # Bonus when multiple users report same area
POINTS_INVALID_PENALTY = -10      # Penalty for fake/invalid complaint
MAX_INVALID_BEFORE_BLOCK = 3      # Block user after this many invalid complaints


# ─── Badge Thresholds ───
BADGE_LEVELS = [
    (0,   "Beginner"),
    (30,  "Active Citizen"),
    (100, "Top Reporter"),
    (200, "Village Guardian"),
]


def calculate_badge(points: int) -> str:
    """Determine badge level based on points"""
    badge = "Beginner"
    for threshold, name in BADGE_LEVELS:
        if points >= threshold:
            badge = name
    return badge


def add_notification(db: Session, user: User, message: str, notif_type: str = "info"):
    """Add a notification to user's notification list"""
    try:
        notifications = json.loads(user.notifications or "[]")
    except:
        notifications = []

    notifications.insert(0, {  # Add newest first
        "message": message,
        "type": notif_type,
        "created_at": datetime.utcnow().isoformat()
    })

    # Keep only last 20 notifications
    notifications = notifications[:20]
    user.notifications = json.dumps(notifications)
    db.commit()


def award_valid_complaint(db: Session, complaint: Complaint):
    """
    Award points when admin marks complaint as VALID.
    +10 points to the reporter.
    """
    user = complaint.user
    user.points += POINTS_VALID_COMPLAINT
    user.badge = calculate_badge(user.points)
    db.commit()

    add_notification(
        db, user,
        f"🏅 Your complaint '{complaint.title}' was verified! +{POINTS_VALID_COMPLAINT} points earned.",
        "success"
    )


def penalize_invalid_complaint(db: Session, complaint: Complaint):
    """
    Penalize user when complaint is marked as INVALID (fake/false report).
    -10 points, and block if repeated offender.
    """
    user = complaint.user
    user.points = max(0, user.points + POINTS_INVALID_PENALTY)  # Never go below 0
    user.invalid_complaint_count += 1
    user.badge = calculate_badge(user.points)

    # Block user after too many fake complaints
    if user.invalid_complaint_count >= MAX_INVALID_BEFORE_BLOCK:
        user.is_blocked = True
        add_notification(
            db, user,
            f"🚫 Your account has been blocked due to {MAX_INVALID_BEFORE_BLOCK} invalid complaints.",
            "warning"
        )
    else:
        remaining = MAX_INVALID_BEFORE_BLOCK - user.invalid_complaint_count
        add_notification(
            db, user,
            f"⚠️ Complaint '{complaint.title}' was invalid. -{abs(POINTS_INVALID_PENALTY)} points. "
            f"Warning: {remaining} more invalid reports may block your account.",
            "warning"
        )

    db.commit()


def award_resolved_complaint(db: Session, complaint: Complaint):
    """
    Award bonus points when complaint is RESOLVED.
    +20 points to the reporter.
    """
    user = complaint.user
    user.points += POINTS_COMPLAINT_RESOLVED
    user.badge = calculate_badge(user.points)
    db.commit()

    add_notification(
        db, user,
        f"🎉 Your complaint '{complaint.title}' has been RESOLVED! +{POINTS_COMPLAINT_RESOLVED} points earned.",
        "success"
    )


def get_leaderboard(db: Session, limit: int = 10):
    """Get top users by points for the leaderboard"""
    users = (
        db.query(User)
        .filter(User.is_admin == False, User.is_blocked == False)
        .order_by(User.points.desc())
        .limit(limit)
        .all()
    )

    leaderboard = []
    for rank, user in enumerate(users, start=1):
        complaint_count = len([c for c in user.complaints if c.is_valid == True])
        leaderboard.append({
            "rank": rank,
            "username": user.username,
            "full_name": user.full_name,
            "points": user.points,
            "badge": user.badge,
            "complaint_count": complaint_count
        })

    return leaderboard
