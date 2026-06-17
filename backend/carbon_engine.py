"""
Carbon emission factors dataset and calculation engine.
Sources: IPCC AR6, EPA, DEFRA 2024.
"""

EMISSION_FACTORS = {
    "transport": {
        "car_petrol": {"factor": 0.192, "unit": "km", "label": "Car (Petrol)", "icon": "🚗"},
        "car_diesel": {"factor": 0.171, "unit": "km", "label": "Car (Diesel)", "icon": "🚗"},
        "car_electric": {"factor": 0.053, "unit": "km", "label": "Electric Car", "icon": "⚡"},
        "car_hybrid": {"factor": 0.120, "unit": "km", "label": "Hybrid Car", "icon": "🔋"},
        "bus": {"factor": 0.089, "unit": "km", "label": "Bus", "icon": "🚌"},
        "train": {"factor": 0.041, "unit": "km", "label": "Train", "icon": "🚆"},
        "metro": {"factor": 0.033, "unit": "km", "label": "Metro/Subway", "icon": "🚇"},
        "bicycle": {"factor": 0.0, "unit": "km", "label": "Bicycle", "icon": "🚲"},
        "walking": {"factor": 0.0, "unit": "km", "label": "Walking", "icon": "🚶"},
        "motorcycle": {"factor": 0.113, "unit": "km", "label": "Motorcycle", "icon": "🏍️"},
        "flight_short": {"factor": 0.255, "unit": "km", "label": "Short Flight", "icon": "✈️"},
        "flight_long": {"factor": 0.195, "unit": "km", "label": "Long Flight", "icon": "✈️"},
        "taxi": {"factor": 0.210, "unit": "km", "label": "Taxi", "icon": "🚕"},
    },
    "food": {
        "beef": {"factor": 27.0, "unit": "kg", "label": "Beef", "icon": "🥩"},
        "lamb": {"factor": 39.2, "unit": "kg", "label": "Lamb", "icon": "🍖"},
        "pork": {"factor": 12.1, "unit": "kg", "label": "Pork", "icon": "🥓"},
        "chicken": {"factor": 6.9, "unit": "kg", "label": "Chicken", "icon": "🍗"},
        "fish": {"factor": 6.1, "unit": "kg", "label": "Fish", "icon": "🐟"},
        "eggs": {"factor": 4.8, "unit": "kg", "label": "Eggs", "icon": "🥚"},
        "dairy_milk": {"factor": 3.2, "unit": "liters", "label": "Dairy Milk", "icon": "🥛"},
        "cheese": {"factor": 13.5, "unit": "kg", "label": "Cheese", "icon": "🧀"},
        "rice": {"factor": 4.0, "unit": "kg", "label": "Rice", "icon": "🍚"},
        "vegetables": {"factor": 2.0, "unit": "kg", "label": "Vegetables", "icon": "🥬"},
        "fruits": {"factor": 1.1, "unit": "kg", "label": "Fruits", "icon": "🍎"},
        "plant_milk": {"factor": 0.9, "unit": "liters", "label": "Plant Milk", "icon": "🌱"},
        "tofu": {"factor": 3.0, "unit": "kg", "label": "Tofu", "icon": "🫘"},
    },
    "energy": {
        "electricity": {"factor": 0.42, "unit": "kWh", "label": "Electricity", "icon": "💡"},
        "electricity_renewable": {"factor": 0.05, "unit": "kWh", "label": "Renewable", "icon": "🌞"},
        "natural_gas": {"factor": 2.0, "unit": "m³", "label": "Natural Gas", "icon": "🔥"},
        "heating_oil": {"factor": 2.54, "unit": "liters", "label": "Heating Oil", "icon": "🛢️"},
        "lpg": {"factor": 1.51, "unit": "liters", "label": "LPG", "icon": "⛽"},
        "solar_panel": {"factor": 0.0, "unit": "kWh", "label": "Solar Panel", "icon": "☀️"},
        "air_conditioning": {"factor": 0.63, "unit": "hours", "label": "AC", "icon": "❄️"},
    },
    "waste": {
        "general_waste": {"factor": 0.59, "unit": "kg", "label": "General Waste", "icon": "🗑️"},
        "recycling_paper": {"factor": -0.18, "unit": "kg", "label": "Paper Recycling", "icon": "📰"},
        "recycling_plastic": {"factor": -0.25, "unit": "kg", "label": "Plastic Recycling", "icon": "♻️"},
        "recycling_glass": {"factor": -0.31, "unit": "kg", "label": "Glass Recycling", "icon": "🫙"},
        "composting": {"factor": -0.10, "unit": "kg", "label": "Composting", "icon": "🌿"},
        "food_waste": {"factor": 0.70, "unit": "kg", "label": "Food Waste", "icon": "🍌"},
        "e_waste": {"factor": 2.80, "unit": "kg", "label": "E-Waste", "icon": "📱"},
    },
}


