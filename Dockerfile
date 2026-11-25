FROM python:3.14.3-slim-bookworm@sha256:f21c0d5a44c56805654c15abccc1b2fd576c8d93aca0a3f74b4aba2dc92510e2

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/root/.cache/huggingface

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory /app

COPY requirements.txt requirements-audio.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt -r requirements-audio.txt accelerate==1.15.0
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY ["collect data script/", "/app/collect data script/"]
COPY ["kaggle_batch/", "/app/kaggle_batch/"]

ENTRYPOINT ["python", "-u", "/app/collect data script/docker_pipeline.py"]
