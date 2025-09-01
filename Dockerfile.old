FROM ubuntu:22.04

# Set non-interactive frontend to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    postgresql-client \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set up Python alternatives
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Install uv and poetry
RUN python3 -m pip install -U pip uv
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add poetry to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Set up working directory
WORKDIR /app

# Copy dependency files and install dependencies
COPY pyproject.toml poetry.lock requirements.lock ./
RUN uv pip sync --system requirements.lock
RUN uv pip install --system bandit ruff mypy pytest pytest-cov pytest-asyncio pre-commit types-setuptools setuptools diff-cover pytest-mock pytest-xdist psutil mutmut hypothesis types-PyYAML types-requests defusedxml types-defusedxml types-psycopg2

# Copy the rest of the application code
COPY . .

# Install the project in editable mode
RUN uv pip install --system -e .

# Set the entrypoint
ENTRYPOINT ["/bin/bash"]
