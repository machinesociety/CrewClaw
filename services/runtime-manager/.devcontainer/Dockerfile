FROM python:3.12-slim

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 -m -s /bin/bash vscode \
    && rm -rf /var/lib/apt/lists/*

USER vscode
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/vscode/.local/bin:${PATH}"

WORKDIR /workspaces/RuntimeManager

