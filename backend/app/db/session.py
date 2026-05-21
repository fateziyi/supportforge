"""
数据库连接与会话管理模块

这个文件负责：
1. 创建异步数据库连接引擎（async_engine）
2. 创建会话工厂（AsyncSessionLocal）
3. 提供 get_db() 依赖注入函数，供 FastAPI 路由使用

为什么用异步引擎？
- FastAPI 本身是异步框架，使用 asyncpg 驱动能实现真正的异步数据库操作
- 同步驱动（psycopg2）在异步框架中会阻塞事件循环，导致性能下降
- asyncpg 是 PostgreSQL 的纯 Python 异步驱动，性能比 psycopg2 更好

为什么 expire_on_commit=False？
- SQLAlchemy 默认在 commit 后 expire 所有对象属性
- expire 意味着下次访问属性时，SQLAlchemy 会再发一次 SELECT 查询
- 这在异步场景下容易出问题（"greenlet spawn" 错误）
- 关闭 expire_on_commit 后，commit 后的对象属性仍然可以直接访问

为什么 pool_pre_ping=True？
- 长时间运行的服务，数据库连接可能因为网络波动、数据库重启等原因失效
- pool_pre_ping 在每次从连接池拿连接时，先发一个轻量 SELECT 1 检查连接是否可用
- 如果连接失效，自动丢弃并创建新连接，避免业务代码拿到坏连接

为什么用 yield 而不是 return？
- get_db() 是 FastAPI 的依赖注入函数
- yield 模式让 FastAPI 在请求处理完成后自动调用 finally 块
- 这样确保每个请求结束后 session 都会被正确关闭，不会泄漏连接

使用方式（API 路由中的典型用法）：
    from app.api.deps import get_db

    @router.get("/tenants")
    async def list_tenants(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Tenant))
        return result.scalars().all()

面试考点：
- "你怎么管理数据库连接？" → async engine + sessionmaker + FastAPI yield 依赖
- "为什么用 asyncpg 而不是 psycopg2？" → FastAPI 异步框架需要异步驱动
- "expire_on_commit=False 是什么意思？" → 避免异步场景下的 greenlet 错误
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import settings


# ── 创建异步数据库引擎 ──
# create_async_engine 是 SQLAlchemy 提供的异步引擎创建函数
# 第一个参数是数据库连接 URL，从 settings 中读取（.env 文件配置）
# echo=False — 不打印每条 SQL 到终端日志，生产环境必须关闭
#   如果需要调试 SQL，可以临时改成 echo=True
# pool_pre_ping=True — 每次从连接池拿连接时先检查可用性
#   避免拿到失效连接导致业务报错
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)


# ── 创建异步会话工厂 ──
# async_sessionmaker 是 SQLAlchemy 提供的异步会话工厂
# 每次调用 AsyncSessionLocal() 会创建一个新的 AsyncSession 实例
# bind=engine — 会话绑定到上面创建的引擎，所有 SQL 操作通过这个引擎执行
# class_=AsyncSession — 指定会话类型为异步会话
# expire_on_commit=False — commit 后不失效对象属性，避免异步场景下的报错
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 数据库会话依赖注入函数

    这个函数通过 yield 模式提供数据库会话：
    1. 请求进入时，创建一个新的 AsyncSession
    2. 通过 yield 把 session 交给路由处理函数
    3. 请求处理完成后（无论成功还是异常），自动关闭 session

    为什么必须用 yield 而不是 return？
    - yield 让 FastAPI 在请求完成后自动执行 finally 块
    - return 模式下，session 的关闭时机不确定，可能泄漏连接
    - yield 模式确保"每个请求一个 session，请求结束立即释放"

    为什么 finally 里要 await session.close()？
    - AsyncSession.close() 是异步操作，必须用 await
    - 关闭 session 会把连接归还到连接池，而不是真正关闭 TCP 连接
    - 连接池管理连接的复用和回收，close 只是"归还"而非"断开"

    Returns:
        AsyncGenerator[AsyncSession, None]: yield 一个 AsyncSession 实例
    """
    # async with 创建一个会话上下文
    # 会话上下文会自动管理事务的 begin/commit/rollback
    async with AsyncSessionLocal() as session:
        try:
            # yield 把 session 交给下游的路由处理函数
            # 下游函数可以通过 db.execute()、db.add() 等方法操作数据库
            yield session
        finally:
            # finally 确保 session 一定会被关闭
            # 即使路由处理函数抛出异常，session 也会被正确释放
            await session.close()