"# Postpartum Care Platform

An AI‑driven, family‑inclusive platform that unifies postpartum recovery support across mental health (PPD screening), breastfeeding, nutrition, symptom tracking, and emergency guidance. Designed for continuous, personalized, explainable care after discharge.

---

## 1) Highlights
- **Unified care**: Single dashboard for breastfeeding, nutrition, mood/sleep/pain and SOS.
- **Continuous screening**: Sentiment‑aware PPD checks with safety guardrails and escalation.
- **Personalized guidance**: Deficiency‑aware nutrition and care plans with “why this” explanations.
- **RAG chatbot**: Trusted, source‑linked answers and similar‑question suggestions along with open AI LLM
- **Privacy first**: JWT auth, CORS control, configurable data retention, and PII hygiene.

---

## 2) Architecture
- **Frontend**: React + MUI under `client/`
- **Backend**: Flask API under `server/` (JWT, CORS, MongoDB)
- **ML services**: RAG chatbot + recommenders under `server/app/ml_services/` and `ml/`
- **Data**: MongoDB (users, tasks, messages, care plans)

Directory overview:
```
client/                 # React app (UI components, pages)
server/                 # Flask app (routes, models, controllers)
  app/
    routes/             # API blueprints (auth, chatbot, nutrition, care-plan, etc.)
    models/             # DB models (Mongo)
    ml_services/        # RAG + inference wrappers
  ml/                    
ml/                     # Datasets and training scripts (offline)
models/                 # Model artifacts (gitignored if large)
minimal_app.py          # Lightweight server entry (optional)

---

## 3) Features in Detail

- **RAG Chatbot + OpenAI LLM** (`/api/chatbot`)
  - Retrieval‑Augmented answers grounded in our curated knowledge base.
  - Returns trusted, source‑linked responses with similar‑question suggestions.
  - Endpoints: `POST /initialize` to warm models; `POST /chat` with `{ message }` → `{ answer, metadata, similar_questions }`.
  - Frontend: `client/src/components/Chatbot/Chatbot.jsx`.

- **PPD Screening & Sentiment** (`/api/sentiment`)
  - Lightweight mood checks and text sentiment to surface early risk signals.
  - Triggers supportive content and escalation guidance when thresholds are met.
  - Integrates with dashboard summaries and micro‑nudges.

- **Breastfeeding Support**
  - Tips, latching guidance, and FAQ via the chatbot and content modules.
  - Track pain/soreness signals to recommend posture, latch checks, and when to consult a lactation expert.

- **Nutrition Guidance & Recommender** (`/api/nutrition`)
  - DEEP NEURAL NETWORK(MLP) based recommenders suggest meals and nutrients tailored to recovery, preferences, and deficiencies and sentimental analysis for nutrition recommendation which should solve her ppd risk where harmones play major role
  - Explains "why" (e.g., iron or DHA emphasis) to build trust and adherence.

- **Personalized Care Plans** (`/api/care-plan`)
  - Generates structured, stepwise recovery actions (sleep hygiene, wound care, hydration, light activity).

  **Mental Dashboard **
  - Daily check‑ins and progress cues to promote small, sustainable wins.

- **Symptom Tracking & Daily Check‑ins** (`/api/symptom-tracking`, `/api/daily-checkin`)
  - Capture mood, sleep, pain, bleeding, incision status; surface trends in the dashboard.
  - Nudges and summaries reduce cognitive load and guide next best actions.

- **Emergency / SOS** (`client/src/pages/Emergency.jsx`)
  - Quick access to red‑flag guidance and helplines when symptoms cross thresholds.

- **Tasking & Reminders** (`/api/tasks`)
  - Convert recommendations into actionable tasks with status tracking.

- **Privacy, Auth, and Governance**
  - JWT authentication, CORS controls, scoped endpoints, and environment‑based secrets.
  - Git‑ignored artifacts: `.env`, models, node_modules, build outputs, caches.

- **Developer Experience**
  - Clear module boundaries, RESTful blueprints, and environment‑driven configuration.
  - Minimal demo server `minimal_app.py` for quick runs.

---

## 4) Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- MongoDB (local or Atlas)

Recommended local tooling: Git, Git LFS (for large model files, optional).

---

## 5) Environment Setup
Create a `.env` (root or `server/`, matching your run mode):
```
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/<db>?retryWrites=true&w=majority
JWT_SECRET_KEY=change_me
```

`.gitignore` already excludes env files, virtualenvs, `node_modules/`, build outputs, and large ML artifacts.

---

## 6) Install & Run (Development)
### Backend (Flask)
```powershell
# From project root
python -m venv .venv
# Windows activate
. .venv/Scripts/activate
# If requirements exist in server/
pip install -r server/requirements.txt  # else: pip install -r requirements.txt

# Run Flask (choose one)
set FLASK_APP=server.app
set FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=5000
# or
python minimal_app.py
```

### Frontend (React)
```powershell
cd client
npm install
npm start            # CRA
# or: npm run dev    # Vite
```

CORS is enabled for `http://localhost:3000` and `http://localhost:3001` in `server/app/__init__.py`. Adjust if your client runs on another port.

---

## 7) Core API Summary
Base path: `/api`

- **Auth**: `/auth/*` (JWT issuance, refresh)
- **Dashboard**: `/dashboard/*`
- **Chatbot**: `/chatbot`
  - `POST /api/chatbot/initialize`
  - `POST /api/chatbot/chat` → `{ message }` ⇒ `{ answer, metadata, similar_questions }`
- **Nutrition**: `/nutrition/*`
- **Care Plan**: `/care-plan/*`
- **Sentiment**: `/sentiment/*`
- **Symptoms**: `/symptom-tracking/*`
- **Daily Check‑ins**: `/daily-checkin/*`
- **Tasks**: `/tasks/*`

All protected endpoints require `Authorization: Bearer <JWT>`.

---

## 8) Running Tips
- Chatbot initialization runs on server startup (see `create_app()` in `server/app/__init__.py`). The client may also call `/initialize` on first open.
- Large models are gitignored. Use Git LFS if you need to version them.
- If you see repeated “already initialized” logs, it’s harmless; it means the RAG index is cached.

- Ensure `MONGO_URI` and `JWT_SECRET_KEY` are set in `.env`.
- CORS: update allowed origins in `server/app/__init__.py` if your client runs on a different port.

---

## 9) Testing (optional)
```bash
# Backend tests (example)
pytest -q
# Frontend tests (example)
npm test -- --watchAll=false
```

---

## 10) Deployment (outline)
- Frontend: Netlify/Vercel/Static hosting
- Backend: Render/Heroku/Fly.io with Mongo Atlas
- Set env vars (`MONGO_URI`, `JWT_SECRET_KEY`) on the platform
- Add allowed CORS origins in `server/app/__init__.py`

---

## 11) Security & Privacy
- JWT‑based auth, role‑scoped access
- Avoid storing secrets in code; use environment variables
- Sensitive PII minimized; add retention windows and export/delete endpoints as needed

---

## 12) Contributing
1. Create a feature branch
2. Keep changes scoped and well‑documented
3. Update README and any affected endpoints/docs

---

## 13) License
For 2025 – Varshitha usage. Final licensing to be confirmed by the team/organizers.
