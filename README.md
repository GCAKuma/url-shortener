[![CI](https://github.com/GCAKuma/url-shortener/actions/workflows/ci.yml/badge.svg)](https://github.com/GCAKuma/url-shortener/actions/workflows/ci.yml)
# URL Shortener

A small FastAPI service that shortens URLs and tracks click counts, built as a
practice project for a CI/CD pipeline.

## API

| Method | Path                  | Description                                  |
| ------ | --------------------- | -------------------------------------------- |
| `GET`  | `/`                   | Minimal HTML frontend                        |
| `GET`  | `/health`             | Liveness probe, used by the container health check and CI |
| `POST` | `/shorten`            | `{"url": "https://..."}` → short code        |
| `GET`  | `/stats/{short_code}` | Original URL, click count, creation time     |
| `GET`  | `/{short_code}`       | Redirects to the original URL, counts a click |

Interactive API docs are at `/docs`.

## Running locally

```bash
python -m venv venv && ./venv/Scripts/activate && pip install -r requirements-dev.txt
```

```bash
uvicorn app.main:app --reload
```

The app is then on <http://localhost:8000>. It defaults to a SQLite file at
`./shortener.db`; set `DATABASE_URL` to point somewhere else.

## Tests and linting

These are the same three commands CI runs, so if they pass locally the pipeline
should stay green.

```bash
ruff check . && ruff format --check . && pytest -q
```

## Docker

```bash
docker build -t url-shortener .
```

The image runs as a non-root user and stores its SQLite database in `/data`.
Mount a volume there, or the data is lost when the container is replaced:

```bash
docker run -d -p 8000:8000 -v urlshort-data:/data --name urlshort url-shortener
```

## CI pipeline

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push and
pull request against `main`, in two stages:

1. **Lint & test** — `ruff check`, `ruff format --check`, then `pytest`.
2. **Build & smoke test image** — builds the Docker image (only if stage 1
   passed), starts it, and checks that `/health` responds and `/shorten`
   returns a real short code.

Dependencies are pinned to exact versions in `requirements.txt`, and the CI
Python version matches the Dockerfile base image, so builds are reproducible
and tests run against the runtime that actually ships.

## Notes / known limitations

- SQLite with a single uvicorn worker is fine for this project. Click counting
  in `crud.increment_clicks` is a read-modify-write, so concurrent hits to the
  same short code can lose counts under multiple workers — moving to Postgres
  and an atomic `UPDATE ... SET clicks = clicks + 1` is the fix.
- There is no deploy stage yet. The image is built and smoke-tested but not
  pushed to a registry.
