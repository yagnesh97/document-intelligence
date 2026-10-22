from bson import ObjectId
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.config import settings
from app.models.document import DocumentStatus
from app.services.documents import document_service
from app.services.documents_delete import document_deletion_service
from app.services.ingestion import ingestion_service
from app.services.parsers import ParserFactory

router = APIRouter(
    prefix="/files",
    tags=["files"],
)


@router.post("", status_code=status.HTTP_201_CREATED)
def upload_files(
    files: list[UploadFile] = File(...),  # noqa: B008
):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required",
        )

    if len(files) > settings.max_upload_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Maximum {settings.max_upload_files} files can be uploaded at once"
            ),
        )

    # Validate all file types before storing or queueing any files.
    for file in files:
        filename = file.filename or "unknown"

        try:
            ParserFactory.get_parser(
                filename=filename,
                content_type=file.content_type,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file '{filename}': {exc}",
            ) from exc

    file_sizes: list[int] = []

    for file in files:
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"'{file.filename}' exceeds the maximum "
                    f"file size of {settings.max_file_size} bytes"
                ),
            )

        file_sizes.append(size)

    total_size = sum(file_sizes)

    if total_size > settings.max_total_upload_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Total upload size exceeds the maximum allowed "
                f"size of {settings.max_total_upload_size} bytes"
            ),
        )

    uploaded_files = []

    for file, file_size in zip(files, file_sizes):
        file.file.seek(0)

        document, task_id = ingestion_service.ingest(
            file_object=file.file,
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            size=file_size,
        )

        uploaded_files.append(
            {
                "document_id": str(document.id),
                "task_id": task_id,
                "filename": document.filename,
                "size": document.size,
                "status": document.status,
            }
        )

    return {
        "count": len(uploaded_files),
        "files": uploaded_files,
    }


@router.get("")
def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: DocumentStatus | None = Query(default=None),  # noqa: B008
):
    documents, total = document_service.list(
        page=page,
        page_size=page_size,
        status=status,
    )

    return {
        "items": [
            {
                "document_id": str(document.id),
                "filename": document.filename,
                "content_type": document.content_type,
                "size": document.size,
                "status": document.status,
                "created_at": document.created_at,
                "processed_at": document.processed_at,
            }
            for document in documents
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/{document_id}")
def get_file(document_id: str):
    try:
        object_id = ObjectId(document_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document_id",
        ) from exc

    document = document_service.get(object_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "content_type": document.content_type,
        "size": document.size,
        "status": document.status,
        "created_at": document.created_at,
        "processed_at": document.processed_at,
        "error": document.error,
        "content": document.content,
        "metadata": document.metadata,
    }


@router.delete("/{document_id}")
def delete_file(document_id: str):
    try:
        object_id = ObjectId(document_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document_id",
        ) from exc

    deleted = document_deletion_service.delete(object_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return {
        "document_id": document_id,
        "status": "DELETED",
    }
