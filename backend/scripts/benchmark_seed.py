#!/usr/bin/env python3
"""
Time seed.py over 3 fresh runs and report per-run timing plus average.

Run from backend/:
    python scripts/benchmark_seed.py
"""
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPTS_DIR.parent
sys.path.insert(0, str(_BACKEND_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR))  # lets `import seed` find seed.py

from sqlalchemy import delete

from seed import _build_engine, seed  # noqa: E402  (after path setup)
from app.models.database import Employee  # noqa: E402

RUNS = 3


def main() -> None:
    engine = _build_engine()
    times = []

    for run in range(1, RUNS + 1):
        # Wipe rows so the idempotency guard doesn't skip subsequent runs.
        with engine.begin() as conn:
            conn.execute(delete(Employee.__table__))

        elapsed = seed(engine, verbose=False)
        times.append(elapsed)
        print(f"Run {run}: {elapsed:.2f}s")

    avg = sum(times) / RUNS
    print(f"\nAverage over {RUNS} runs: {avg:.2f}s")


if __name__ == "__main__":
    main()