class CarbonCalculator:
    def __init__(self):
        self.factors = EMISSION_FACTORS

    def calculate(self, category, activity_type, quantity):
        if category not in self.factors:
            raise ValueError(f"Unknown category: {category}")
        if activity_type not in self.factors[category]:
            raise ValueError(f"Unknown activity: {activity_type}")
        data = self.factors[category][activity_type]
        carbon_kg = round(quantity * data["factor"], 4)
        return {
            "category": category, "activity_type": activity_type,
            "quantity": quantity, "unit": data["unit"],
            "emission_factor": data["factor"], "carbon_kg": carbon_kg,
            "label": data["label"], "icon": data["icon"],
        }

    def get_categories(self):
        result = {}
        for cat, acts in self.factors.items():
            result[cat] = {
                k: {"label": d["label"], "unit": d["unit"], "factor": d["factor"], "icon": d["icon"]}
                for k, d in acts.items()
            }
        return result

    def get_eco_alternatives(self, category, activity_type):
        if category not in self.factors or activity_type not in self.factors[category]:
            return []
        cur = self.factors[category][activity_type]["factor"]
        alts = []
        for k, d in self.factors[category].items():
            if k != activity_type and d["factor"] < cur:
                s = cur - d["factor"]
                alts.append({
                    "activity_type": k, "label": d["label"], "icon": d["icon"],
                    "factor": d["factor"], "savings_per_unit": round(s, 4),
                    "savings_percent": round((s / cur) * 100, 1) if cur > 0 else 0,
                })
        alts.sort(key=lambda x: x["savings_per_unit"], reverse=True)
        return alts

    def what_if(self, category, current_type, alt_type, quantity):
        cur = self.calculate(category, current_type, quantity)
        alt = self.calculate(category, alt_type, quantity)
        sav = round(cur["carbon_kg"] - alt["carbon_kg"], 4)
        pct = round((sav / cur["carbon_kg"]) * 100, 1) if cur["carbon_kg"] > 0 else 0
        return {
            "current": cur, "alternative": alt, "savings_kg": sav,
            "savings_percent": pct, "annual_savings_kg": round(sav * 365, 2),
            "equivalent_trees": round(sav * 365 / 22, 1),
        }


class EcoScoreEngine:
    BASE_SCORE = 500
    BADGES = {
        "eco_beginner": {"threshold": 100, "name": "Eco Beginner", "icon": "🌱"},
        "carbon_conscious": {"threshold": 300, "name": "Carbon Conscious", "icon": "🌿"},
        "eco_commuter": {"threshold": 500, "name": "Eco Commuter", "icon": "🚲"},
        "green_foodie": {"threshold": 600, "name": "Green Foodie", "icon": "🥗"},
        "energy_saver": {"threshold": 700, "name": "Energy Saver", "icon": "💡"},
        "climate_hero": {"threshold": 850, "name": "Climate Hero", "icon": "🦸"},
        "eco_legend": {"threshold": 950, "name": "Eco Legend", "icon": "🌍"},
    }

    @classmethod
    def calculate_activity_impact(cls, carbon_kg, category, activity_type):
        if category == "waste" and carbon_kg <= 0:
            return 8
        elif carbon_kg == 0:
            return 10
        elif carbon_kg < 1.0:
            return 5
        elif carbon_kg < 5.0:
            return -3
        else:
            return -6

    @classmethod
    def clamp_score(cls, score):
        return max(0, min(1000, score))

    @classmethod
    def get_level(cls, score):
        current = {"name": "Newcomer", "icon": "🌰"}
        for b in cls.BADGES.values():
            if score >= b["threshold"]:
                current = b
        return current


