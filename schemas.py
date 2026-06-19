"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ── Auth ──
class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=6)
    full_name: Optional[str] = ""

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserProfile(BaseModel):
    username: str
    email: str
    full_name: str
    theme: str
    monthly_budget_kg: float
    eco_score: int
    total_carbon_saved_kg: float
    created_at: datetime

# ── Activity ──
class ActivityCreate(BaseModel):
    category: str
    activity_type: str
    quantity: float = Field(gt=0)
    description: Optional[str] = ""

class ActivityResponse(BaseModel):
    id: int
    category: str
    activity_type: str
    quantity: float
    unit: str
    carbon_kg: float
    emission_factor: float
    description: str
    date: datetime

# ── Goals ──
class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    category: Optional[str] = "general"
    target_reduction_kg: float = Field(gt=0)

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    is_completed: Optional[bool] = None

# ── Settings ──
class SettingsUpdate(BaseModel):
    theme: Optional[str] = None
    monthly_budget_kg: Optional[float] = None
    full_name: Optional[str] = None
    notification_enabled: Optional[bool] = None

# ── AI Chat ──
class ChatMessage(BaseModel):
    message: str
