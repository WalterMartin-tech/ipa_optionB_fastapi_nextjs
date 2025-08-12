# IPA Option B – FastAPI + Next.js

## Backend
```bash
cd backend
python3 -m venv .venv
./.venv/bin/python -m pip install -U pip
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/uvicorn app:app --reload --port 8000
```
API:
- POST /calculate
- POST /export/xlsx
- POST /export/pdf

## Frontend
```bash
cd frontend
npm i
npm run dev
```
Open http://localhost:3000 and set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` if needed.
