import pytest


@pytest.mark.api
@pytest.mark.asyncio
async def test_document_upload_index_and_query(client):
    uploaded = await client.post(
        "/api/v1/documents",
        files={"file": ("employee_handbook.md", b"Employees receive 25 annual leave days per year.", "text/markdown")},
    )
    assert uploaded.status_code == 201
    document = uploaded.json()
    assert document["indexing_status"] == "pending"

    indexed = await client.post(f"/api/v1/documents/{document['id']}/index")
    assert indexed.status_code == 200
    assert indexed.json()["chunk_count"] == 1

    response = await client.post("/api/v1/rag/query", json={"question": "How many annual leave days do employees receive?", "top_k": 3})
    assert response.status_code == 200
    body = response.json()
    assert "25" in body["answer"]
    assert body["sources"][0]["document_name"] == "employee_handbook.md"
    assert body["total_latency_ms"] >= 0


@pytest.mark.api
@pytest.mark.asyncio
async def test_rejects_invalid_and_empty_documents(client):
    invalid = await client.post("/api/v1/documents", files={"file": ("payload.exe", b"x", "application/octet-stream")})
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "INVALID_DOCUMENT"
    empty = await client.post("/api/v1/documents", files={"file": ("empty.txt", b"", "text/plain")})
    assert empty.status_code == 400
    assert empty.json()["error"]["code"] == "EMPTY_DOCUMENT"


@pytest.mark.api
@pytest.mark.asyncio
async def test_query_validation_is_structured(client):
    response = await client.post("/api/v1/rag/query", json={"question": "", "top_k": 0})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

