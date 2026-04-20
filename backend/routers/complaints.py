"""
Complaints Router
Handles creating, viewing, and managing complaints
"""

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import User, Complaint
from schemas import ComplaintOut
from utils.auth import get_current_user

router = APIRouter()

# Allowed image file types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE_MB = 10


def save_image(file: UploadFile) -> str:
    """
    Save uploaded image to disk and return the file path.
    Uses UUID to prevent filename conflicts.
    """
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload JPG, PNG, or WebP image."
        )

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join("uploads", filename)

    # Save file to disk
    with open(filepath, "wb") as f:
        content = file.file.read()
        # Check file size
        if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB."
            )
        f.write(content)

    return f"/uploads/{filename}"


@router.post("/", response_model=ComplaintOut, status_code=201)
async def create_complaint(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    location_name: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a new complaint with optional photo.
    Uses multipart form data to support image upload.
    """
    # Save image if provided
    image_path = None
    if image and image.filename:
        image_path = save_image(image)

    # Validate category
    valid_categories = ["road", "water", "electricity", "sanitation", "others"]
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Category must be one of: {valid_categories}")

    # Create complaint record
    complaint = Complaint(
        user_id=current_user.id,
        title=title,
        description=description,
        category=category,
        image_path=image_path,
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return complaint


@router.get("/my", response_model=List[ComplaintOut])
def get_my_complaints(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all complaints submitted by the current logged-in user"""
    complaints = (
        db.query(Complaint)
        .filter(Complaint.user_id == current_user.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    return complaints


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single complaint by ID"""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    # Users can only view their own complaints (admins can view all - handled in admin router)
    if not current_user.is_admin and complaint.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    return complaint
