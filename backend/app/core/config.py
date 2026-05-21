"""
全局配置管理模块

这个文件使用 pydantic-settings 从环境变量和 .env 文件中读取所有配置项，
提供一个全局 settings 单例对象，供其他模块直接导入使用。

为什么用 pydantic-settings？
- 自动从 .env 文件和环境变量读取配置
- 自动类型校验（比如 port 必须是 int）
- 配置项有默认值，即使 .env 不存在也能启动
- 避免把密码、密钥等敏感值硬编码在代码中

使用方式：
    from app.core.config import settings
    print(settings.app_name)       # → SupportForge
    print(settings.database_url)   # → 从 .env 读取

面试考点：
- "你的配置是怎么管理的？" → pydantic-settings 统一管理，.env 存敏感值
- "生产环境和开发环境怎么区分？" → app_env 字段控制，.env 文件按环境切换
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    项目全局配置类

    每个字段对应一个配置项：
    - 有默认值的字段：即使 .env 中没有也能正常启动
    - 没有默认值的字段：必须在 .env 中提供，否则启动时报错

    配置项来源优先级：环境变量 > .env 文件 > 默认值
    """

    # ── 应用基础配置 ──
    # app_name: 项目名称，显示在 Swagger 文档标题
    app_name: str = "SupportForge"
    # app_env: 运行环境，影响日志级别、文档开关等行为
    # 可选值：development / test / production
    app_env: str = "development"
    # app_port: 服务监听端口，默认 8000
    app_port: int = 8000

    # ── 日志配置 ──
    # log_level: 日志输出级别，development 建议 INFO，production 建议 WARNING
    # 可选值：DEBUG / INFO / WARNING / ERROR / CRITICAL
    log_level: str = "INFO"

    # ── JWT 认证配置（Week 2 使用，Day 2 先只读取不使用）──
    # jwt_secret_key: JWT 签名密钥，生产环境必须更换为强随机值
    jwt_secret_key: str = "change-me-in-production"
    # jwt_algorithm: JWT 签名算法，默认 HS256
    jwt_algorithm: str = "HS256"
    # access_token_expire_minutes: Access Token 有效期（分钟）
    access_token_expire_minutes: int = 30
    # refresh_token_expire_days: Refresh Token 有效期（天）
    refresh_token_expire_days: int = 7

    # ── 数据库配置（Day 3 使用）──
    # database_url: PostgreSQL 异步连接字符串
    # 格式：postgresql+asyncpg://用户名:密码@主机:端口/数据库名
    database_url: str = "postgresql+asyncpg://supportforge:supportforge_dev@localhost:5432/supportforge"
    # database_url_sync: PostgreSQL 同步连接字符串（Alembic 迁移用）
    database_url_sync: str = "postgresql://supportforge:supportforge_dev@localhost:5432/supportforge"

    # ── Redis 配置（Week 5 Celery 使用）──
    redis_url: str = "redis://localhost:6379/0"

    # ── Qdrant 向量数据库配置（Week 3 RAG 使用）──
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "supportforge_vectors"

    # ── OpenAI 配置（Week 3/4 Agent 使用）──
    openai_api_key: str = "sk-your-openai-api-key"
    openai_model_name: str = "gpt-4o-mini"

    # ── Celery 配置（Week 5 使用）──
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # pydantic-settings 的配置
    # env_file: 指定 .env 文件路径，自动从该文件读取配置
    # env_file_encoding: .env 文件编码
    # extra="ignore": 忽略 .env 中多余的字段，不报错
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# ── 全局配置单例 ──
# 其他模块通过 "from app.core.config import settings" 导入这个对象
# 不要在每个模块里重新创建 Settings()，避免重复读取 .env
settings = Settings()