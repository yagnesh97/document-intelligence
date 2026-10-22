
#!/usr/bin/env bash

set -e

case "${1:-start}" in
  start)
    echo "Starting infrastructure..."
    docker compose up -d

    echo "Starting FastAPI..."
    uv run uvicorn app.api.main:app --reload
    ;;

  worker)
    echo "Starting Celery worker..."
    uv run celery -A app.worker.celery:celery worker --loglevel=info --pool=solo
    ;;

  flower)
    echo "Starting Flower..."
    uv run celery -A app.worker.celery:celery flower --port=5555
    ;;

  stop)
    echo "Stopping infrastructure..."
    docker compose stop
    ;;

  restart)
    echo "Restarting infrastructure..."
    docker compose restart
    ;;

  check)
    echo "Checking lint..."
    uv run ruff check .

    echo "Checking formatting..."
    uv run ruff format --check .
    ;;

  format)
    echo "Running lint fixes..."
    uv run ruff check --fix .

    echo "Formatting Python files..."
    uv run ruff format .
    ;;

  test)
    echo "Running tests..."
    uv run pytest
    ;;

  *)
    echo "Usage: ./cmd.sh {start|worker|flower|stop|restart|check|format|test}"
    exit 1
    ;;
esac