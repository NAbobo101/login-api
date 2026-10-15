FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /code

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install . && useradd --create-home appuser && mkdir /data && chown appuser /data

USER appuser
ENV DATABASE_URL=sqlite:////data/database.db
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
