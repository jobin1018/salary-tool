# Architecture

## Stack choices

### FastAPI + SQLite

This is an internal HR tool for one team. The right call at this scope is the simplest stack that satisfies the requirements — not the one that would survive a Series B.

FastAPI gives async-capable routes, automatic OpenAPI docs, and Pydantic validation out of the box. SQLite removes the operational overhead of running a database server: no container, no connection string management, no migration tooling beyond SQLAlchemy's `create_all`. The database is a single file that lives next to the application, backs up with `cp`, and handles tens of thousands of reads per second easily — far more than one HR manager will ever generate.

PostgreSQL becomes the right answer when you need concurrent writers, row-level locking, or a managed cloud instance shared across teams. None of those apply here.

### Service layer

Routes delegate to `app/services/employee_service.py`; they do not touch the database directly.

```
Request → Route (HTTP concerns only) → Service (business logic) → ORM → DB
```

This separation has two concrete payoffs:

1. **Testability.** The service functions take a `Session` argument, so tests can inject an in-memory SQLite session without monkey-patching anything or standing up a server.
2. **Single responsibility.** When the insight aggregation logic changes (e.g. switching median from Python to a SQL window function), the route file is untouched. When the HTTP response shape changes, the service is untouched.

Routes are responsible for: parsing query params, calling the service, mapping return values to response models, and raising `HTTPException` on known error conditions (404, 409). Nothing else.

### Composite index on (country, job_title)

The insights endpoints access salary data in two patterns:

1. All employees in a country → `WHERE country = ?`
2. Employees in a country with a specific job title → `WHERE country = ? AND job_title = ?`

A composite index `(country, job_title)` satisfies both. SQLite (and every other B-tree index engine) can use the leftmost prefix of a composite index, so a query filtering only on `country` hits the same index. A separate single-column index on `country` would have been redundant.

A composite index on `(job_title, country)` would not work for case 1 — the leading column must be `country`.

### Pydantic validation at the schema boundary

Validation lives in `app/models/schemas.py`, not in the service or the route handler. The rule is: invalid data should be rejected as early as possible, before it touches any business logic.

The specific case that motivated an explicit validator rather than relying on Pydantic's type coercion: `hire_date`. Python 3.11+ `date.fromisoformat()` accepts compact format strings like `"20240315"` — no hyphens. Pydantic's `date` type would silently accept that. Declaring the field as `str` with a regex validator (`^\d{4}-\d{2}-\d{2}$`) rejects it at the boundary with a clear error message instead of storing a value the frontend never sent.

`salary` is validated `ge=0` in the schema. `currency` and `employment_type` are `Literal` types — any value not in the enum fails immediately with a list of valid options. None of this logic bleeds into the service.

## Frontend

### React Query over useEffect + fetch

Every mutation (create, update, delete) calls `queryClient.invalidateQueries({ queryKey: ['employees'] })` on success. React Query refetches the employee list automatically. The alternative — managing a local state array and splicing/appending on mutation success — requires handling every edge case manually: pagination offsets shifting after a delete, stale total counts, concurrent updates from other tabs.

React Query also handles loading and error states per-query without global state, and its `keepPreviousData` option prevents the table from flickering to empty on every page change. These are problems you solve yourself with `useEffect + fetch`, every time, in every project. Using React Query means they're already solved.
