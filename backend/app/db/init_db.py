"""
数据库初始化脚本

这个文件的职责是：
1. 创建默认租户（Acme Demo）
2. 创建默认管理员账号（admin@acme.com）
3. 为本地演示和 Day 6 验证提供基础数据

设计原则：
- 幂等执行：重复运行不会反复插入同一批默认数据
  - 按 tenant.id 先查后插，如果已存在则跳过
  - 按 user.email 先查后插，如果已存在则跳过
- 只允许承载"初始化专用的最小逻辑"
  - 不做完整业务层，不写复杂查询
  - 如果后续初始化逻辑变复杂，应在 Week 2/3 抽到 service/repository

密码哈希说明：
- 密码只以 Argon2id 哈希形式保存，绝不保存明文
- 已存在的 Day 6 演示账号会在本脚本再次执行时自动升级旧 sha256 哈希

执行方式：
    cd backend
    poetry run python -m app.db.init_db

面试考点：
- "初始化脚本怎么保证幂等？" → 先查后插，已存在就跳过
- "为什么用 sha256 而不是 argon2？" → Day 6 临时方案，Week 2 换 argon2
- "初始化脚本应该放在哪里？" → db/init_db.py，不属于业务层
"""

from sqlalchemy import select

from ..core.security import hash_password, is_argon2_hash
from ..db.session import AsyncSessionLocal, engine
from ..models.tenant import Tenant
from ..models.user import User

# ── 默认数据定义 ──
# 这些值与 api/v1/auth.py 的 mock 常量对齐
DEFAULT_TENANT_ID = "default-tenant-id"
DEFAULT_TENANT_NAME = "Acme Demo"
DEFAULT_TENANT_SLUG = "acme-demo"
DEFAULT_ADMIN_ID = "default-admin-id"
DEFAULT_ADMIN_EMAIL = "admin@acme.com"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_ROLE = "tenant_admin"
DEFAULT_ADMIN_PASSWORD = "123456"


async def create_default_tenant() -> str:
    """
    创建默认租户（幂等）

    逻辑：
    1. 按 id 查询是否已存在默认租户
    2. 如果已存在，跳过创建，返回"skipped"
    3. 如果不存在，创建默认租户，返回"created"

    Returns:
        "created" 或 "skipped"
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.id == DEFAULT_TENANT_ID)
        )
        existing = result.scalar_one_or_none()

        if existing:
            if existing.slug != DEFAULT_TENANT_SLUG:
                existing.slug = DEFAULT_TENANT_SLUG
                await session.commit()
                print(f"  ✅ Tenant '{DEFAULT_TENANT_NAME}' slug repaired.")
                return "upgraded"
            print(f"  ⏭  Tenant '{DEFAULT_TENANT_NAME}' already exists, skipped.")
            return "skipped"

        tenant = Tenant(
            id=DEFAULT_TENANT_ID,
            name=DEFAULT_TENANT_NAME,
            slug=DEFAULT_TENANT_SLUG,
            status="active",
        )
        session.add(tenant)
        await session.commit()
        print(f"  ✅ Tenant '{DEFAULT_TENANT_NAME}' created.")
        return "created"


async def create_default_admin_user() -> str:
    """
    创建默认管理员账号（幂等）

    逻辑：
    1. 按 email 查询是否已存在默认管理员
    2. 如果已存在，跳过创建，返回"skipped"
    3. 如果不存在，创建默认管理员，返回"created"

    注意：
    - password_hash 使用 Argon2id 哈希，不能保存明文密码
    - 旧版 demo 数据存在时会升级哈希，保证本地环境可直接登录

    Returns:
        "created" 或 "skipped"
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.tenant_id == DEFAULT_TENANT_ID,
                User.email == DEFAULT_ADMIN_EMAIL,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            if not is_argon2_hash(existing.password_hash):
                existing.password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
                await session.commit()
                print(f"  ✅ Admin '{DEFAULT_ADMIN_EMAIL}' password hash upgraded.")
                return "upgraded"
            print(f"  ⏭  Admin '{DEFAULT_ADMIN_EMAIL}' already exists, skipped.")
            return "skipped"

        user = User(
            id=DEFAULT_ADMIN_ID,
            tenant_id=DEFAULT_TENANT_ID,
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            role=DEFAULT_ADMIN_ROLE,
            status="active",
        )
        session.add(user)
        await session.commit()
        print(f"  ✅ Admin '{DEFAULT_ADMIN_EMAIL}' created.")
        return "created"


async def init_db() -> None:
    """
    初始化数据库：创建默认租户 + 默认管理员

    执行顺序：
    1. 先创建默认租户（因为管理员依赖租户的外键约束）
    2. 再创建默认管理员（管理员的 tenant_id 指向默认租户）

    这个顺序很重要！如果反过来，插入管理员时 tenant_id 的外键校验会失败。
    """
    print("🔧 Initializing database...")
    await create_default_tenant()
    await create_default_admin_user()
    print("✅ Database initialization complete.")


async def main() -> None:
    """
    入口函数，通过 python -m app.db.init_db 执行

    为什么用 async？
    - 我们的数据库引擎是异步的（asyncpg），所有数据库操作必须用 await
    - 不能在同步函数里直接调用 await，需要用 asyncio.run() 启动异步上下文
    """

    await init_db()

    # 初始化完成后释放数据库引擎连接池
    await engine.dispose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
