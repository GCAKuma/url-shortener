FROM python:3.14-slim

# No .pyc files in the image, and unbuffered stdout so `docker logs`
# (and the pipeline tailing it) sees output immediately.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# Install dependencies first so Docker can cache this layer
# and skip it on rebuilds where only app code changed.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./static ./static

# Run as a non-root user. The SQLite file lives in /data rather than the
# code directory so it can be bind-mounted and survive a redeploy.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data /code
USER appuser

ENV DATABASE_URL=sqlite:////data/shortener.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
