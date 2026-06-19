"""
Seed the database with initial challenges and badges.
"""
from sqlalchemy.orm import Session
from models import Challenge, Badge
from datetime import datetime, timedelta, timezone


def seed_badges(db: Session):
    existing = db.query(Badge).count()
    if existing > 0:
        return
    badges = [
        Badge(name="Eco Beginner", description="Started tracking your carbon footprint!", icon="🌱",
              category="general", requirement_type="activities_count", requirement_value=1),
        Badge(name="First Week", description="Tracked activities for 7 days!", icon="📅",
              category="general", requirement_type="streak", requirement_value=7),
        Badge(name="Eco Commuter", description="Logged 10 green transport activities!", icon="🚲",
              category="transport", requirement_type="activities_count", requirement_value=10),
        Badge(name="Green Foodie", description="Logged 10 plant-based meals!", icon="🥗",
              category="food", requirement_type="activities_count", requirement_value=10),
        Badge(name="Energy Saver", description="Reduced energy usage for a month!", icon="💡",
              category="energy", requirement_type="carbon_saved", requirement_value=50),
        Badge(name="Zero Waste Hero", description="Recycled or composted 20 times!", icon="♻️",
              category="waste", requirement_type="activities_count", requirement_value=20),
        Badge(name="Climate Hero", description="Reached eco score of 850!", icon="🦸",
              category="general", requirement_type="eco_score", requirement_value=850),
        Badge(name="Carbon Cutter", description="Saved 100kg of CO₂!", icon="✂️",
              category="general", requirement_type="carbon_saved", requirement_value=100),
        Badge(name="Eco Legend", description="Reached eco score of 950!", icon="🌍",
              category="general", requirement_type="eco_score", requirement_value=950),
    ]
    db.add_all(badges)
    db.commit()


def seed_challenges(db: Session):
    existing = db.query(Challenge).count()
    if existing > 0:
        return
    now = datetime.now(timezone.utc)
    challenges = [
        Challenge(title="🚲 Car-Free Week", description="Use only public transport, bike, or walk for 7 days.",
                  category="transport", challenge_type="weekly", target_value=7, reward_points=100,
                  start_date=now, end_date=now + timedelta(days=7), is_active=True),
        Challenge(title="🥗 Meatless Monday x4", description="Go meat-free every Monday this month.",
                  category="food", challenge_type="monthly", target_value=4, reward_points=80,
                  start_date=now, end_date=now + timedelta(days=30), is_active=True),
        Challenge(title="💡 Energy Diet", description="Reduce electricity usage by 20% this week.",
                  category="energy", challenge_type="weekly", target_value=20, reward_points=75,
                  start_date=now, end_date=now + timedelta(days=7), is_active=True),
        Challenge(title="♻️ Zero Waste Week", description="Recycle or compost all waste for 7 days.",
                  category="waste", challenge_type="weekly", target_value=7, reward_points=90,
                  start_date=now, end_date=now + timedelta(days=7), is_active=True),
        Challenge(title="🌍 50kg Challenge", description="Keep total emissions under 50kg this month.",
                  category="general", challenge_type="monthly", target_value=50, reward_points=150,
                  start_date=now, end_date=now + timedelta(days=30), is_active=True),
    ]
    db.add_all(challenges)
    db.commit()


def seed_all(db: Session):
    seed_badges(db)
    seed_challenges(db)
