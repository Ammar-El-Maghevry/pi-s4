#!/bin/sh
set -e

echo "Waiting for database..."
python - <<'PY'
import time
import sys
from sqlalchemy import create_engine, text
from app.config import settings

for attempt in range(30):
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        break
    except Exception as exc:
        print(f"  db not ready yet ({exc}); retrying...")
        time.sleep(2)
else:
    print("Database never became ready", file=sys.stderr)
    sys.exit(1)
PY

echo "Running migrations..."
alembic upgrade head

echo "Seeding initial data..."
python -m app.initial_data

echo "Starting application..."
exec "$@"
