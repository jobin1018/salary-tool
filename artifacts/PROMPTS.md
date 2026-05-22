### 1. Project scaffold

> Scaffold a `salary-tool/` project with `backend/` (FastAPI), `frontend/` (Vite + React), and `artifacts/` (empty). In `backend/`, create `requirements.txt` with fastapi, uvicorn, sqlalchemy, pydantic[email], pytest, httpx, pytest-asyncio. Create the `app/` package with `__init__.py` files. Add `.gitignore` for Python and Node. Do not write any application logic yet.

**Intent:** Establish the directory contract and dependency list before any code exists. Separating scaffold from implementation prevents the AI from making stack choices that belong to the engineer.

---

### 2. RED tests — Pydantic schema

> In `backend/app/tests/test_models.py`, write pytest tests for a Pydantic `EmployeeCreate` schema that does not exist yet. Cover: empty `full_name` rejected, negative salary rejected, `currency` must be one of `[USD, EUR, GBP, INR, AED, AUD, CAD, SGD]`, `employment_type` must be one of `[Full-time, Part-time, Contract, Intern]`, `hire_date` must be `YYYY-MM-DD` format (reject `"20240315"` and `"2024/03/15"`), valid payload passes. Run pytest — all tests must fail with `ImportError`. Do not write the schema.

**Intent:** Lock the validation contract in tests before implementation exists. Specifying the `"20240315"` rejection case explicitly prevents Pydantic's permissive `date` coercion from slipping through — a detail the AI would not know to guard against without being told.

---

### 3. GREEN implementation — models and DB wiring

> Make all tests in `test_models.py` pass. Implement: `backend/app/models/database.py` — SQLAlchemy `Employee` model with columns `[id, full_name, email, job_title, department, country, salary, currency, employment_type, hire_date, created_at, updated_at]`. Add a composite index on `(country, job_title)`. Use SQLite. `backend/app/models/schemas.py` — Pydantic v2 `EmployeeCreate`, `EmployeeUpdate` (all fields optional), `EmployeeRead` (includes `id`, `created_at`, `updated_at`), `PaginatedEmployees`. Wire up `get_db()` as a generator dependency. Do not write routes yet.

**Intent:** The composite index requirement and the four-schema structure were decided before this prompt. Telling the AI "do not write routes yet" keeps the RED/GREEN boundary clean — one failing test suite at a time.

---

### 4. Insights endpoint tests and implementation

> In `backend/app/tests/test_insights_api.py`, write failing tests for: `GET /api/v1/insights/summary` (total count, global min/max/avg), `GET /api/v1/insights/country/{country}` (count, min, max, avg, median), `GET /api/v1/insights/country/{country}/job-titles` (list of strings), `GET /api/v1/insights/country/{country}/job-title/{job_title}` (same stats shape as country). Seed exactly 20 employees with known salaries in the fixture so stat assertions are deterministic — do not use random data. Routes do not exist yet.
>
> Then make them pass. Use `statistics.median` for median — do not approximate. Use SQL aggregates (`func.count`, `func.min`, `func.max`, `func.avg`) for the rest, not Python loops over all rows.

**Intent:** Deterministic seed data in the fixture is non-negotiable for stats tests — random data makes assertions impossible. Specifying `statistics.median` vs SQL prevents the AI from choosing an approximation. The two-phase structure (write failing tests, then implement) was a deliberate constraint to keep the test suite honest.

---

### 5. Seed script with performance target

> Create `backend/scripts/seed.py`. Requirements: insert exactly 10,000 employees into the SQLite database, idempotent (skip if already seeded), under 5 seconds on commodity hardware. Use a single bulk `executemany` INSERT — not ORM `session.add()` in a loop. Generate unique `(first, last)` name pairs from `first_names.txt` and `last_names.txt` files (create these too, 200+ diverse international names each). Emails must be collision-safe. Strip diacritics from names before building email addresses. Return elapsed seconds from the function so it can be timed externally. Also create `scripts/benchmark_seed.py` that runs 3 fresh seedings and prints per-run time and average.

**Intent:** The 5-second target, bulk insert requirement, and diacritic stripping were all pre-decided constraints. Giving the AI a measurable target (return elapsed seconds, benchmark script) makes the requirement verifiable rather than subjective.

---

### 6. Frontend wiring

> Build the React frontend. Backend runs at `http://localhost:8000`. Stack: Vite + React (already scaffolded), TailwindCSS, shadcn/ui components as `.jsx` (manual setup, not CLI — avoid interactive prompts), React Query v5 for data fetching, React Router, Recharts, axios. Two pages: `/employees` — server-side paginated table with debounced search (300ms), country/department/type filter dropdowns populated from `GET /api/v1/employees/filters`, add/edit modal with client-side validation, delete confirmation dialog, all mutations invalidate the employees query. `/insights` — four summary cards, country selector → stats card, job title selector (resets on country change) → stats card, bar chart of avg salary by department, top 10 earners table. Sticky navbar with active link styling.

**Intent:** Manual shadcn/ui setup was specified to avoid the CLI asking interactive questions mid-execution. The `300ms` debounce, query invalidation pattern, and "resets on country change" behaviour were specified explicitly because they're the details that get missed when the prompt is vague.
