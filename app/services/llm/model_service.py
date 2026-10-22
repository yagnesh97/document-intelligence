from bson import ObjectId
from pymongo import DESCENDING

from app.db.mongodb import db
from app.models.llm_model import LLMModel


class LLMModelService:
    def __init__(self):
        self.collection = db.llm_models

    def create(self, model: LLMModel) -> LLMModel:
        data = model.model_dump(
            by_alias=True,
            exclude={"id"},
            exclude_none=True,
        )

        result = self.collection.insert_one(data)

        data["_id"] = result.inserted_id

        return LLMModel(**data)

    def get_by_id(self, model_id: str) -> LLMModel | None:
        if not ObjectId.is_valid(model_id):
            return None

        document = self.collection.find_one({"_id": ObjectId(model_id)})

        if document is None:
            return None

        return LLMModel(**document)

    def get_by_name(self, name: str) -> LLMModel | None:
        document = self.collection.find_one({"name": name})

        if document is None:
            return None

        return LLMModel(**document)

    def get_enabled(self) -> list[LLMModel]:
        documents = self.collection.find({"enabled": True}).sort("name", DESCENDING)

        return [LLMModel(**document) for document in documents]

    def update(
        self,
        model_id: str,
        updates: dict,
    ) -> LLMModel | None:
        if not ObjectId.is_valid(model_id):
            return None

        updates.pop("_id", None)
        updates.pop("id", None)

        if not updates:
            return self.get_by_id(model_id)

        result = self.collection.update_one(
            {"_id": ObjectId(model_id)},
            {"$set": updates},
        )

        if result.matched_count == 0:
            return None

        return self.get_by_id(model_id)

    def delete(self, model_id: str) -> bool:
        if not ObjectId.is_valid(model_id):
            return False

        result = self.collection.delete_one({"_id": ObjectId(model_id)})

        return result.deleted_count > 0
