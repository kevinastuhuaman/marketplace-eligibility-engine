FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY inventory-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY inventory-service/app/ /app/app/
COPY inventory-service/alembic.ini /app/alembic.ini
COPY inventory-service/alembic/ /app/alembic/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
