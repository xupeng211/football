# Football Prediction System v3.0 - Optimized Dockerfile
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN pip install uv

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml ./

# 创建虚拟环境并安装依赖
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv sync --no-dev

# 复制源代码
COPY src/ ./src/
COPY tests/ ./tests/

# 安装项目本身
RUN . .venv/bin/activate && uv pip install -e .

# 创建非root用户
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD [".venv/bin/uvicorn", "src.football_predict_system.main:app", "--host", "0.0.0.0", "--port", "8000"]
