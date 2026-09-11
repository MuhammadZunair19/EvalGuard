"""initial EvalGuard schema"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(16), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("indexing_status", sa.String(20), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "evaluation_datasets",
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "prompt_versions",
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", "version"),
    )
    op.create_table(
        "quality_thresholds",
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("comparator", sa.String(8), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "document_chunks",
        sa.Column(
            "document_id",
            sa.String(36),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("vector_id", sa.String(128)),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("document_id", "position"),
    )
    op.create_table(
        "test_cases",
        sa.Column(
            "dataset_id",
            sa.String(36),
            sa.ForeignKey("evaluation_datasets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text()),
        sa.Column("expected_behavior", sa.Text()),
        sa.Column("expected_facts", sa.JSON(), nullable=False),
        sa.Column("expected_document", sa.String(255)),
        sa.Column("expected_chunk", sa.String(128)),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("test_type", sa.String(40), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "evaluation_runs",
        sa.Column(
            "dataset_id", sa.String(36), sa.ForeignKey("evaluation_datasets.id"), nullable=False
        ),
        sa.Column("prompt_version_id", sa.String(36), sa.ForeignKey("prompt_versions.id")),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("embedding_model", sa.String(120), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("chunk_configuration", sa.JSON(), nullable=False),
        sa.Column("thresholds", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("test_count", sa.Integer(), nullable=False),
        sa.Column("pass_count", sa.Integer(), nullable=False),
        sa.Column("fail_count", sa.Integer(), nullable=False),
        sa.Column("pass_percentage", sa.Float(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "test_results",
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("test_case_id", sa.String(36), sa.ForeignKey("test_cases.id"), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("actual_answer", sa.Text(), nullable=False),
        sa.Column("retrieved_context", sa.JSON(), nullable=False),
        sa.Column("failure_type", sa.String(80)),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("unsupported_claims", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "metric_results",
        sa.Column(
            "test_result_id",
            sa.String(36),
            sa.ForeignKey("test_results.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric", sa.String(80), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "metric_results",
        "test_results",
        "evaluation_runs",
        "test_cases",
        "document_chunks",
        "quality_thresholds",
        "prompt_versions",
        "evaluation_datasets",
        "documents",
    ]:
        op.drop_table(table)
