# 🐳 Local CI Docker Image - Matches GitHub Actions Environment
# 与远程GitHub Actions完全一致的本地CI环境

FROM ubuntu:22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHON_VERSION=3.11
ENV UV_CACHE_DIR=/tmp/.uv-cache
ENV PYTHONPATH=/workspace/src
ENV ENVIRONMENT=testing

# 使用清华镜像源提高下载速度和稳定性
RUN sed -i 's@//.*archive.ubuntu.com@//mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list && \
    sed -i 's@//.*security.ubuntu.com@//mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list

# 安装系统依赖 (与GitHub Actions ubuntu-latest一致)
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 设置Python 3.11为默认python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# 安装uv (与GitHub Actions保持一致)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 创建工作目录
WORKDIR /workspace

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY tests/ ./tests/
COPY Makefile ./
COPY ai_security_rules.json ./

# 安装依赖
RUN uv sync --extra dev

# 设置Git安全目录 (避免Git安全警告)
RUN git config --global --add safe.directory /workspace

# 创建CI执行脚本
COPY scripts/ci/local_ci_runner.sh /usr/local/bin/local_ci_runner.sh
RUN chmod +x /usr/local/bin/local_ci_runner.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 --version && uv --version

# 默认执行CI流程
CMD ["/usr/local/bin/local_ci_runner.sh"] 