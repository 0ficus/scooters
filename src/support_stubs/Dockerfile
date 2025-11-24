FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./support_stubs/app
COPY __init__.py ./support_stubs/__init__.py

EXPOSE 8081
CMD ["uvicorn", "support_stubs.app.main:app", "--host", "0.0.0.0", "--port", "8081"]

