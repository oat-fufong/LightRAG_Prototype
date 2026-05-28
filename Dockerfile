# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy installed packages and application code
COPY pyproject.toml .
COPY uv.lock .

RUN uv venv
RUN . .venv/bin/activate 

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV HTTP_PROXY=$HTTP_PROXY
ENV HTTPS_PROXY=$HTTPS_PROXY
ENV NO_PROXY=$NO_PROXY

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