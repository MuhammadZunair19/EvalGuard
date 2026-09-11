import pytest


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_uses_saved_prompt_and_quality_gates(client):
    document_response = await client.post(
        "/api/v1/documents",
        files={
            "file": (
                "employee_handbook.md",
                b"Employees receive 25 annual leave days per year.",
                "text/markdown",
            )
        },
    )
    document = document_response.json()
    await client.post(f"/api/v1/documents/{document['id']}/index")

    dataset_response = await client.post(
        "/api/v1/datasets",
        json={"name": "Release QA", "description": "Integration baseline"},
    )
    dataset = dataset_response.json()
    case_response = await client.post(
        f"/api/v1/datasets/{dataset['id']}/test-cases",
        json={
            "category": "leave",
            "question": "How many annual leave days do employees receive?",
            "expected_answer": "25 annual leave days",
            "expected_facts": ["Employees receive 25 annual leave days per year"],
            "expected_document": "employee_handbook.md",
            "test_type": "factual",
        },
    )
    assert case_response.status_code == 201

    prompt_response = await client.post(
        "/api/v1/prompts",
        json={
            "name": "grounded-qa",
            "version": 2,
            "system_prompt": "Use only the supplied evidence.",
            "template": "Evidence:\n{context}\nQuestion: {question}",
        },
    )
    prompt = prompt_response.json()
    gate_response = await client.put(
        "/api/v1/quality-gates/answer_relevance",
        json={"value": 0.7, "comparator": ">="},
    )
    assert gate_response.status_code == 200

    run_response = await client.post(
        "/api/v1/evaluation-runs",
        json={
            "dataset_id": dataset["id"],
            "prompt_version_id": prompt["id"],
            "top_k": 3,
            "model": "llama3.1:8b",
        },
    )
    assert run_response.status_code == 201
    run = run_response.json()
    assert run["prompt_version_id"] == prompt["id"]
    assert run["thresholds"]["answer_relevance"] == 0.7
    assert run["test_count"] == 1
    assert run["status"] == "passed"


@pytest.mark.api
@pytest.mark.asyncio
async def test_rejects_unconfigured_model_and_invalid_prompt_template(client):
    prompt_response = await client.post(
        "/api/v1/prompts",
        json={
            "name": "broken",
            "version": 1,
            "system_prompt": "Ground answers.",
            "template": "Question only: {question}",
        },
    )
    assert prompt_response.status_code == 422

    dataset_response = await client.post(
        "/api/v1/datasets",
        json={"name": "Model validation", "description": None},
    )
    response = await client.post(
        "/api/v1/evaluation-runs",
        json={"dataset_id": dataset_response.json()["id"], "model": "unconfigured:latest"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MODEL_NOT_CONFIGURED"
