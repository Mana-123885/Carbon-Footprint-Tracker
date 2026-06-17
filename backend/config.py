"""
Application configuration settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./carbon_tracker.db")

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "eco-tracker-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# App
APP_NAME = "Carbon Footprint Tracker"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# AI Coach (optional)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Carbon Budget defaults
DEFAULT_MONTHLY_BUDGET_KG = 300  # kg CO2e per month (global avg ~333kg)
