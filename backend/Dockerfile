# Install system dependencies required for building Python packages
# Note: We must install python3-dev for the SPECIFIC python version if possible,
# or rely on the base image's headers if we use the full image.
# For python:3.10-slim (Debian Bookworm), python3-dev installs 3.11/3.12 headers which mismatch the container's python (3.10).
# So we switch to the full non-slim image which HAS the correct headers.
FROM python:3.10

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Install build tools just in case (gcc, make, etc) although python:3.10 usually has them or sufficient.
# Actually, the python base image is often minimal. Let's ensure compiler is present.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
RUN pip install uv==0.5.11

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/.venv/bin:$PATH"

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Install dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ENV PYTHONPATH=/app

COPY ./scripts /app/scripts

COPY ./pyproject.toml ./uv.lock ./alembic.ini /app/

COPY ./app /app/app
COPY ./tests /app/tests

# Sync the project
# Explicitly use the system python (3.10) to avoid uv downloading a newer python (like 3.13)
# which might lack headers or cause compilation issues.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --python 3.10

# Make prestart script executable
RUN chmod +x /app/scripts/prestart.sh

# Run prestart script (migrations and initial data) then start the app
CMD ["/bin/bash", "-c", "/app/scripts/prestart.sh && uv run --python 3.10 fastapi run --workers 4 app/main.py"]

