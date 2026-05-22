#!/bin/sh
set -e

python - <<'EOF'
import sys
import traceback
sys.path.insert(0, "/app")

try:
    from sqlalchemy import create_engine, func, select
    from app.database import Base
    from app.models.database import Employee
    import os

    url = os.getenv("DATABASE_URL", "sqlite:///./salary_tool.db")
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        count = conn.execute(select(func.count()).select_from(Employee.__table__)).scalar()

    if count == 0:
        print("Database is empty — running seed script")
        from scripts.seed import seed
        seed(engine, verbose=True)
    else:
        print(f"Database already has {count:,} rows — skipping seed")
except Exception:
    print("Seed step failed — starting server anyway")
    traceback.print_exc()
EOF

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
