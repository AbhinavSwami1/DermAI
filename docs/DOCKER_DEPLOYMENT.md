# DermAI - Docker Containerization and Deployment

## Status
Dockerfiles and Compose configuration are written and the Compose file parses. **The images have not been built or run in the authoring environment (no Docker daemon).** Treat the build and the checks below as pending until executed and recorded in the table at the end.

## Architecture
| Service | Image | Port | Notes |
|---|---|---|---|
| db | postgres:16 | internal only | named volume `postgres_data`, health check |
| backend | built from `backend/Dockerfile` (repo root context) | 8001 | FastAPI + MobileNetV3 inference + Grad-CAM, CPU PyTorch; runs `alembic upgrade head` on start; non-root user |
| frontend | built from `frontend/Dockerfile` (Node build, nginx) | 8080 | API URL baked in at build time |

Inference stays inside the backend container (no separate inference service). Uploads are stored in the named volume `uploads_data` (`/app/backend/storage`). The checkpoint is **not** in the image: it is bind-mounted read-only from `./ml/checkpoints` to `/app/ml/checkpoints`; its path is set by `DERMAI_MODEL_CHECKPOINT`. CORS origins come from `CORS_ORIGINS` (default for local dev unchanged).

## Run
```
cp .env.example .env        # set POSTGRES_PASSWORD and JWT_SECRET_KEY
ls ml/checkpoints/mobilenet/best_mobilenet_v3_large_finetuned.pth
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f backend
```
Open http://localhost:8080 (API docs: http://localhost:8001/docs). Use `localhost` for both, so the refresh cookie stays same-site.

Stop: `docker compose down` (keeps volumes). `docker compose down -v` erases the database and uploads.

## Update and rollback
```
git pull && docker compose build && docker compose up -d
docker tag dermai-backend:latest dermai-backend:<release>     # keep the previous image for rollback
docker compose logs --tail=200 backend
```
Rollback: check out the previous git tag, rebuild, `docker compose up -d`. Database migrations are additive; restore a database backup if a migration must be undone (`alembic downgrade -1` for the last one).

## Backup
```
docker compose exec db pg_dump -U dermai dermai > backup_$(date +%F).sql
docker run --rm -v dermai_uploads_data:/data -v "$PWD":/out alpine tar czf /out/uploads_$(date +%F).tgz -C /data .
```
Also copy `ml/checkpoints/` (not in Git) to a separate location. A volume is persistence, not a backup.

## Known limitations
- CPU inference only; no GPU configuration.
- Single backend process; login rate limiting is in memory per process.
- Not deployed to a public host; no HTTPS or reverse proxy configured. Public use requires TLS and `CORS_ORIGINS` set to the real frontend origin.
- `/insights/model-metrics` reports "not available" in Docker unless `ml/outputs/mobilenet_v3_large_finetuned/test_metrics.json` is made available to the container.
- Python/torch versions come from `backend/requirements.txt`; if the CPU wheel for the pinned torch version is unavailable, the build fails and the pin must be changed.

## Verification record (fill in after running)
| Check | Expected | Result | Date | By |
|---|---|---|---|---|
| `docker compose build` | both images build | | | |
| `docker compose ps` | db healthy, backend healthy, frontend up | | | |
| Landing page at :8080 | loads | | | |
| Register and log in | succeeds | | | |
| Upload + prediction (real checkpoint) | real class and scores | | | |
| `docker compose restart backend`, open history | record and image still present | | | |
| `docker compose down` then `up`, open history | record and image still present | | | |
| PDF/CSV/JSON export from saved record | matches record | | | |
| Invalid file, oversized file | controlled error | | | |
| Checkpoint missing (rename it) | controlled 503, no crash | | | |
