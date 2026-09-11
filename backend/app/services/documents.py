import re
from pathlib import Path

from fastapi import UploadFile
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.models.entities import Document, DocumentChunk, IndexingStatus
from backend.app.providers.base import EmbeddingProvider, VectorRecord, VectorStore

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        embeddings: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self.session = session
        self.settings = settings
        self.embeddings = embeddings
        self.vector_store = vector_store

    async def upload(self, file: UploadFile) -> Document:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise AppError("INVALID_DOCUMENT", "Only PDF, TXT, and Markdown files are supported.")
        content = await file.read(self.settings.max_upload_size + 1)
        if len(content) > self.settings.max_upload_size:
            raise AppError("DOCUMENT_TOO_LARGE", "The document exceeds the configured upload limit.", 413)
        if not content:
            raise AppError("EMPTY_DOCUMENT", "The uploaded document is empty.")
        document = Document(filename=Path(file.filename or "document").name, file_type=suffix[1:], storage_path="")
        self.session.add(document)
        await self.session.flush()
        self.settings.upload_path.mkdir(parents=True, exist_ok=True)
        path = self.settings.upload_path / f"{document.id}{suffix}"
        path.write_bytes(content)
        document.storage_path = str(path)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def list(self) -> list[Document]:
        return list((await self.session.scalars(select(Document).order_by(Document.created_at.desc()))).all())

    async def get(self, document_id: str) -> Document:
        document = await self.session.get(Document, document_id)
        if document is None:
            raise AppError("DOCUMENT_NOT_FOUND", "Document was not found.", 404)
        return document

    async def delete(self, document_id: str) -> None:
        document = await self.get(document_id)
        await self.vector_store.delete_document(document_id)
        Path(document.storage_path).unlink(missing_ok=True)
        await self.session.delete(document)
        await self.session.commit()

    async def index(self, document_id: str) -> Document:
        document = await self.get(document_id)
        if document.indexing_status == IndexingStatus.INDEXED:
            raise AppError("DOCUMENT_ALREADY_INDEXED", "Document has already been indexed.", 409)
        text = await self._extract_text(Path(document.storage_path), document.file_type)
        chunks = self._chunk(text)
        if not chunks:
            raise AppError("NO_EXTRACTABLE_TEXT", "No extractable text was found in the document.")
        records: list[VectorRecord] = []
        for position, content in enumerate(chunks):
            chunk = DocumentChunk(document_id=document.id, position=position, content=content)
            self.session.add(chunk)
            await self.session.flush()
            chunk.vector_id = chunk.id
            records.append(VectorRecord(chunk.id, content, {"document_id": document.id, "document_name": document.filename, "position": position}))
        await self.vector_store.upsert(records, await self.embeddings.embed(chunks))
        document.chunk_count = len(chunks)
        document.indexing_status = IndexingStatus.INDEXED
        await self.session.commit()
        await self.session.refresh(document)
        return document

    @staticmethod
    async def _extract_text(path: Path, file_type: str) -> str:
        if file_type == "pdf":
            return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _chunk(text: str, size: int = 900, overlap: int = 120) -> list[str]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []
        chunks, start = [], 0
        while start < len(normalized):
            end = min(len(normalized), start + size)
            if end < len(normalized):
                boundary = normalized.rfind(" ", start, end)
                end = boundary if boundary > start else end
            chunks.append(normalized[start:end].strip())
            if end == len(normalized):
                break
            start = max(end - overlap, start + 1)
        return chunks

