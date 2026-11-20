# DermAI

Skin-image analysis research prototype (PAD-UFES-20). Not clinically validated; not a diagnostic tool.

## Stack
FastAPI + PostgreSQL (SQLAlchemy, Alembic), PyTorch (MobileNetV3-Large), React + Vite + Tailwind.

## Setup
```
# Backend
cp backend/.env.example backend/.env      # set DATABASE_URL and JWT_SECRET_KEY
pip install -r backend/requirements.txt -r ml/requirements.txt
alembic upgrade head
PYTHONPATH="$PWD:$PWD/backend" uvicorn app.main:app --app-dir backend --port 8001 --reload

# Frontend
cd frontend && npm install && npm run dev
```
Place the checkpoint at `ml/checkpoints/mobilenet/best_mobilenet_v3_large_finetuned.pth` (not committed).

## Tests
`PYTHONPATH="$PWD:$PWD/backend" pytest -q backend/tests/`  and  `cd frontend && npm run build`

## Docs
See `docs/` (status, dataset audit, model comparison, Grad-CAM, calibration, risk feasibility, LR plan, Week 7 checklist).

## Docker
See `docs/DOCKER_DEPLOYMENT.md`. Quick start: `cp .env.example .env`, set the two secrets, put the checkpoint in `ml/checkpoints/mobilenet/`, then `docker compose up --build` and open http://localhost:8080.
