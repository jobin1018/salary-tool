"""
Insights API tests — all assertions will fail until the routes are implemented.

Seed design (20 employees, 5 countries):
  India (5):  SE×3 @ 50k/70k/90k, Data Analyst @ 60k, DevOps @ 80k
              → count=5, min=50k, max=90k, avg=70k, median=70k
  India SE (3):  50k/70k/90k  → avg=70k, median=70k
  Global:    sum=2_200_000, avg=110k, min=50k, max=200k
"""
import pytest
import pytest_asyncio

_EMPLOYEES_BASE = "/api/v1/employees"
BASE = "/api/v1/insights"

# ---------------------------------------------------------------------------
# Seed data — 20 employees across 5 countries with exact, integer salaries
# so every stats assertion is deterministic.
# ---------------------------------------------------------------------------
_SEED_EMPLOYEES = [
    # ── India (5) ────────────────────────────────────────────────────────────
    # Three Software Engineers: 50k / 70k / 90k
    # → India SE: count=3, min=50k, max=90k, avg=70k, median=70k
    # → India all: count=5, min=50k, max=90k, avg=70k, median=70k
    {"full_name": "Aarav Singh",    "email": "aarav@example.com",  "job_title": "Software Engineer", "department": "Engineering",    "country": "India",  "salary": 50000,  "currency": "INR", "employment_type": "Full-time", "hire_date": "2022-01-10"},
    {"full_name": "Priya Patel",    "email": "priya@example.com",  "job_title": "Software Engineer", "department": "Engineering",    "country": "India",  "salary": 70000,  "currency": "INR", "employment_type": "Full-time", "hire_date": "2021-05-15"},
    {"full_name": "Rohan Mehta",    "email": "rohan@example.com",  "job_title": "Software Engineer", "department": "Engineering",    "country": "India",  "salary": 90000,  "currency": "INR", "employment_type": "Full-time", "hire_date": "2020-08-20"},
    {"full_name": "Sneha Kumar",    "email": "sneha@example.com",  "job_title": "Data Analyst",      "department": "Analytics",      "country": "India",  "salary": 60000,  "currency": "INR", "employment_type": "Full-time", "hire_date": "2023-02-01"},
    {"full_name": "Vikram Nair",    "email": "vikram@example.com", "job_title": "DevOps Engineer",   "department": "Infrastructure", "country": "India",  "salary": 80000,  "currency": "INR", "employment_type": "Full-time", "hire_date": "2021-11-30"},

    # ── USA (5) ──────────────────────────────────────────────────────────────
    {"full_name": "Alice Morgan",   "email": "alice.m@example.com","job_title": "Product Manager",   "department": "Product",        "country": "USA",    "salary": 120000, "currency": "USD", "employment_type": "Full-time", "hire_date": "2019-03-15"},
    {"full_name": "Brian Cooper",   "email": "brian@example.com",  "job_title": "Software Engineer", "department": "Engineering",    "country": "USA",    "salary": 140000, "currency": "USD", "employment_type": "Full-time", "hire_date": "2020-07-01"},
    {"full_name": "Clara Foster",   "email": "clara@example.com",  "job_title": "Data Scientist",    "department": "Analytics",      "country": "USA",    "salary": 130000, "currency": "USD", "employment_type": "Full-time", "hire_date": "2021-09-15"},
    {"full_name": "Daniel Hayes",   "email": "daniel@example.com", "job_title": "UX Designer",       "department": "Design",         "country": "USA",    "salary": 110000, "currency": "USD", "employment_type": "Full-time", "hire_date": "2022-04-20"},
    {"full_name": "Elena Brooks",   "email": "elena@example.com",  "job_title": "DevOps Engineer",   "department": "Infrastructure", "country": "USA",    "salary": 135000, "currency": "USD", "employment_type": "Full-time", "hire_date": "2020-11-10"},

    # ── UK (4) ───────────────────────────────────────────────────────────────
    {"full_name": "Fiona Campbell", "email": "fiona@example.com",  "job_title": "Software Engineer", "department": "Engineering",    "country": "UK",     "salary": 85000,  "currency": "GBP", "employment_type": "Full-time", "hire_date": "2021-06-01"},
    {"full_name": "George Dixon",   "email": "george@example.com", "job_title": "Data Analyst",      "department": "Analytics",      "country": "UK",     "salary": 75000,  "currency": "GBP", "employment_type": "Full-time", "hire_date": "2022-03-15"},
    {"full_name": "Hannah Ellis",   "email": "hannah@example.com", "job_title": "Product Manager",   "department": "Product",        "country": "UK",     "salary": 95000,  "currency": "GBP", "employment_type": "Full-time", "hire_date": "2020-09-01"},
    {"full_name": "Ian Fletcher",   "email": "ian@example.com",    "job_title": "UX Designer",       "department": "Design",         "country": "UK",     "salary": 80000,  "currency": "GBP", "employment_type": "Full-time", "hire_date": "2023-01-15"},

    # ── UAE (3) ──────────────────────────────────────────────────────────────
    # Kevin is the global top earner at 200k.
    {"full_name": "Julia Green",    "email": "julia@example.com",  "job_title": "Software Engineer", "department": "Engineering",    "country": "UAE",    "salary": 180000, "currency": "AED", "employment_type": "Full-time", "hire_date": "2021-08-01"},
    {"full_name": "Kevin Hall",     "email": "kevin@example.com",  "job_title": "Data Scientist",    "department": "Analytics",      "country": "UAE",    "salary": 200000, "currency": "AED", "employment_type": "Full-time", "hire_date": "2019-12-15"},
    {"full_name": "Laura Jones",    "email": "laura@example.com",  "job_title": "DevOps Engineer",   "department": "Infrastructure", "country": "UAE",    "salary": 190000, "currency": "AED", "employment_type": "Full-time", "hire_date": "2020-06-20"},

    # ── Canada (3) ───────────────────────────────────────────────────────────
    {"full_name": "Marcus King",    "email": "marcus@example.com", "job_title": "Software Engineer", "department": "Engineering",    "country": "Canada", "salary": 110000, "currency": "CAD", "employment_type": "Full-time", "hire_date": "2022-05-10"},
    {"full_name": "Natalie Lane",   "email": "natalie@example.com","job_title": "Data Analyst",      "department": "Analytics",      "country": "Canada", "salary": 95000,  "currency": "CAD", "employment_type": "Full-time", "hire_date": "2021-10-01"},
    {"full_name": "Oscar Lloyd",    "email": "oscar@example.com",  "job_title": "Product Manager",   "department": "Product",        "country": "Canada", "salary": 105000, "currency": "CAD", "employment_type": "Full-time", "hire_date": "2020-02-28"},
]

