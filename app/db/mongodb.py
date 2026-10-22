import json
from pathlib import Path

from pymongo import MongoClient

from app.config import settings

client = MongoClient(settings.mongodb_uri)
db = client[settings.mongodb_database]


def seed_llm_models() -> None:
    collection = db.llm_models
    collection.create_index("name", unique=True)

    seed_file = Path(__file__).resolve().parents[1] / "data" / "llm_models.json"

    with seed_file.open(encoding="utf-8") as file:
        models = json.load(file)

    metadata_fields = (
        "display_name",
        "description",
        "capabilities",
        "context_window",
        "max_output_tokens",
    )

    for model in models:
        collection.update_one(
            {"name": model["name"]},
            {"$setOnInsert": model},
            upsert=True,
        )

        collection.update_one(
            {"name": model["name"]},
            {
                "$set": {
                    field: model[field] for field in metadata_fields if field in model
                }
            },
        )


def init_db() -> None:
    db.document_chunks.create_index("document_id")
    seed_llm_models()
