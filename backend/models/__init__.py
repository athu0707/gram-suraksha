"""
Database Models
Defines the structure of our database tables using SQLAlchemy ORM
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class BadgeLevel(str, enum.Enum):
    """User badge levels based on points earned"""
    BEGINNER = "Beginner"
    ACTIVE_CITIZEN = "Active Citizen"
    TOP_REPORTER = "Top Reporter"
    GUARDIAN = "Village Guardian"


class ComplaintStatus(str, enum.Enum):
    """Possible statuses for a complaint"""
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class ComplaintCategory(str, enum.Enum):
    """Categories of issues that can be reported"""
    ROAD = "road"
    WATER = "water"
    ELECTRICITY = "electricity"
    SANITATION = "sanitation"
    OTHERS = "others"


class User(Base):
    """
    User table - stores villager and admin accounts
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=True)
    hashed_password = Column(String(200), nullable=False)

    # Reward system fields
    points = Column(Integer, default=0)
    badge = Column(String(50), default=BadgeLevel.BEGINNER)

    # Account status
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)  # Block users who abuse the system
    invalid_complaint_count = Column(Integer, default=0)  # Track fake complaints

    # Notifications (stored as JSON string)
    notifications = Column(Text, default="[]")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship: one user can have many complaints
    complaints = relationship("Complaint", back_populates="user")


class Complaint(Base):
    """
    Complaint table - stores all reported issues
    """
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Issue details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # road, water, electricity, etc.

    # Photo of the issue
    image_path = Column(String(300), nullable=True)

    # GPS location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(200), nullable=True)  # Human-readable address

    # Status tracking
    status = Column(String(50), default=ComplaintStatus.SUBMITTED)
    is_valid = Column(Boolean, nullable=True)  # None = not reviewed, True/False = admin decision

    # Reward tracking
    points_awarded = Column(Boolean, default=False)  # Prevent double-awarding points

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Admin notes
    admin_notes = Column(Text, nullable=True)

    # Relationship: many complaints belong to one user
    user = relationship("User", back_populates="complaints")
