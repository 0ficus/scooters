FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH="/app"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./order_offer_service/app
COPY __init__.py ./order_offer_service/__init__.py

EXPOSE 8080

ENTRYPOINT ["sh", "-c"]
CMD ["uvicorn", "order_offer_service.app.main:app", "--host", "0.0.0.0", "--port", "8080"]

