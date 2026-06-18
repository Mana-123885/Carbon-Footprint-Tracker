"""
Carbon Footprint Tracker — FastAPI Main Application
"""
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

from database import get_db, init_db
from models import User, Activity, Goal, Challenge, UserChallenge, Badge, UserBadge, EcoScoreHistory
from schemas import (
    UserRegister, UserLogin, TokenResponse, ActivityCreate,
    GoalCreate, GoalUpdate, SettingsUpdate, ChatMessage
)
from auth import hash_password, verify_password, create_access_token, get_current_user_id
from carbon_engine import carbon_calculator, EcoScoreEngine, AIEcoCoach
from seed_data import seed_all
from config import APP_NAME, APP_VERSION

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.on_event("startup")
def on_startup():
    init_db()
    db = next(get_db())
    try:
        seed_all(db)
    finally:
        db.close()


@app.get("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": f"{APP_NAME} API v{APP_VERSION}"}

@app.get("/manifest.json")
def serve_manifest():
    path = os.path.join(FRONTEND_DIR, "manifest.json")
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(404, "Manifest not found")

@app.get("/sw.js")
def serve_sw():
    path = os.path.join(FRONTEND_DIR, "sw.js")
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(404, "Service Worker not found")


# ═══════════════════ AUTH ═══════════════════

@app.post("/api/register", response_model=TokenResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "Username already taken")
    user = User(
        username=data.username, email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name or data.username,
        eco_score=500
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Add initial eco score history
    db.add(EcoScoreHistory(user_id=user.id, score=500, change=0, reason="Account created"))
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=_user_dict(user))


