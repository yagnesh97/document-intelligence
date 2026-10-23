from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str
    mongodb_database: str = "document_intelligence"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "document_chunks"

    # S3 / MinIO
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str
    s3_secret_key: str
    s3_region: str = "us-west-1"
    s3_bucket: str = "document-intelligence-raw"

    # Upload limits
    max_upload_files: int = 10
    max_file_size: int = 25 * 1024 * 1024  # 25 MB
    max_total_upload_size: int = 100 * 1024 * 1024  # 100 MB

    # Embedding model
    embedding_model: str = "BAAI/bge-m3"
    sparse_embedding_model: str = "Qdrant/bm25"
    hf_token: str | None = None

    # LLM providers
    openai_api_key: str | None = None
    gemini_api_key: str | None = None

    # Reranker
    reranker_enabled: bool = True
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_top_k: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
