from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    created_at: datetime
    chunk_count: int
    indexing_status: str


class IndexResponse(BaseModel):
    document_id: str
    chunk_count: int
    indexing_status: str

