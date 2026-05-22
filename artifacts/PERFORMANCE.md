# Performance

## Seed script

### The problem with naive ORM inserts

The obvious implementation of a seed script creates one ORM object per row and adds it to the session:

```python
for row in data:
    db.add(Employee(**row))
db.commit()
```

For 10,000 rows this is O(n) round trips to SQLite. Each `add()` registers the object in SQLAlchemy's identity map. The `commit()` flushes 10,000 individual INSERT statements. On top of the actual I/O, there is Python-side overhead for object construction, `__init__` calls, and attribute instrumentation for every row. At 10k rows this runs in several seconds. At 100k rows it becomes a blocking operation.

### The solution: single bulk INSERT

All row dicts are built in Python first — no ORM objects, just plain dicts — then dispatched in a single call:

```python
with engine.begin() as conn:
    conn.execute(insert(Employee.__table__), rows)
```

SQLAlchemy translates this to a single DBAPI `executemany()` call. SQLite processes the entire batch in one transaction with one write-ahead log flush. The ORM layer (identity map, change tracking, `__init__` hooks) is bypassed entirely, which is correct here — the seed script is not an application write path.

Additional SQLite pragmas applied at connection time:

```sql
PRAGMA journal_mode=WAL      -- concurrent readers during write
PRAGMA synchronous=NORMAL    -- one fsync at checkpoint, not per-commit
PRAGMA cache_size=-65536     -- 64 MB page cache
```

### Benchmark results

Measured on a standard development laptop. Each run seeds 10,000 rows into a fresh (truncated) table.

| Run | Time |
|-----|------|
| 1   | 0.22s |
| 2   | 0.25s |
| 3   | 0.24s |
| **Average** | **0.24s** |

Target was under 5 seconds. Actual result is ~20× under that target. The bottleneck at this scale is not SQLite I/O — it is Python-side list construction (name cross-product sampling, `unicodedata.normalize` calls for diacritic stripping). The INSERT itself is negligible.

To reproduce:

```bash
cd backend
python scripts/benchmark_seed.py
```

## Index strategy

A composite B-tree index on `(country, job_title)` was added to the `employees` table:

```python
Index("ix_employees_country_job_title", "country", "job_title")
```

The insights endpoints have two access patterns:

- `GET /insights/country/{country}` — filters `WHERE country = ?`, aggregates over all matching rows
- `GET /insights/country/{country}/job-title/{job_title}` — filters `WHERE country = ? AND job_title = ?`

SQLite can use the leftmost prefix of a composite index. Both queries hit `ix_employees_country_job_title`. A standalone `country` index would handle only the first pattern; the composite handles both and eliminates the need for a second index on `(country, job_title)` individually.

At 10,000 rows the index is not required for correctness, but it makes the insight queries index scans instead of full table scans, which matters when the table grows and when multiple insight requests arrive concurrently.

## What changes at 1M rows

| Concern | Current approach | At 1M rows |
|---|---|---|
| Database | SQLite, single writer | PostgreSQL with connection pooling |
| Bulk load | `executemany` via SQLAlchemy core | PostgreSQL `COPY FROM STDIN` (order-of-magnitude faster than INSERT) |
| Median | `statistics.median` in Python (loads all salaries into memory) | `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary)` SQL window function |
| Count query | `SELECT COUNT(*)` on filtered result set | Cursor-based pagination or materialised count to avoid full scans |
| Connection management | Single `create_engine` call | `AsyncEngine` with `asyncpg`, pool size tuned to worker count |
