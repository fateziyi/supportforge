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
- 即使 Day 6 还没做完整认证，也不能把明文密码直接存进 password_hash
- 这里使用 hashlib.sha256 作为临时方案
- Week 2 会替换为 argon2（更安全的哈希算法，比 bcrypt 更抗 GPU/ASIC 攻击）
- sha256 不适合密码存储（容易被彩虹表攻击），但 Day 6 作为临时方案够用

执行方式：
    cd backend
    poetry run python -m app.db.init_db

面试考点：
- "初始化脚本怎么保证幂等？" → 先查后插，已存在就跳过
- "为什么用 sha256 而不是 argon2？" → Day 6 临时方案，Week 2 换 argon2
- "初始化脚本应该放在哪里？" → db/init_db.py，不属于业务层
"""

import hashlib

from sqlalchemy import select

from ..db.session import AsyncSessionLocal, engine
from ..models.tenant import Tenant
from ..models.user import User

# ── 默认数据定义 ──
# 这些值与 api/v1/auth.py 的 mock 常量对齐
DEFAULT_TENANT_ID = "default-tenant-id"
DEFAULT_TENANT_NAME = "Acme Demo"
DEFAULT_ADMIN_ID = "default-admin-id"
DEFAULT_ADMIN_EMAIL = "admin@acme.com"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_ROLE = "tenant_admin"
DEFAULT_ADMIN_PASSWORD = "123456"


def _temporary_password_hash(password: str) -> str:
    """
    临时密码哈希函数（Day 6 用，Week 2 替换为 argon2）

    为什么 Day 6 不直接用 argon2？
    - argon2 需要额外依赖（argon2-cffi 库），Day 6 不引入太多新依赖
    - argon2 是内存硬哈希算法，比 bcrypt 更抗 GPU/ASIC 暴力破解
    - 但 sha256 绝对不适合生产环境密码存储：
      - sha256 是快速哈希，容易被暴力破解
      - 没有盐值（salt），彩虹表可以直接命中
    - Week 2 替换为 argon2 后，需要同步更新：
      1. init_db.py 的哈希函数
      2. auth.py 的密码校验逻辑
      3. 已创建的默认管理员需要重新生成密码哈希

    Args:
        password: 明文密码

    Returns:
        sha256 哈希后的字符串（临时方案，不安全）
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


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
            print(f"  ⏭  Tenant '{DEFAULT_TENANT_NAME}' already exists, skipped.")
            return "skipped"

        tenant = Tenant(
            id=DEFAULT_TENANT_ID,
            name=DEFAULT_TENANT_NAME,
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
    - password_hash 使用临时 sha256 哈希，Week 2 替换为 argon2
    - 不能把明文密码直接存进 password_hash，即使 Day 6 是 demo 数据

    Returns:
        "created" 或 "skipped"
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == DEFAULT_ADMIN_EMAIL)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  ⏭  Admin '{DEFAULT_ADMIN_EMAIL}' already exists, skipped.")
            return "skipped"

        user = User(
            id=DEFAULT_ADMIN_ID,
            tenant_id=DEFAULT_TENANT_ID,
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=_temporary_password_hash(DEFAULT_ADMIN_PASSWORD),
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
