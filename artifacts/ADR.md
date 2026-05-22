# Architecture Decision Records

---

## ADR-001: SQLite over PostgreSQL

**Status:** Accepted

**Context:**
The tool serves a single HR team internally. There is one concurrent writer at most. The dataset is bounded (10k employees, growing slowly). There is no existing infrastructure mandate for a particular database, and minimising operational overhead was an explicit goal.

**Decision:**
Use SQLite with WAL journal mode. The database lives as a file in the backend directory. No database server, no Docker Compose, no connection pooling configuration.

**Consequences:**
- Zero operational overhead to run or back up the database.
- WAL mode (`PRAGMA journal_mode=WAL`) allows concurrent readers alongside a single writer, which is sufficient for this access pattern.
- Single-writer limitation means this cannot scale to multiple simultaneous users submitting edits. Acceptable for MVP; migrating to PostgreSQL later requires changing only the `DATABASE_URL` and dropping the SQLite-specific `check_same_thread` connect arg — SQLAlchemy abstracts the rest.
- The database file must not be committed to version control (enforced via `.gitignore`).

---

## ADR-002: Bulk INSERT for seed script over ORM individual inserts

**Status:** Accepted

**Context:**
The seed script needs to insert 10,000 employee rows. The naive approach — instantiate an ORM `Employee` object per row and `db.add()` each one — results in 10,000 individual round trips to SQLite, each with its own Python overhead for object construction, attribute tracking, and identity map bookkeeping.

**Decision:**
Build all row dicts in Python first, then execute a single `conn.execute(insert(Employee.__table__), rows)` call. SQLAlchemy translates this to a single `executemany` call against the DBAPI, which SQLite processes in one transaction with minimal overhead.

**Consequences:**
- Seed time: ~0.24s average for 10,000 rows (measured; see `PERFORMANCE.md`).
- Bypasses SQLAlchemy's ORM layer (no identity map, no `created_at`/`updated_at` Python-side defaults). The `created_at` and `updated_at` columns use `server_default=func.now()` so SQLite sets them — this works correctly with core INSERT.
- The seed script is not the application's write path, so losing ORM conveniences (e.g. `db.refresh()`) is not a problem.
- The benchmark script (`scripts/benchmark_seed.py`) validates performance across 3 fresh runs so regressions are detectable.

---

## ADR-003: Server-side pagination over client-side for 10k records

**Status:** Accepted

**Context:**
The employees table has 10,000 rows. The list endpoint needs to support search, filtering by country/department/employment type, and sorting. Fetching the full dataset on page load and filtering in the browser was considered.

**Decision:**
Paginate at the database level. The list endpoint accepts `page`, `page_size`, `search`, `country`, `department`, `employment_type`, `sort_by`, and `sort_order` query parameters. SQLAlchemy applies `OFFSET/LIMIT` after filters and count query.

**Consequences:**
- Initial page load transfers ~20 rows, not 10,000. Response time is fast regardless of dataset size.
- Every filter change and page turn requires a network round trip. Acceptable: the backend is local or on the same network, and React Query's `keepPreviousData` prevents visible jank between pages.
- The total row count requires a separate `COUNT(*)` query on the filtered result set. At 10k rows this is negligible. At 1M rows a cursor-based approach or cached count would be warranted.
- Client-side filtering would have been simpler to implement but would break down the moment the dataset grows or the tool is used over a slow connection.
