# salary-tool

A full-stack web application for managing and analysing salary data.

## Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python · FastAPI · SQLAlchemy     |
| Frontend | React · Vite                      |
| Testing  | pytest · pytest-asyncio · httpx   |

## Project layout

```
salary-tool/
├── backend/          # FastAPI application
│   ├── app/          # Application package
│   └── requirements.txt
├── frontend/         # React + Vite application
└── artifacts/        # Docs, diagrams, and other assets
```

## Getting started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
