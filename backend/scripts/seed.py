#!/usr/bin/env python3
"""
Seed 10,000 employees into the salary-tool SQLite database using a single
bulk INSERT (SQLAlchemy core executemany).

Run from backend/:
    python scripts/seed.py
"""
import random
import sys
import time
import unicodedata
from datetime import date
from itertools import product
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── path setup ───────────────────────────────────────────────────────────────
_SCRIPTS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPTS_DIR.parent
sys.path.insert(0, str(_BACKEND_DIR))

from sqlalchemy import create_engine, event, func, insert, select
from sqlalchemy.engine import Engine

from app.database import Base
from app.models.database import Employee  # registers Employee with Base.metadata

# ── configuration ─────────────────────────────────────────────────────────────
_N_TARGET = 10_000

# country → (currency, salary_low, salary_high, weight)
_COUNTRY_CONFIG: Dict[str, Tuple[str, int, int, int]] = {
    "India":       ("INR", 400_000, 2_500_000, 25),
    "USA":         ("USD",  70_000,   220_000, 20),
    "UK":          ("GBP",  35_000,   120_000, 12),
    "UAE":         ("AED",  80_000,   400_000,  8),
    "Canada":      ("CAD",  60_000,   180_000, 10),
    "Australia":   ("AUD",  65_000,   180_000,  8),
    "Singapore":   ("SGD",  50_000,   180_000,  7),
    "Germany":     ("EUR",  40_000,   140_000,  5),
    "France":      ("EUR",  38_000,   130_000,  3),
    "Netherlands": ("EUR",  42_000,   145_000,  2),
}

_DEPT_TITLES: Dict[str, List[str]] = {
    "Engineering":       ["Software Engineer", "Senior Software Engineer", "Backend Developer",
                          "Frontend Developer", "Full Stack Developer", "Technical Lead"],
    "Analytics":         ["Data Analyst", "Data Scientist", "Machine Learning Engineer", "Business Analyst"],
    "Product":           ["Product Manager", "Project Manager", "Scrum Master"],
    "Design":            ["UX Designer"],
    "Infrastructure":    ["DevOps Engineer", "Cloud Architect", "Security Engineer", "Database Administrator"],
    "Quality Assurance": ["QA Engineer"],
    "Operations":        ["Solutions Architect", "Project Manager", "Business Analyst"],
    "Finance":           ["Business Analyst", "Data Analyst", "Project Manager"],
}

_EMP_TYPES   = ["Full-time", "Part-time", "Contract", "Intern"]
_EMP_WEIGHTS = [70, 10, 15, 5]

_DATE_START     = date(2018, 1, 1)
_DATE_RANGE_DAYS = (date(2025, 12, 31) - _DATE_START).days


# ── helpers ──────────────────────────────────────────────────────────────────
def _load_names(filename: str) -> List[str]:
    path = _SCRIPTS_DIR / filename
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _normalize(name: str) -> str:
    """Strip diacritics, keep only ASCII alpha chars, return lowercase."""
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(
        c for c in nfkd if not unicodedata.combining(c) and c.isalpha()
    ).lower()


def _build_engine(url: Optional[str] = None) -> Engine:
    if url is None:
        url = f"sqlite:///{_BACKEND_DIR / 'salary_tool.db'}"
    eng = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _set_pragmas(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        # WAL + NORMAL give a good speed/safety balance for bulk loads.
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.execute("PRAGMA cache_size=-65536")   # 64 MB page cache
        cur.close()

    return eng


# ── seed ─────────────────────────────────────────────────────────────────────
def seed(engine: Optional[Engine] = None, verbose: bool = True) -> float:
    """
    Bulk-insert _N_TARGET employee rows.  Idempotent: skips when the table
    already contains >= _N_TARGET rows.  Returns elapsed seconds (0.0 if skipped).
    """
    if engine is None:
        engine = _build_engine()

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        existing: int = conn.execute(
            select(func.count()).select_from(Employee.__table__)
        ).scalar() or 0

    if existing >= _N_TARGET:
        if verbose:
            print(f"Already seeded ({existing:,} rows). Skipping.")
        return 0.0

    # ── load name lists ───────────────────────────────────────────────────────
    first_names = _load_names("first_names.txt")
    last_names  = _load_names("last_names.txt")

    # unique (first, last) pairs via random sample from the full cross-product
    pairs: List[Tuple[str, str]] = random.sample(
        list(product(first_names, last_names)), _N_TARGET
    )

    # ── pre-sample repeated categorical columns for speed ────────────────────
    country_keys    = list(_COUNTRY_CONFIG.keys())
    country_weights = [_COUNTRY_CONFIG[c][3] for c in country_keys]
    sel_countries   = random.choices(country_keys, weights=country_weights, k=_N_TARGET)
    sel_emp_types   = random.choices(_EMP_TYPES,   weights=_EMP_WEIGHTS,   k=_N_TARGET)
    dept_keys       = list(_DEPT_TITLES.keys())

    # ── build row dicts ───────────────────────────────────────────────────────
    t0        = time.perf_counter()
    start_ord = _DATE_START.toordinal()
    rows: List[dict] = []

    for i, ((first, last), country, emp_type) in enumerate(
        zip(pairs, sel_countries, sel_emp_types)
    ):
        currency, sal_lo, sal_hi, _ = _COUNTRY_CONFIG[country]
        salary    = round(random.randint(sal_lo, sal_hi) / 500) * 500
        dept      = random.choice(dept_keys)
        job_title = random.choice(_DEPT_TITLES[dept])
        hire_date = date.fromordinal(start_ord + random.randint(0, _DATE_RANGE_DAYS))

        fn    = _normalize(first) or f"user{i}"
        ln    = _normalize(last)  or f"name{i}"
        email = f"{fn}.{ln}.{i:05d}@company.com"

        rows.append({
            "full_name":       f"{first} {last}",
            "email":           email,
            "job_title":       job_title,
            "department":      dept,
            "country":         country,
            "salary":          salary,
            "currency":        currency,
            "employment_type": emp_type,
            "hire_date":       hire_date,
        })

    # ── single bulk INSERT (executemany) ─────────────────────────────────────
    with engine.begin() as conn:
        conn.execute(insert(Employee.__table__), rows)

    elapsed = time.perf_counter() - t0
    if verbose:
        print(f"Seeded {_N_TARGET:,} employees in {elapsed:.2f}s")
    return elapsed


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    seed()
