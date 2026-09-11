from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_providers
from backend.app.core.config import Settings, get_settings
from backend.app.db.session import get_session
from backend.app.schemas.documents import DocumentResponse, IndexResponse
from backend.app.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


def service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    providers=Depends(get_providers),
) -> DocumentService:
    _, embeddings, vectors = providers
    return DocumentService(session, settings, embeddings, vectors)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), documents: DocumentService = Depends(service)):
    return await documents.upload(file)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(documents: DocumentService = Depends(service)):
    return await documents.list()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, documents: DocumentService = Depends(service)):
    return await documents.get(document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, documents: DocumentService = Depends(service)) -> Response:
    await documents.delete(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{document_id}/index", response_model=IndexResponse)
async def index_document(document_id: str, documents: DocumentService = Depends(service)):
    document = await documents.index(document_id)
    return IndexResponse(document_id=document.id, chunk_count=document.chunk_count, indexing_status=document.indexing_status)