# Derived constants (verified by hand above the module docstring)
_TOTAL = 20
_GLOBAL_MIN = 50_000
_GLOBAL_MAX = 200_000
_GLOBAL_AVG = 110_000  # 2_200_000 / 20

_INDIA_COUNT = 5
_INDIA_MIN = 50_000
_INDIA_MAX = 90_000
_INDIA_AVG = 70_000   # 350_000 / 5
_INDIA_MEDIAN = 70_000

_INDIA_SE_COUNT = 3
_INDIA_SE_MIN = 50_000
_INDIA_SE_MAX = 90_000
_INDIA_SE_AVG = 70_000   # 210_000 / 3
_INDIA_SE_MEDIAN = 70_000

_INDIA_JOB_TITLES = {"Software Engineer", "Data Analyst", "DevOps Engineer"}
_ENGINEERING_COUNT = 7  # Aarav+Priya+Rohan (India) + Brian (USA) + Fiona (UK) + Julia (UAE) + Marcus (Canada)


# ---------------------------------------------------------------------------
# Fixture — seeds all 20 employees through the live CRUD endpoint so the
# test DB is populated identically to a real run.  Inherits `client` from
# conftest.py (fresh in-memory SQLite per test).
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def seeded_client(client):
    for emp in _SEED_EMPLOYEES:
        r = await client.post(_EMPLOYEES_BASE, json=emp)
        assert r.status_code == 201, f"seed failed for {emp['email']}: {r.json()}"
    return client


# ---------------------------------------------------------------------------
# GET /api/v1/insights/summary
# ---------------------------------------------------------------------------

async def test_summary_returns_200_with_required_keys(seeded_client):
    r = await seeded_client.get(f"{BASE}/summary")
    assert r.status_code == 200
    body = r.json()
    for key in ("total_employees", "global_avg_salary", "global_min_salary",
                "global_max_salary", "country_breakdown", "department_breakdown",
                "top_earners"):
        assert key in body, f"missing key in summary: {key}"


