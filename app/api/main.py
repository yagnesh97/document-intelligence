from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.middleware import ResponseHeadersMiddleware
from app.api.routes.chat import router as chat_router
from app.api.routes.files import router as files_router
from app.api.routes.search import router as search_router
from app.config import settings
from app.db.mongodb import db, init_db
from app.services.embeddings import embedding_service
from app.services.reranker import reranker_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.command("ping")
    init_db()

    # Load model weights during startup.
    embedding_service.warm_up()

    if settings.reranker_enabled:
        reranker_service.warm_up()

    yield


app = FastAPI(
    title="Document Intelligence API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(ResponseHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "Idempotency-Key",
    ],
    expose_headers=[
        "X-Request-ID",
        "X-Process-Time",
    ],
)


@app.get("/health")
def health():
    db.command("ping")
    return {"status": "ok", "database": "ok"}


app.include_router(files_router)
app.include_router(search_router)
app.include_router(chat_router)
