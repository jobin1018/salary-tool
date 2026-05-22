FROM python:3.12-slim

WORKDIR /app

# Build context is repo root (Railway default)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN chmod +x start.sh

ENV PORT=8000

CMD ["./start.sh"]
