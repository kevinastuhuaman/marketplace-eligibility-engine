FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit==1.41.0 httpx redis

COPY app.py .

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"]
