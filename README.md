# LearnTube (YouTube Quality Search)

LearnTube is a full-stack web app that searches YouTube videos and ranks them by educational quality using AI scoring.

## What this app does

- Accepts a search query from the frontend
- Fetches matching YouTube videos from the backend
- Uses Gemini to score each result from `1.0` to `10.0`
- Returns ranked results with title, channel, views, likes, duration, and score
- Displays results in a modern YouTube-style dark UI

## Project structure

- `backend/` — Flask API and scoring pipeline
- `frontend/` — React + Vite UI

## Tech stack

- **Frontend:** React, Vite, Axios
- **Backend:** Flask, Flask-CORS, Google API Client, Google GenAI
- **Deployment:** Render (backend), Vercel (frontend)

## Current API endpoints

- `GET /healthz` → health check
- `GET /api/search?q=<query>` → returns ranked video list

## Local development setup

## 1) Backend

1. Open terminal in `backend/`
2. Create and activate a virtual environment
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set environment variables (locally):
   - `YT_API_KEY`
   - `GEMINI_API_KEY`
   - `GROQ_API_KEY` (optional)
   - `AI_MODEL` (default: `models/gemini-flash-lite-latest`)
   - `AI_FALLBACK_MODELS` (default: `models/gemini-2.0-flash-lite`)
5. Run backend:
   ```bash
   python app.py
   ```

## 2) Frontend

1. Open terminal in `frontend/`
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start dev server:
   ```bash
   npm run dev
   ```

Frontend calls backend using `VITE_API_BASE_URL` when provided; otherwise it falls back to localhost.

## Deployment

## Backend (Render)

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Environment variables required:
  - `YT_API_KEY`
  - `GEMINI_API_KEY`
  - `AI_MODEL`
  - `AI_FALLBACK_MODELS`
  - `FLASK_ENV=production`

## Frontend (Vercel)

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variables:
  - `VITE_API_BASE_URL=https://<your-render-service>.onrender.com`

## Improvement roadmap

## Phase 1 — Stability and security (next)

- [ ] Hide debug-only fields (`aiError`, model metadata) in production responses
- [ ] Restrict CORS to frontend domains only
- [ ] Add request validation and consistent API error format

## Phase 2 — Performance and scale

- [ ] Add caching for repeated search queries
- [ ] Add backend rate limiting per IP/user
- [ ] Reuse API clients safely and reduce cold-start overhead
- [ ] Add async queue for AI scoring to reduce response latency

## Phase 3 — Product quality

- [ ] Better ranking prompt and scoring consistency
- [ ] Add language-aware scoring support (TR/EN)
- [ ] Add richer filters (duration, channel, sort)
- [ ] Add pagination / infinite scroll

## Phase 4 — Observability and ops

- [ ] Structured logging and correlation IDs
- [ ] Basic metrics dashboard (latency, error rate, quota usage)
- [ ] Health/readiness checks for all critical dependencies
- [ ] CI/CD checks for build, lint, and smoke tests

## Known deployment pitfalls

- If Vercel app tries to call localhost, `VITE_API_BASE_URL` is missing or incorrect.
- If scoring returns `N/A` with permission/quota messages, check Gemini key validity and quotas.
- Linux hosts (Vercel/Render) are case-sensitive: import paths must match file names exactly.

---

If you are onboarding to this repo, start with:
1. `backend/app.py`
2. `backend/services.py`
3. `frontend/src/App.jsx`
4. `frontend/src/components/VideoCard.jsx`
