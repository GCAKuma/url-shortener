FROM python:3.11-slim

WORKDIR /code

# Install dependencies first so Docker can cache this layer
# and skip it on rebuilds where only app code changed.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./static ./static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
