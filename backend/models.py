"""
SQLAlchemy ORM models for the Carbon Footprint Tracker.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), default="")
    avatar_url = Column(String(255), default="")
    
    # Preferences
    theme = Column(String(10), default="light")  # light or dark
    monthly_budget_kg = Column(Float, default=300.0)
    notification_enabled = Column(Boolean, default=True)
    
    # Eco Score
    eco_score = Column(Integer, default=500)
    total_carbon_saved_kg = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")
    eco_score_history = relationship("EcoScoreHistory", back_populates="user", cascade="all, delete-orphan")
    challenge_participations = relationship("UserChallenge", back_populates="user", cascade="all, delete-orphan")


class Activity(Base):
    """User carbon-emitting activity model."""
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Category: transport, food, energy, waste
    category = Column(String(20), nullable=False, index=True)
    # Sub-type within category (e.g., "car", "bus", "beef", "electricity")
    activity_type = Column(String(50), nullable=False)
    
    # Activity details
    description = Column(String(255), default="")
    quantity = Column(Float, nullable=False)  # e.g., km, kWh, kg
    unit = Column(String(20), nullable=False)  # km, kWh, kg, liters
    
    # Carbon calculation results
    carbon_kg = Column(Float, nullable=False)  # kg CO2e
    emission_factor = Column(Float, nullable=False)  # kg CO2e per unit
    
    # Metadata
    date = Column(DateTime, default=utcnow, index=True)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    user = relationship("User", back_populates="activities")


class Goal(Base):
    """User carbon reduction goal."""
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String(100), nullable=False)
    description = Column(Text, default="")
    category = Column(String(20), default="general")  # transport, food, energy, waste, general
    
    target_reduction_kg = Column(Float, nullable=False)  # target kg CO2e reduction
    current_progress_kg = Column(Float, default=0.0)
    
    start_date = Column(DateTime, default=utcnow)
    end_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="goals")


class Challenge(Base):
    """Weekly/monthly eco challenges."""
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(20), default="general")
    
    challenge_type = Column(String(20), default="weekly")  # weekly, monthly
    target_value = Column(Float, nullable=False)  # e.g., reduce by 10kg
    reward_points = Column(Integer, default=50)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=True)
    
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=utcnow)

    participants = relationship("UserChallenge", back_populates="challenge")
    badge = relationship("Badge")


class UserChallenge(Base):
    """User participation in challenges."""
    __tablename__ = "user_challenges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    
    progress = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    
    joined_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="challenge_participations")
    challenge = relationship("Challenge", back_populates="participants")


class Badge(Base):
    """Achievement badges."""
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=False)
    icon = Column(String(50), default="🏅")  # emoji icon
    category = Column(String(20), default="general")
    
    # Requirements
    requirement_type = Column(String(30), nullable=False)  # eco_score, activities_count, carbon_saved, streak
    requirement_value = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=utcnow)


class UserBadge(Base):
    """Badges earned by users."""
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="badges")
    badge = relationship("Badge")


class EcoScoreHistory(Base):
    """Track eco score changes over time."""
    __tablename__ = "eco_score_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    change = Column(Integer, default=0)
    reason = Column(String(255), default="")
    recorded_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="eco_score_history")
