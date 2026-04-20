"""
Admin Router
Admin-only endpoints for managing complaints and users
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import User, Complaint
from schemas import ComplaintOut, ComplaintUpdate, UserOut
from utils.auth import get_admin_user
from utils.rewards import (
    award_valid_complaint,
    penalize_invalid_complaint,
    award_resolved_complaint,
    add_notification
)

router = APIRouter()


@router.get("/complaints", response_model=List[ComplaintOut])
def get_all_complaints(
    status: Optional[str] = None,
    category: Optional[str] = None,
    is_valid: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all complaints with optional filters.
    Admin only endpoint.
    """
    query = db.query(Complaint)

    # Apply filters if provided
    if status:
        query = query.filter(Complaint.status == status)
    if category:
        query = query.filter(Complaint.category == category)
    if is_valid is not None:
        query = query.filter(Complaint.is_valid == is_valid)

    complaints = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
    return complaints


@router.patch("/complaints/{complaint_id}", response_model=ComplaintOut)
def update_complaint(
    complaint_id: int,
    update_data: ComplaintUpdate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update complaint status, validity, and admin notes.
    Automatically applies reward/penalty based on validity.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    old_status = complaint.status
    old_is_valid = complaint.is_valid

    # Update fields if provided
    if update_data.admin_notes is not None:
        complaint.admin_notes = update_data.admin_notes

    # Handle validity change (reward/penalty)
    if update_data.is_valid is not None and update_data.is_valid != old_is_valid:
        complaint.is_valid = update_data.is_valid

        if update_data.is_valid == True:
            # Award points for valid complaint (only once)
            if not complaint.points_awarded:
                award_valid_complaint(db, complaint)
                complaint.points_awarded = True
        elif update_data.is_valid == False:
            # Penalize for invalid/fake complaint
            penalize_invalid_complaint(db, complaint)

    # Handle status change
    if update_data.status is not None and update_data.status != old_status:
        complaint.status = update_data.status

        if update_data.status == "resolved":
            complaint.resolved_at = datetime.utcnow()
            # Award resolution bonus (only if complaint was valid)
            if complaint.is_valid == True:
                award_resolved_complaint(db, complaint)
            else:
                # Just notify without points if validity unknown
                add_notification(
                    db, complaint.user,
                    f"✅ Your complaint '{complaint.title}' has been resolved.",
                    "info"
                )

        elif update_data.status == "in_progress":
            add_notification(
                db, complaint.user,
                f"🔧 Work has started on your complaint: '{complaint.title}'",
                "info"
            )

    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("/users", response_model=List[UserOut])
def get_all_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all registered users. Admin only."""
    return db.query(User).filter(User.is_admin == False).all()


@router.patch("/users/{user_id}/block")
def toggle_user_block(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Block or unblock a user. Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.is_blocked = not user.is_blocked
    db.commit()

    action = "blocked" if user.is_blocked else "unblocked"
    return {"message": f"User {user.username} has been {action}."}


@router.get("/stats")
def get_dashboard_stats(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get summary statistics for admin dashboard"""
    total = db.query(Complaint).count()
    submitted = db.query(Complaint).filter(Complaint.status == "submitted").count()
    in_progress = db.query(Complaint).filter(Complaint.status == "in_progress").count()
    resolved = db.query(Complaint).filter(Complaint.status == "resolved").count()
    invalid = db.query(Complaint).filter(Complaint.is_valid == False).count()
    total_users = db.query(User).filter(User.is_admin == False).count()
    blocked_users = db.query(User).filter(User.is_blocked == True).count()

    return {
        "total_complaints": total,
        "submitted": submitted,
        "in_progress": in_progress,
        "resolved": resolved,
        "invalid": invalid,
        "total_users": total_users,
        "blocked_users": blocked_users
    }
