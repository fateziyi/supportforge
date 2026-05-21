"""
Alembic 迁移运行环境配置

这个文件是 Alembic 迁移框架的核心入口，每次执行 alembic 命令时都会读取这个文件。

它负责两件关键事情：
1. 提供数据库连接 URL（从项目 settings 中读取同步 URL）
2. 提供 target_metadata（项目的 Base.metadata，让 Alembic 自动发现所有 ORM 模型）

为什么 Alembic 用同步 URL 而项目运行用异步 URL？
- Alembic 的迁移脚本本身是同步代码（不需要在异步框架中运行）
- asyncpg 是异步驱动，Alembic 的同步引擎无法使用异步 URL
- 所以 Alembic 使用 psycopg2（同步驱动）连接数据库
- 这就是 config.py 中同时有 database_url（异步）和 database_url_sync（同步）的原因

为什么需要导入 Base.metadata？
- Alembic 的 autogenerate 功能需要知道"当前定义了哪些 ORM 模型"
- Base.metadata 包含了所有继承 Base 的模型的表结构信息
- Alembic 通过对比 Base.metadata 和数据库实际表结构，自动生成迁移脚本

⚠️ 重要：env.py 中的 Base.metadata 只包含已经被导入的模型
- Day 3 阶段没有业务模型，所以 metadata 是空的
- Day 4/Day 5 创建模型后，需要确保 models/__init__.py 导入所有模型
- 这样 env.py 中的 `import app.models` 就能让 Alembic 发现所有新表

面试考点：
- "数据库迁移是怎么做的？" → Alembic + autogenerate + Base.metadata
- "为什么迁移用同步驱动？" → Alembic 是同步框架，不支持 asyncpg
- "autogenerate 是怎么发现新表的？" → 通过导入 models 让 Base.metadata 包含新定义
"""

from logging.config import fileConfig

from alembic import context  # type: ignore[import-untyped]
from sqlalchemy import engine_from_config, pool

# ── 导入项目配置和 ORM 基类 ──
# config: 提供数据库连接 URL（同步版本）
# Base: 提供所有 ORM 模型的 metadata
from app.core.config import settings
from app.db.base import Base

# ── 导入所有 ORM 模型（让 Alembic 能识别）──
# Day 3 阶段没有业务模型，这个 import 是占位
# Day 4/Day 5 创建模型后，app/models/__init__.py 会导入所有模型
# 这里通过 import app.models 让所有模型被加载到 Base.metadata 中
# ⚠️ 如果不导入 app.models，Alembic 的 autogenerate 就不会发现新定义的表
import app.models  # noqa: F401  # type: ignore[import-relative]

# Alembic Config 对象，提供 alembic.ini 中的配置信息
config = context.config

# ── 从项目配置动态注入数据库 URL ──
# 不在 alembic.ini 里写死 URL，避免敏感信息泄露和版本不一致
# config.set_main_option 会覆盖 alembic.ini 中的 sqlalchemy.url 占位值
# 使用 settings.database_url_sync（同步 URL），因为 Alembic 是同步框架
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

# ── 设置日志配置（如果 alembic.ini 中有定义）──
# fileConfig 让 Alembic 使用 alembic.ini 中定义的日志格式
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── target_metadata：Alembic autogenerate 的目标 ──
# 告诉 Alembic："你应该让数据库变成和 Base.metadata 一致的状态"
# autogenerate 会对比 Base.metadata 和数据库实际表结构的差异
# 然后自动生成 CREATE TABLE / DROP TABLE / ADD COLUMN 等迁移脚本
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式运行迁移

    在不连接数据库的情况下生成 SQL 脚本。
    这种模式适合：
    - 审查迁移脚本内容
    - 在生产环境手动执行 SQL（而不是通过 Alembic 自动执行）

    context.execute() 在离线模式下只会输出 SQL，不会真正执行
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线模式运行迁移

    连接数据库并执行迁移脚本。
    这是日常开发中最常用的模式：
    - alembic upgrade head → 在线模式，连接数据库执行所有待执行的迁移
    - alembic revision --autogenerate → 在线模式，连接数据库对比差异生成迁移脚本
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # 迁移不需要连接池，每次迁移完成后立即释放连接
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ── Alembic 入口逻辑 ──
# 根据 context.is_offline_mode() 判断是离线还是在线模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()