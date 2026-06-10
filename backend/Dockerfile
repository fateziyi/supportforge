# ── 多阶段构建：先安装依赖，再运行 ──
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装系统依赖（PostgreSQL 客户端库）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 Poetry
RUN pip install --no-cache-dir poetry

# 复制依赖声明文件
COPY pyproject.toml poetry.lock* ./

# 安装生产依赖（不含 dev）
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main

# ── 运行阶段 ──
FROM python:3.12-slim AS runtime

WORKDIR /app

# 运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制已安装的 Python 包
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY app/ ./app/
# 复制初始化脚本（compose 内可能需要运行 init_demo_data.py）
COPY scripts/ ./scripts/

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]