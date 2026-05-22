# Tradeoffs and Descoped Work

These are conscious decisions, not oversights. Each one is acceptable for the current scope and would be revisited at a specific trigger.

---

## No authentication

There is no JWT, session cookie, or OAuth flow. Any request to the API succeeds.

**Why it's acceptable now:** This is an internal tool accessed by one HR team on a private network. Adding auth before the data model and UX are stable adds friction to iteration without reducing meaningful risk.

**When it changes:** Before any external exposure — reverse proxy, public URL, or a second team onboarded. The addition would be FastAPI's `Depends` on a token validator injected into the routes that need it. Nothing in the service layer would change.

---

## Salaries stored in local currency with no normalisation

Each employee record stores a raw salary figure and a currency code (`INR`, `USD`, `GBP`, etc.). The global average shown in the insights summary aggregates across all rows regardless of currency — comparing ₹1,400,000 and $145,000 as if they were the same unit.

**Why it's acceptable now:** The current summary card is labelled "Global Avg Salary" without a currency symbol — a deliberate choice to make the limitation visible rather than hide it behind a misleading `$` sign. Within-country comparisons (which is where the tool is most useful) are entirely valid.

**When it changes:** When cross-country salary benchmarking becomes a use case. The schema addition is a `base_salary_usd` computed column (or a separate `fx_rates` table with a daily snapshot) and a background job to keep it current. The existing `salary` + `currency` columns stay for display; `base_salary_usd` is used only for aggregation.

---

## Median computed in Python, not SQL

`GET /api/v1/insights/country/{country}` loads all salary values for the country into a Python list and calls `statistics.median()`.

```python
salaries = [float(r[0]) for r in q.with_entities(Employee.salary).all()]
median = statistics.median(salaries)
```

**Why it's acceptable now:** The largest country bucket (India) has ~2,500 employees. Loading 2,500 floats into memory is trivial.

**When it changes:** At the scale where loading tens or hundreds of thousands of values per request is a problem. The replacement is a single SQL expression:

```sql
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary)
```

SQLite does not support `PERCENTILE_CONT`. This is another reason SQLite gives way to PostgreSQL at scale — not just write concurrency, but analytical functions.

---

## SQLite single-writer limitation

SQLite serialises all writes. Concurrent `POST`, `PATCH`, or `DELETE` requests queue behind each other at the database level. In WAL mode, reads proceed concurrently with a single writer, but two simultaneous writes block.

**Why it's acceptable now:** One HR manager, one browser tab. The write rate is low enough that serialisation is undetectable.

**When it changes:** Multiple simultaneous users submitting edits — e.g. a team of recruiters all updating records at once. The migration path is PostgreSQL: change `DATABASE_URL`, drop `check_same_thread` from the connect args, and switch to `asyncpg` if async throughput matters. The SQLAlchemy abstraction means application code is unchanged.

---

## No frontend tests

There are no Playwright or Cypress tests for the UI. The CRUD flow, modal validation, and pagination are untested at the browser level.

**Why it's acceptable now:** The backend is fully tested (46 pytest tests covering schema validation, CRUD endpoints, and all insight queries). The frontend is thin — it renders data from the API and delegates business logic to the backend. The risk surface is low.

**When it changes:** When the frontend grows past its current scope — multi-step forms, role-based rendering, or anything where a regression in the UI would be hard to catch manually. The priority test cases would be: add employee → appears in table, delete employee → row disappears, country filter → only matching rows shown, insights page → summary cards populate from real data.
