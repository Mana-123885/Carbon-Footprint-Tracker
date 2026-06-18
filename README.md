# EcoTrack 🌍

EcoTrack is an AI-powered Carbon Footprint Tracking application designed to help users understand, monitor, and reduce their environmental impact. By combining real-time emissions tracking, personalized AI coaching, and engaging gamification, EcoTrack makes sustainability accessible and rewarding.

---

## 🎯 Chosen Vertical
**Sustainability & CleanTech (Personal Environmental Impact)**
This project targets the urgent global need for climate action by focusing on individual lifestyle modifications. While industrial changes are crucial, individual carbon footprints account for a significant portion of global emissions. EcoTrack empowers users to take control of their personal environmental impact through data visibility and actionable insights.

## 🧠 Approach and Logic
The application approaches climate change mitigation by transforming a traditionally tedious task (tracking emissions) into an engaging, educational experience. The core logic relies on three pillars:
1. **Data-Driven Visibility:** Translating mundane daily activities (like a commute or a meal) into tangible CO₂ figures using standardized emission factors, making the abstract concept of "emissions" highly concrete.
2. **Behavioral Reinforcement (Gamification):** Using an "Eco Score", tiered levels, and unlockable badges to positively reinforce sustainable behavior. The logic assumes that positive reinforcement is more effective for long-term habit building than guilt.
3. **Hyper-Personalization via AI:** Instead of offering generic "save the planet" tips, the integrated AI Coach analyzes the user's specific logged activities to provide highly relevant, contextual advice.

## ⚙️ How the Solution Works
1. **Activity Logging:** Users input daily activities across various categories (Transport, Food, Energy, Waste). For example, logging a "15km drive in a gasoline car."
2. **Emission Calculation Engine:** The FastAPI backend receives this input and processes it through a `carbon_calculator` engine, which multiplies the quantity by a predefined emission factor to output the exact CO₂ equivalent in kilograms.
3. **Dynamic Scoring:** The `EcoScoreEngine` adjusts the user's Eco Score. High-emission activities (like a long flight) deplete the score, while low-emission alternatives (like taking the train) or staying under budget increase the score.
4. **Insights & Visualizations:** The frontend (a Progressive Web App) fetches this data and renders beautiful, responsive charts (via Chart.js) showing weekly trends, category breakdowns, and monthly budget progress.
5. **AI Coaching:** The user can chat with the AI Eco Coach or read AI-generated insights. The AI contextually reads the user's recent high-emission categories and suggests specific, localized strategies for reduction.
6. **Community Challenges:** Users can join challenges (e.g., "Meatless Week" or "Public Transit Commuter") to earn bonus points and stay motivated alongside a virtual community.

## 📝 Assumptions Made
- **Averaged Emission Factors:** The emission factors (e.g., kg CO₂ per km driven) are based on global/national averages. We assume these averages are sufficient for personal tracking, though they may not perfectly reflect hyper-localized variables (like the exact fuel efficiency of the user's specific car or their local power grid's energy mix).
- **Honesty in Data Entry:** The effectiveness of the Eco Score and AI insights assumes that users are inputting their activities honestly and regularly.
- **Baseline Budgets:** The default monthly carbon budget (e.g., 300 kg CO₂) is assumed as a starting baseline. It is expected that users will manually adjust this based on their national averages or personal goals.
- **Offline Capability Needs:** By designing the frontend as a PWA with a Service Worker, we assume users will want fast, app-like access to log activities quickly on the go, even on unstable network connections.

---

## Features ✨
- **Progressive Web App (PWA)**: Installable directly to your home screen or desktop for a native app-like experience with offline caching.
- **Activity Tracking**: Log daily activities across multiple categories to calculate your exact CO₂ emissions.
- **AI Eco Coach**: A built-in AI assistant to answer sustainability questions and provide actionable insights.
- **Gamification**: Earn points, level up your "Eco Score", and unlock badges.
- **Interactive Dashboard**: Visualize your weekly, monthly, and category-based carbon footprint using dynamic charts.
- **What-If Simulations**: Calculate the potential carbon savings of making lifestyle changes (e.g., swapping a car commute for a bicycle).

## Technology Stack 🛠️

**Backend:**
- Python 3.10+
- FastAPI (Web framework)
- SQLite with SQLAlchemy (Database & ORM)
- PyJWT & Bcrypt (Authentication)

**Frontend:**
- HTML5, Vanilla JavaScript, CSS3
- Chart.js (Data visualization)
- Axios (API requests)
- Service Workers & Web App Manifest (PWA capabilities)

## Getting Started 🚀

### Prerequisites
Make sure you have Python 3 installed on your system.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Carbon-Footprint-Tracker.git
   cd Carbon-Footprint-Tracker
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install backend dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```
   *The server will start using Uvicorn. The database and seed data will be initialized automatically.*

5. **Access the App:**
   Open your browser and navigate to `http://localhost:8000`. You can install the application to your device directly from the browser's address bar.

## Project Structure 📁

```
Carbon-Footprint-Tracker/
├── backend/                  # FastAPI Backend
│   ├── main.py               # Main application entry point & API routes
│   ├── models.py             # SQLAlchemy database models
│   ├── schemas.py            # Pydantic schemas for data validation
│   ├── auth.py               # JWT authentication logic
│   ├── database.py           # Database connection setup
│   ├── carbon_engine.py      # AI Coach, Eco Score, and Emission calculations
│   ├── seed_data.py          # Initial database seeding
│   └── requirements.txt      # Python dependencies
└── frontend/                 # Progressive Web App (PWA) Frontend
    ├── index.html            # Main UI
    ├── app.js                # Frontend logic & API integration
    ├── styles.css            # Custom CSS styling
    ├── manifest.json         # PWA Manifest
    ├── sw.js                 # PWA Service Worker
    └── icon-*.svg            # PWA Icons
```

## Contributing 🤝
Contributions are always welcome! Feel free to open an issue or submit a pull request.