class AIEcoCoach:
    TIPS = {
        "transport": [
            "🚲 Biking for short trips saves ~1.5kg CO₂ per trip!",
            "🚆 Trains produce 85% less CO₂ than flights.",
            "🚗 Carpooling halves your transport emissions.",
            "⚡ EVs produce 60-70% less CO₂ than petrol cars.",
            "🏠 WFH 2 days/week cuts transport emissions ~40%.",
        ],
        "food": [
            "🥗 Plant meals produce 50-80% less emissions.",
            "🌱 Oat milk = 80% less CO₂ than dairy milk.",
            "🍎 Local seasonal produce cuts food transport CO₂ by 50%.",
            "🍌 Halving food waste saves ~300kg CO₂/year.",
        ],
        "energy": [
            "💡 LEDs save 80% energy vs incandescent bulbs.",
            "🌡️ 1°C lower thermostat = ~10% less heating emissions.",
            "☀️ Solar panels offset 1,000-2,000 kg CO₂/year.",
            "🔌 Unplug standby devices to save 5-10% electricity.",
        ],
        "waste": [
            "♻️ Recycling 1 can saves energy for 3 hours of TV.",
            "🌿 Composting reduces landfill methane.",
            "📱 Using your phone 1 extra year saves ~70kg CO₂.",
            "👕 Second-hand clothes save 5-10kg CO₂ per item.",
        ],
    }

    @classmethod
    def get_insights(cls, activities, eco_score, monthly_budget):
        if not activities:
            return {
                "summary": "Start tracking to get personalized insights!",
                "tips": [cls.TIPS["transport"][0], cls.TIPS["food"][0], cls.TIPS["energy"][0]],
                "category_breakdown": {}, "top_emitter": None,
            }
        cat_totals = {}
        for a in activities:
            c = a.get("category", "general")
            cat_totals[c] = cat_totals.get(c, 0) + a.get("carbon_kg", 0)
        total = sum(cat_totals.values())
        top = max(cat_totals, key=cat_totals.get) if cat_totals else None
        pct = round(total / monthly_budget * 100, 1) if monthly_budget > 0 else 0
        if pct > 80:
            summary = f"⚠️ At {pct}% of budget! Focus on {top}."
        elif pct > 50:
            summary = f"📊 {pct}% of budget used. Watch {top}."
        else:
            summary = f"🌟 Only {pct}% used. Great work!"
        tips = cls.TIPS.get(top, [])[:2]
        for c in ["transport", "food", "energy", "waste"]:
            if c != top:
                tips.append(cls.TIPS[c][0])
            if len(tips) >= 4:
                break
        return {
            "summary": summary, "tips": tips,
            "category_breakdown": {k: round(v, 2) for k, v in cat_totals.items()},
            "total_carbon_kg": round(total, 2), "budget_percent": pct,
            "top_emitter": top,
        }

    @classmethod
    def chat_response(cls, message, user_data):
        ml = message.lower()
        eco_score = user_data.get("eco_score", 500)
        if any(w in ml for w in ["hello", "hi", "hey"]):
            lv = EcoScoreEngine.get_level(eco_score)
            return f"Hey there, {lv['icon']} {lv['name']}! Your eco score is {eco_score}/1000. Ask me anything about reducing your carbon footprint!"
        if any(w in ml for w in ["carbon", "emission", "co2", "footprint"]):
            return "📊 The average person emits ~4,000 kg CO₂/year. Quick wins:\n• 🚲 Bike for short trips\n• 🥗 Try meat-free days\n• 💡 Switch to LEDs\n• ♻️ Recycle regularly"
        if any(w in ml for w in ["transport", "car", "drive", "fly", "bus", "train"]):
            import random
            return "🚗 Transport Tips:\n" + "\n".join(f"• {t}" for t in random.sample(cls.TIPS["transport"], 3))
        if any(w in ml for w in ["food", "eat", "diet", "meat", "vegan"]):
            import random
            return "🍽️ Food Tips:\n" + "\n".join(f"• {t}" for t in random.sample(cls.TIPS["food"], 3))
        if any(w in ml for w in ["energy", "electric", "power", "solar"]):
            import random
            return "⚡ Energy Tips:\n" + "\n".join(f"• {t}" for t in random.sample(cls.TIPS["energy"], 3))
        if any(w in ml for w in ["waste", "recycle", "compost"]):
            import random
            return "♻️ Waste Tips:\n" + "\n".join(f"• {t}" for t in random.sample(cls.TIPS["waste"], 3))
        if any(w in ml for w in ["score", "level", "badge", "rank"]):
            lv = EcoScoreEngine.get_level(eco_score)
            return f"🏆 Eco Score: {eco_score}/1000\nLevel: {lv['icon']} {lv['name']}\nKeep logging green activities!"
        return "🌿 I can help with:\n• 🚗 Transport tips\n• 🍽️ Food advice\n• ⚡ Energy saving\n• ♻️ Waste reduction\n• 📊 Your eco score\n\nJust ask!"


carbon_calculator = CarbonCalculator()
eco_score_engine = EcoScoreEngine()
ai_coach = AIEcoCoach()
