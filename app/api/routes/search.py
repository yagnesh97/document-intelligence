from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from app.services.search import search_service

router = APIRouter(
    prefix="/search",
    tags=["search"],
)


@router.get("")
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
    document_id: str | None = Query(default=None),
):
    q = q.strip()
    if not q:
        raise HTTPException(
            status_code=400,
            detail="Query must not be empty",
        )

    object_id = None

    if document_id is not None:
        try:
            object_id = ObjectId(document_id)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid document_id",
            ) from exc

    return {
        "query": q,
        "results": search_service.search(
            query=q,
            limit=limit,
            document_id=object_id,
        ),
    }
