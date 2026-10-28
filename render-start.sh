#!/usr/bin/env bash
set -e
python -c "from app import app; from database.models import db, WaterData; from database.seed import seed_database; ctx=app.app_context(); ctx.push(); db.create_all(); seed_database() if WaterData.query.count() == 0 else None"
exec gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 4 --timeout 120
