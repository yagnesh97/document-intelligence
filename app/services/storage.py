import boto3

from app.config import settings


class StorageService:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )

    def upload_file(
        self,
        file_object,
        object_name: str,
        content_type: str,
    ) -> None:
        self.client.upload_fileobj(
            file_object,
            settings.s3_bucket,
            object_name,
            ExtraArgs={"ContentType": content_type},
        )

    def download_file(self, object_name: str) -> bytes:
        response = self.client.get_object(
            Bucket=settings.s3_bucket,
            Key=object_name,
        )

        try:
            return response["Body"].read()
        finally:
            response["Body"].close()

    def delete_file(self, object_name: str) -> None:
        self.client.delete_object(
            Bucket=settings.s3_bucket,
            Key=object_name,
        )


storage_service = StorageService()
