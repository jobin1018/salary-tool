# salary-tool

An internal HR tool for managing and analysing employee salary data across countries and departments. 10,000 seeded employees, server-side pagination, filtering, and an insights dashboard with per-country breakdowns and top earners.

## Stack

| Layer    | Technology                                          |
|----------|-----------------------------------------------------|
| Backend  | Python 3.12 · FastAPI · SQLAlchemy · SQLite         |
| Frontend | React 19 · Vite · TailwindCSS · shadcn/ui · Recharts |
| Testing  | pytest · pytest-asyncio · httpx                     |
| Deploy   | Render (Docker)                                     |

## Project layout

```
salary-tool/
├── backend/
│   ├── app/
│   │   ├── models/       # SQLAlchemy model + Pydantic schemas
│   │   ├── routes/       # FastAPI routers (employees, insights)
│   │   ├── services/     # Business logic, DB queries
│   │   └── tests/        # pytest test suite (46 tests)
│   ├── scripts/
│   │   ├── seed.py           # Bulk-inserts 10k employees (~0.24s)
│   │   └── benchmark_seed.py # Times 3 seed runs, prints average
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/          # axios API layer
│       ├── components/   # Navbar, modals, shadcn/ui primitives
│       └── pages/        # EmployeesPage, InsightsPage
├── artifacts/            # Architecture docs, ADRs, tradeoffs
├── render.yaml
└── README.md
```

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API runs at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### Seed the database

```bash
cd backend
python scripts/seed.py
```

Inserts 10,000 employees in a single bulk INSERT (~0.24s). Idempotent — safe to run again if the table already has data.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173`. Expects the backend at `http://localhost:8000` (set in `frontend/.env`).

## Running tests

```bash
cd backend
pytest
```

46 tests across schema validation, employee CRUD, and all insights endpoints. Uses an in-memory SQLite database — no running server required.

```bash
pytest -v          # verbose output
pytest -k insights # run only insights tests
```

## Deployment

Configured for [Render](https://render.com) via `render.yaml`. The backend runs as a Docker service built from `backend/Dockerfile`.

Before deploying the frontend, update `frontend/.env.production` with the Render service URL:

```
VITE_API_URL=https://your-service-name.onrender.com
```

## Live URL

_To be updated after first deploy._