@app.post("/api/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=_user_dict(user))


@app.get("/api/me")
def get_me(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return _user_dict(user)


# ═══════════════════ ACTIVITIES ═══════════════════

@app.post("/api/add-activity")
def add_activity(data: ActivityCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        result = carbon_calculator.calculate(data.category, data.activity_type, data.quantity)
    except ValueError as e:
        raise HTTPException(400, str(e))

    activity = Activity(
        user_id=user_id, category=data.category, activity_type=data.activity_type,
        description=data.description or result["label"], quantity=data.quantity,
        unit=result["unit"], carbon_kg=result["carbon_kg"],
        emission_factor=result["emission_factor"]
    )
    db.add(activity)

    # Update eco score
    user = db.query(User).filter(User.id == user_id).first()
    score_change = EcoScoreEngine.calculate_activity_impact(
        result["carbon_kg"], data.category, data.activity_type
    )
    user.eco_score = EcoScoreEngine.clamp_score(user.eco_score + score_change)
    db.add(EcoScoreHistory(
        user_id=user_id, score=user.eco_score,
        change=score_change, reason=f"Added: {result['label']}"
    ))
    if result["carbon_kg"] < 0:
        user.total_carbon_saved_kg += abs(result["carbon_kg"])

    db.commit()
    db.refresh(activity)
    return {
        "activity": _activity_dict(activity),
        "carbon_result": result,
        "eco_score": user.eco_score,
        "score_change": score_change,
        "alternatives": carbon_calculator.get_eco_alternatives(data.category, data.activity_type)
    }


@app.get("/api/activities")
def get_activities(
    days: int = 30,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    activities = (
        db.query(Activity)
        .filter(Activity.user_id == user_id, Activity.date >= since)
        .order_by(Activity.date.desc())
        .all()
    )
    return [_activity_dict(a) for a in activities]


@app.delete("/api/activities/{activity_id}")
def delete_activity(activity_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    act = db.query(Activity).filter(Activity.id == activity_id, Activity.user_id == user_id).first()
    if not act:
        raise HTTPException(404, "Activity not found")
    db.delete(act)
    db.commit()
    return {"message": "Deleted"}


# ═══════════════════ DASHBOARD ═══════════════════

@app.get("/api/get-dashboard")
def get_dashboard(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    now = datetime.now(timezone.utc)

    # This month's activities
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_acts = db.query(Activity).filter(
        Activity.user_id == user_id, Activity.date >= month_start
    ).all()

    # Today's activities
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_acts = db.query(Activity).filter(
        Activity.user_id == user_id, Activity.date >= today_start
    ).all()

    # Week activities
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_acts = db.query(Activity).filter(
        Activity.user_id == user_id, Activity.date >= week_start
    ).all()

    # Category breakdown
    categories = {}
    for a in month_acts:
        categories[a.category] = categories.get(a.category, 0) + a.carbon_kg

    # Daily totals for the week chart
    daily_totals = {}
    for i in range(7):
        d = (now - timedelta(days=6 - i)).strftime("%Y-%m-%d")
        daily_totals[d] = 0
    for a in week_acts:
        d = a.date.strftime("%Y-%m-%d")
        if d in daily_totals:
            daily_totals[d] = round(daily_totals[d] + a.carbon_kg, 2)

    total_month = round(sum(a.carbon_kg for a in month_acts), 2)
    total_today = round(sum(a.carbon_kg for a in today_acts), 2)
    total_week = round(sum(a.carbon_kg for a in week_acts), 2)
    budget = user.monthly_budget_kg
    level = EcoScoreEngine.get_level(user.eco_score)

    # Recent activities
    recent = db.query(Activity).filter(Activity.user_id == user_id).order_by(Activity.date.desc()).limit(5).all()

    return {
        "user": _user_dict(user),
        "eco_score": user.eco_score,
        "level": level,
        "today_carbon_kg": total_today,
        "week_carbon_kg": total_week,
        "month_carbon_kg": total_month,
        "monthly_budget_kg": budget,
        "budget_percent": round(total_month / budget * 100, 1) if budget > 0 else 0,
        "category_breakdown": categories,
        "daily_totals": daily_totals,
        "recent_activities": [_activity_dict(a) for a in recent],
        "activity_count": len(month_acts),
    }


# ═══════════════════ INSIGHTS ═══════════════════

@app.get("/api/get-insights")
def get_insights(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    activities = db.query(Activity).filter(
        Activity.user_id == user_id, Activity.date >= month_start
    ).all()
    acts_data = [{"category": a.category, "carbon_kg": a.carbon_kg, "activity_type": a.activity_type} for a in activities]
    insights = AIEcoCoach.get_insights(acts_data, user.eco_score, user.monthly_budget_kg)

    # Score history
    history = db.query(EcoScoreHistory).filter(
        EcoScoreHistory.user_id == user_id
    ).order_by(EcoScoreHistory.recorded_at.desc()).limit(30).all()

    return {
        **insights,
        "eco_score": user.eco_score,
        "score_history": [{"score": h.score, "change": h.change, "reason": h.reason,
                           "date": h.recorded_at.isoformat()} for h in history],
    }


@app.get("/api/get-eco-score")
def get_eco_score(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    level = EcoScoreEngine.get_level(user.eco_score)
    badges_list = []
    for key, badge in EcoScoreEngine.BADGES.items():
        badges_list.append({
            **badge, "earned": user.eco_score >= badge["threshold"]
        })
    return {"eco_score": user.eco_score, "level": level, "badges": badges_list}


# ═══════════════════ WHAT-IF ═══════════════════

@app.get("/api/what-if")
def what_if_simulation(
    category: str, current_type: str, alt_type: str, quantity: float = 10,
    user_id: int = Depends(get_current_user_id)
):
    try:
        return carbon_calculator.what_if(category, current_type, alt_type, quantity)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ═══════════════════ AI COACH ═══════════════════

@app.post("/api/ai-chat")
def ai_chat(data: ChatMessage, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    total_carbon = db.query(func.coalesce(func.sum(Activity.carbon_kg), 0)).filter(
        Activity.user_id == user_id).scalar()
    user_data = {"eco_score": user.eco_score, "total_carbon": float(total_carbon), "username": user.username}
    response = AIEcoCoach.chat_response(data.message, user_data)
    return {"response": response}


# ═══════════════════ GOALS ═══════════════════

@app.post("/api/goals")
def create_goal(data: GoalCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    goal = Goal(user_id=user_id, title=data.title, description=data.description,
                category=data.category, target_reduction_kg=data.target_reduction_kg)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _goal_dict(goal)


@app.get("/api/goals")
def get_goals(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    goals = db.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.created_at.desc()).all()
    return [_goal_dict(g) for g in goals]


@app.put("/api/goals/{goal_id}")
def update_goal(goal_id: int, data: GoalUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not goal:
        raise HTTPException(404, "Goal not found")
    if data.title is not None:
        goal.title = data.title
    if data.is_completed is not None:
        goal.is_completed = data.is_completed
    db.commit()
    return _goal_dict(goal)


@app.delete("/api/goals/{goal_id}")
def delete_goal(goal_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not goal:
        raise HTTPException(404, "Goal not found")
    db.delete(goal)
    db.commit()
    return {"message": "Goal deleted"}


# ═══════════════════ CHALLENGES ═══════════════════

@app.get("/api/get-challenges")
def get_challenges(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    challenges = db.query(Challenge).filter(Challenge.is_active == True).all()
    user_participations = {
        uc.challenge_id: uc for uc in
        db.query(UserChallenge).filter(UserChallenge.user_id == user_id).all()
    }
    result = []
    for c in challenges:
        uc = user_participations.get(c.id)
        result.append({
            "id": c.id, "title": c.title, "description": c.description,
            "category": c.category, "type": c.challenge_type,
            "target_value": c.target_value, "reward_points": c.reward_points,
            "joined": uc is not None,
            "progress": uc.progress if uc else 0,
            "is_completed": uc.is_completed if uc else False,
        })
    return result


@app.post("/api/join-challenge/{challenge_id}")
def join_challenge(challenge_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(404, "Challenge not found")
    existing = db.query(UserChallenge).filter(
        UserChallenge.user_id == user_id, UserChallenge.challenge_id == challenge_id
    ).first()
    if existing:
        raise HTTPException(400, "Already joined")
    uc = UserChallenge(user_id=user_id, challenge_id=challenge_id)
    db.add(uc)
    db.commit()
    return {"message": "Joined challenge", "challenge": challenge.title}


# ═══════════════════ CATEGORIES ═══════════════════

@app.get("/api/categories")
def get_categories():
    return carbon_calculator.get_categories()


# ═══════════════════ SETTINGS ═══════════════════

@app.put("/api/settings")
def update_settings(data: SettingsUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if data.theme is not None:
        user.theme = data.theme
    if data.monthly_budget_kg is not None:
        user.monthly_budget_kg = data.monthly_budget_kg
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.notification_enabled is not None:
        user.notification_enabled = data.notification_enabled
    db.commit()
    return _user_dict(user)


# ═══════════════════ EDUCATION ═══════════════════

@app.get("/api/education")
def get_education():
    return {
        "cards": [
            {"id": 1, "icon": "🌍", "title": "What is a Carbon Footprint?",
             "content": "A carbon footprint is the total amount of greenhouse gases produced directly and indirectly by human activities, measured in CO₂ equivalents. The global average is about 4 tonnes per person per year."},
            {"id": 2, "icon": "🚗", "title": "Transport & Emissions",
             "content": "Transport accounts for ~29% of global emissions. A single transatlantic flight can produce 1.6 tonnes of CO₂. Switching to public transit can reduce your transport footprint by 65%."},
            {"id": 3, "icon": "🍽️", "title": "Food's Climate Impact",
             "content": "Food systems produce 26% of global emissions. Beef produces 27kg CO₂ per kg — 20x more than vegetables. Reducing meat consumption is one of the most impactful individual actions."},
            {"id": 4, "icon": "⚡", "title": "Energy at Home",
             "content": "Household energy use accounts for ~20% of emissions. LED bulbs use 75% less energy than incandescent. Smart thermostats can reduce heating emissions by 10-15%."},
            {"id": 5, "icon": "♻️", "title": "Waste & Circular Economy",
             "content": "Landfills produce methane, a greenhouse gas 80x more potent than CO₂. Recycling one tonne of paper saves 1.4 tonnes of CO₂. Composting can divert 30% of household waste."},
            {"id": 6, "icon": "🌳", "title": "Carbon Offsets & Trees",
             "content": "One mature tree absorbs about 22kg CO₂ per year. Carbon offset programs fund renewable energy, reforestation, and community projects. Offsets work best alongside emission reduction."},
            {"id": 7, "icon": "💧", "title": "Water & Carbon",
             "content": "Heating water accounts for 17% of home energy use. A 5-minute shower uses 40L of water and produces ~0.5kg CO₂. Cold water washing saves 0.3kg CO₂ per load."},
            {"id": 8, "icon": "🏭", "title": "Industry & You",
             "content": "While industry produces 21% of global emissions, consumer choices drive industrial output. Choosing sustainable products and reducing consumption creates ripple effects throughout supply chains."},
        ],
        "facts": [
            "If food waste were a country, it would be the 3rd largest emitter after China and the USA.",
            "The internet produces ~3.7% of global carbon emissions — similar to the airline industry.",
            "A single email produces about 4g of CO₂. An email with attachment: 50g.",
            "Producing one smartphone generates ~70kg of CO₂.",
            "The fashion industry produces 10% of global carbon emissions.",
        ]
    }


# ═══════════════════ HELPERS ═══════════════════

def _user_dict(u):
    return {
        "id": u.id, "username": u.username, "email": u.email,
        "full_name": u.full_name, "theme": u.theme,
        "monthly_budget_kg": u.monthly_budget_kg, "eco_score": u.eco_score,
        "total_carbon_saved_kg": u.total_carbon_saved_kg,
        "notification_enabled": u.notification_enabled,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }

def _activity_dict(a):
    return {
        "id": a.id, "category": a.category, "activity_type": a.activity_type,
        "description": a.description, "quantity": a.quantity, "unit": a.unit,
        "carbon_kg": a.carbon_kg, "emission_factor": a.emission_factor,
        "date": a.date.isoformat() if a.date else None,
    }

def _goal_dict(g):
    return {
        "id": g.id, "title": g.title, "description": g.description,
        "category": g.category, "target_reduction_kg": g.target_reduction_kg,
        "current_progress_kg": g.current_progress_kg,
        "is_completed": g.is_completed,
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
