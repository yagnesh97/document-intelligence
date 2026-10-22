from celery import Celery

celery = Celery(
    "smart_finance",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["app.worker.tasks.ingestion"],
)

celery.conf.update(
    task_track_started=True,
)