async def test_summary_global_counts_and_salary_bounds(seeded_client):
    r = await seeded_client.get(f"{BASE}/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_employees"] == _TOTAL
    assert body["global_min_salary"] == pytest.approx(_GLOBAL_MIN)
    assert body["global_max_salary"] == pytest.approx(_GLOBAL_MAX)
    assert body["global_avg_salary"] == pytest.approx(_GLOBAL_AVG)


async def test_summary_top_earners_length_and_order(seeded_client):
    r = await seeded_client.get(f"{BASE}/summary")
    assert r.status_code == 200
    top = r.json()["top_earners"]
    assert len(top) == 10
    # Kevin (UAE, 200k) must be first
    assert top[0]["salary"] == pytest.approx(_GLOBAL_MAX)
    # List is sorted descending
    salaries = [e["salary"] for e in top]
    assert salaries == sorted(salaries, reverse=True)


async def test_summary_country_breakdown_india(seeded_client):
    r = await seeded_client.get(f"{BASE}/summary")
    assert r.status_code == 200
    breakdown = r.json()["country_breakdown"]

    countries = {row["country"] for row in breakdown}
    assert {"India", "USA", "UK", "UAE", "Canada"} == countries

    india = next(row for row in breakdown if row["country"] == "India")
    assert india["count"] == _INDIA_COUNT
    assert "avg_salary" in india


async def test_summary_department_breakdown_engineering(seeded_client):
    r = await seeded_client.get(f"{BASE}/summary")
    assert r.status_code == 200
    breakdown = r.json()["department_breakdown"]

    dept_names = {row["department"] for row in breakdown}
    assert {"Engineering", "Analytics", "Infrastructure", "Product", "Design"} == dept_names

    eng = next(row for row in breakdown if row["department"] == "Engineering")
    assert eng["count"] == _ENGINEERING_COUNT


# ---------------------------------------------------------------------------
# GET /api/v1/insights/country/{country}
# ---------------------------------------------------------------------------

async def test_country_stats_india_shape_and_values(seeded_client):
    r = await seeded_client.get(f"{BASE}/country/India")
    assert r.status_code == 200
    body = r.json()
    for key in ("count", "min_salary", "max_salary", "avg_salary", "median_salary"):
        assert key in body, f"missing key in country stats: {key}"
    assert body["count"] == _INDIA_COUNT
    assert body["min_salary"] == pytest.approx(_INDIA_MIN)
    assert body["max_salary"] == pytest.approx(_INDIA_MAX)
    assert body["avg_salary"] == pytest.approx(_INDIA_AVG)
    assert body["median_salary"] == pytest.approx(_INDIA_MEDIAN)


async def test_country_stats_unknown_returns_404(seeded_client):
    r = await seeded_client.get(f"{BASE}/country/Narnia")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/insights/country/{country}/job-titles
# ---------------------------------------------------------------------------

async def test_country_job_titles_india(seeded_client):
    r = await seeded_client.get(f"{BASE}/country/India/job-titles")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert set(body) == _INDIA_JOB_TITLES


async def test_country_job_titles_unknown_country_returns_404(seeded_client):
    r = await seeded_client.get(f"{BASE}/country/Narnia/job-titles")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/insights/country/{country}/job-title/{job_title}
# ---------------------------------------------------------------------------

async def test_country_job_title_stats_india_se(seeded_client):
    r = await seeded_client.get(f"{BASE}/country/India/job-title/Software%20Engineer")
    assert r.status_code == 200
    body = r.json()
    for key in ("count", "min_salary", "max_salary", "avg_salary", "median_salary"):
        assert key in body, f"missing key in job-title stats: {key}"
    assert body["count"] == _INDIA_SE_COUNT
    assert body["min_salary"] == pytest.approx(_INDIA_SE_MIN)
    assert body["max_salary"] == pytest.approx(_INDIA_SE_MAX)
    assert body["avg_salary"] == pytest.approx(_INDIA_SE_AVG)
    assert body["median_salary"] == pytest.approx(_INDIA_SE_MEDIAN)


async def test_country_job_title_unknown_job_returns_404(seeded_client):
    r = await seeded_client.get(f"{BASE}/country/India/job-title/FakeJob")
    assert r.status_code == 404


async def test_country_job_title_unknown_country_returns_404(seeded_client):
    r = await seeded_client.get(f"{BASE}/country/Narnia/job-title/Software%20Engineer")
    assert r.status_code == 404
