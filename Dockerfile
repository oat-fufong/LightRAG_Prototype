# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy installed packages and application code
COPY pyproject.toml .
COPY uv.lock .

RUN uv pip install --no-deps git+https://github.com/HKUDS/LightRAG.git@v1.4.16

RUN uv sync

COPY . .

# Create data directories
RUN mkdir -p /app/data/rag_storage /app/data/inputs /app/data/tiktoken

# Set environment variables
ENV TIKTOKEN_CACHE_DIR=/app/data/tiktoken
ENV WORKING_DIR=/app/data/rag_storage
ENV INPUT_DIR=/app/data/inputs

# Expose the API port
EXPOSE 9621

ENTRYPOINT ["uv", "run", "lightrag-server"]