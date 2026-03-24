FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x and enable pnpm via corepack.
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && corepack enable \
    && corepack prepare pnpm@10 --activate \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# COPY requirements.txt /tmp/requirements.txt
# COPY requirements-dev.txt /tmp/requirements-dev.txt

# RUN pip install --no-cache-dir -r /tmp/requirements.txt \
#     && pip install --no-cache-dir -r /tmp/requirements-dev.txt