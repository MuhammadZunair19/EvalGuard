# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

WORKDIR /app

# Install dependencies before application code so normal source changes reuse
# this expensive layer. Ollama owns GPU inference, so the embedding runtime uses
# the much smaller CPU-only PyTorch wheel instead of downloading CUDA libraries.
COPY backend/requirements.docker.txt ./backend/requirements.docker.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --index-url https://download.pytorch.org/whl/cpu torch && \
    pip install --prefer-binary -r backend/requirements.docker.txt

COPY backend ./backend

EXPOSE 8000
CMD ["sh", "-c", "alembic -c backend/alembic.ini upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
