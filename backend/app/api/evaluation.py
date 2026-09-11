from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_providers
from backend.app.core.config import Settings, get_settings
from backend.app.core.errors import AppError
from backend.app.db.session import get_session
from backend.app.models.entities import (
    EvaluationDataset,
    EvaluationRun,
    PromptVersion,
    QualityThreshold,
    TestCase,
)
from backend.app.schemas.evaluation import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
    EvaluationRunCreate,
    EvaluationRunResponse,
    PromptCreate,
    PromptResponse,
    QualityThresholdResponse,
    QualityThresholdUpdate,
    TestCaseCreate,
    TestCaseResponse,
    TestCaseUpdate,
)
from backend.app.services.evaluation import EvaluationService, compare_runs
from backend.app.services.rag import RAGService

router = APIRouter(tags=["evaluation"])


@router.post("/datasets", response_model=DatasetResponse, status_code=201)
async def create_dataset(payload: DatasetCreate, session: AsyncSession = Depends(get_session)):
    dataset = EvaluationDataset(**payload.model_dump())
    session.add(dataset)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AppError(
            "DUPLICATE_DATASET", "A dataset with this name already exists.", 409
        ) from exc
    await session.refresh(dataset)
    return dataset


@router.get("/datasets", response_model=list[DatasetResponse])
async def list_datasets(session: AsyncSession = Depends(get_session)):
    return list(
        (
            await session.scalars(
                select(EvaluationDataset).order_by(EvaluationDataset.created_at.desc())
            )
        ).all()
    )


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str, session: AsyncSession = Depends(get_session)):
    dataset = await session.get(EvaluationDataset, dataset_id)
    if dataset is None:
        raise AppError("DATASET_NOT_FOUND", "Evaluation dataset was not found.", 404)
    return dataset


@router.patch("/datasets/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: str, payload: DatasetUpdate, session: AsyncSession = Depends(get_session)
):
    dataset = await session.get(EvaluationDataset, dataset_id)
    if dataset is None:
        raise AppError("DATASET_NOT_FOUND", "Evaluation dataset was not found.", 404)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(dataset, field, value)
    await session.commit()
    await session.refresh(dataset)
    return dataset


@router.delete("/datasets/{dataset_id}", status_code=204)
async def delete_dataset(dataset_id: str, session: AsyncSession = Depends(get_session)) -> Response:
    dataset = await session.get(EvaluationDataset, dataset_id)
    if dataset is None:
        raise AppError("DATASET_NOT_FOUND", "Evaluation dataset was not found.", 404)
    await session.delete(dataset)
    await session.commit()
    return Response(status_code=204)


@router.post("/datasets/{dataset_id}/test-cases", response_model=TestCaseResponse, status_code=201)
async def create_test_case(
    dataset_id: str, payload: TestCaseCreate, session: AsyncSession = Depends(get_session)
):
    if await session.get(EvaluationDataset, dataset_id) is None:
        raise AppError("DATASET_NOT_FOUND", "Evaluation dataset was not found.", 404)
    case = TestCase(dataset_id=dataset_id, **payload.model_dump())
    session.add(case)
    await session.commit()
    await session.refresh(case)
    return case


@router.get("/datasets/{dataset_id}/test-cases", response_model=list[TestCaseResponse])
async def list_test_cases(dataset_id: str, session: AsyncSession = Depends(get_session)):
    return list(
        (
            await session.scalars(
                select(TestCase)
                .where(TestCase.dataset_id == dataset_id)
                .order_by(TestCase.created_at)
            )
        ).all()
    )


@router.get("/test-cases/{case_id}", response_model=TestCaseResponse)
async def get_test_case(case_id: str, session: AsyncSession = Depends(get_session)):
    case = await session.get(TestCase, case_id)
    if case is None:
        raise AppError("TEST_CASE_NOT_FOUND", "Test case was not found.", 404)
    return case


@router.patch("/test-cases/{case_id}", response_model=TestCaseResponse)
async def update_test_case(
    case_id: str, payload: TestCaseUpdate, session: AsyncSession = Depends(get_session)
):
    case = await session.get(TestCase, case_id)
    if case is None:
        raise AppError("TEST_CASE_NOT_FOUND", "Test case was not found.", 404)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    await session.commit()
    await session.refresh(case)
    return case


@router.delete("/test-cases/{case_id}", status_code=204)
async def delete_test_case(case_id: str, session: AsyncSession = Depends(get_session)) -> Response:
    case = await session.get(TestCase, case_id)
    if case is None:
        raise AppError("TEST_CASE_NOT_FOUND", "Test case was not found.", 404)
    await session.delete(case)
    await session.commit()
    return Response(status_code=204)


@router.post("/prompts", response_model=PromptResponse, status_code=201)
async def create_prompt(payload: PromptCreate, session: AsyncSession = Depends(get_session)):
    prompt = PromptVersion(**payload.model_dump())
    session.add(prompt)
    await session.commit()
    await session.refresh(prompt)
    return prompt


@router.get("/prompts", response_model=list[PromptResponse])
async def list_prompts(session: AsyncSession = Depends(get_session)):
    return list(
        (
            await session.scalars(select(PromptVersion).order_by(PromptVersion.created_at.desc()))
        ).all()
    )


@router.get("/quality-gates", response_model=list[QualityThresholdResponse])
async def list_quality_gates(session: AsyncSession = Depends(get_session)):
    return list(
        (await session.scalars(select(QualityThreshold).order_by(QualityThreshold.name))).all()
    )


@router.put("/quality-gates/{name}", response_model=QualityThresholdResponse)
async def upsert_quality_gate(
    name: str, payload: QualityThresholdUpdate, session: AsyncSession = Depends(get_session)
):
    gate = await session.scalar(select(QualityThreshold).where(QualityThreshold.name == name))
    if gate is None:
        gate = QualityThreshold(name=name, **payload.model_dump())
        session.add(gate)
    else:
        gate.value, gate.comparator = payload.value, payload.comparator
    await session.commit()
    await session.refresh(gate)
    return gate


@router.post("/evaluation-runs", response_model=EvaluationRunResponse, status_code=201)
async def create_run(
    payload: EvaluationRunCreate,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    providers=Depends(get_providers),
):
    llm, embeddings, vectors = providers
    return await EvaluationService(session, RAGService(llm, embeddings, vectors), settings).execute(
        payload
    )


@router.get("/evaluation-runs", response_model=list[EvaluationRunResponse])
async def list_runs(session: AsyncSession = Depends(get_session)):
    return list(
        (
            await session.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc()))
        ).all()
    )


@router.get("/evaluation-runs/{run_id}", response_model=EvaluationRunResponse)
async def get_run(run_id: str, session: AsyncSession = Depends(get_session)):
    run = await session.get(EvaluationRun, run_id)
    if run is None:
        raise AppError("RUN_NOT_FOUND", "Evaluation run was not found.", 404)
    return run


@router.get("/evaluation-runs/{run_id}/compare/{baseline_id}")
async def compare(run_id: str, baseline_id: str, session: AsyncSession = Depends(get_session)):
    current, baseline = (
        await session.get(EvaluationRun, run_id),
        await session.get(EvaluationRun, baseline_id),
    )
    if current is None or baseline is None:
        raise AppError("RUN_NOT_FOUND", "One or both evaluation runs were not found.", 404)
    return compare_runs(current, baseline)
