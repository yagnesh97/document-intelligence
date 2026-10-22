import json
from collections.abc import Iterator

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.chat import ChatRequest, ChatResponse
from app.services.llm.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    document_id = None

    if request.document_id:
        if not ObjectId.is_valid(request.document_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid document ID.",
            )

        document_id = ObjectId(request.document_id)

    try:
        result = rag_service.ask(
            question=request.question,
            model_id=request.model_id,
            limit=request.limit,
            document_id=document_id,
        )

        return ChatResponse(**result)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    document_id = None

    if request.document_id:
        if not ObjectId.is_valid(request.document_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid document ID.",
            )

        document_id = ObjectId(request.document_id)

    def generate() -> Iterator[str]:
        try:
            for token in rag_service.stream(
                question=request.question,
                model_id=request.model_id,
                limit=request.limit,
                document_id=document_id,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"

            yield "data: [DONE]\n\n"

        except ValueError as exc:
            error = json.dumps({"error": str(exc)})
            yield f"data: {error}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
