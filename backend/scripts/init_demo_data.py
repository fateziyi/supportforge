"""
演示数据初始化脚本（可选但推荐）

这个脚本在默认租户和管理员的基础上，再补少量演示数据：
1. 创建一个知识库
2. 创建一条文档记录
3. 创建一条对话（conversation）
4. 创建一条工单（ticket）

目的是让本地 Swagger/数据库演示更完整，而不是做完整测试工厂。

设计原则：
- 幂等执行：按名称/标题先查后插
- 最小内容：只创建少量数据，不写大量 demo 数据
- 依赖 init_db.py：必须先执行 init_db.py 创建默认租户和管理员，
  再执行 init_demo_data.py 创建演示数据

执行方式：
    cd backend
    poetry run python -m app.db.init_db        # 先初始化基础数据
    poetry run python scripts/init_demo_data.py  # 再初始化演示数据

注意：
- scripts/ 不属于 app 包，需要 sys.path 调整才能使用绝对导入 from app.xxx
- Day 6 spec 标注为"可选但推荐"
- 不纳入 Day 6 必做 DoD
- 如果时间不够，可以跳过，留到 Day 7 / Week 2
"""

# ── sys.path 调整：scripts/ 在 app 包之外，需要把 backend/ 目录加入路径 ──
# 这使得脚本中的 `from app.xxx` 绝对导入可以正常解析，
# 而不必依赖外部 PYTHONPATH 环境变量设置
import sys
from pathlib import Path

# 将 backend/ 目录（即 app 包的父目录）加入 sys.path
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import uuid  # noqa: E402 — 必须在 sys.path 调整之后才能导入 app 模块

from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.models.conversation import Conversation  # noqa: E402
from app.models.document import Document  # noqa: E402
from app.models.knowledge_base import KnowledgeBase  # noqa: E402
from app.models.ticket import Ticket  # noqa: E402
from sqlalchemy import select  # noqa: E402

# ── 默认数据常量 ──
DEFAULT_TENANT_ID = "default-tenant-id"
DEFAULT_ADMIN_ID = "default-admin-id"
DEMO_CONVERSATION_ID = "demo-conversation-id"
DEMO_TICKET_ID = "demo-ticket-id"


async def create_demo_knowledge_base() -> str:
    """
    创建演示知识库（幂等）

    逻辑：
    1. 查询是否已存在名为 "Acme Help Center" 的知识库
    2. 如果已存在，跳过创建
    3. 如果不存在，创建并返回 ID

    Returns:
        "created" 或 "skipped"
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.name == "Acme Help Center",
                KnowledgeBase.tenant_id == DEFAULT_TENANT_ID,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("  ⏭  Knowledge base 'Acme Help Center' already exists, skipped.")
            return "skipped"

        kb = KnowledgeBase(
            id=str(uuid.uuid4()),
            tenant_id=DEFAULT_TENANT_ID,
            name="Acme Help Center",
            description="Demo knowledge base for Acme customer support",
            status="active",
        )
        session.add(kb)
        await session.commit()
        print("  ✅ Knowledge base 'Acme Help Center' created.")
        return "created"


async def create_demo_document() -> str:
    """
    创建演示文档记录（幂等）

    逻辑：
    1. 查询是否已存在名为 "FAQ.md" 的文档
    2. 如果已存在，跳过创建
    3. 如果不存在，创建一条文档记录

    注意：
    - Day 6 只创建文档记录，不真正上传文件内容
    - 文档的 file_path 是占位值，Week 2 实现真实文件上传后替换
    - mime_type 设为 "text/markdown"，表示这是一个 Markdown 格式文档

    Returns:
        "created" 或 "skipped"
    """
    async with AsyncSessionLocal() as session:
        # 先找到演示知识库的 ID
        result = await session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.name == "Acme Help Center",
                KnowledgeBase.tenant_id == DEFAULT_TENANT_ID,
            )
        )
        kb = result.scalar_one_or_none()

        if not kb:
            print("  ⚠️  Knowledge base not found, skipping document creation.")
            return "skipped"

        # 查询是否已存在同名文档
        result = await session.execute(
            select(Document).where(
                Document.filename == "FAQ.md",
                Document.knowledge_base_id == kb.id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("  ⏭  Document 'FAQ.md' already exists, skipped.")
            return "skipped"

        doc = Document(
            id=str(uuid.uuid4()),
            tenant_id=DEFAULT_TENANT_ID,
            knowledge_base_id=kb.id,
            filename="FAQ.md",
            mime_type="text/markdown",
            file_path="placeholder://faq.md",
            status="uploaded",
        )
        session.add(doc)
        await session.commit()
        print("  ✅ Document 'FAQ.md' created.")
        return "created"


async def create_demo_conversation() -> str:
    """
    创建演示对话（幂等）

    逻辑：
    1. 按固定 ID 查询是否已存在演示对话
    2. 如果已存在，跳过创建
    3. 如果不存在，创建一条对话，发起人为默认管理员

    为什么用固定 ID 做幂等判断？
    - conversation 没有 name 等天然唯一字段
    - 用固定 ID 比用 status 过滤更精确，不会误跳其他对话

    Returns:
        "created" 或 "skipped"
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation).where(
                Conversation.id == DEMO_CONVERSATION_ID,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("  ⏭  Demo conversation already exists, skipped.")
            return "skipped"

        conversation = Conversation(
            id=DEMO_CONVERSATION_ID,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=DEFAULT_ADMIN_ID,
            status="open",
        )
        session.add(conversation)
        await session.commit()
        print("  ✅ Demo conversation created.")
        return "created"


async def create_demo_ticket() -> str:
    """
    创建演示工单（幂等）

    逻辑：
    1. 按固定 ID 查询是否已存在演示工单
    2. 如果已存在，跳过创建
    3. 如果不存在，创建一条工单，关联到演示对话，指派给默认管理员

    为什么用固定 ID 做幂等判断？
    - 与 conversation 同理，subject 不是唯一字段
    - 用固定 ID 更精确

    Returns:
        "created" 或 "skipped"
    """
    async with AsyncSessionLocal() as session:
        # 先确认演示对话存在
        result = await session.execute(
            select(Conversation).where(
                Conversation.id == DEMO_CONVERSATION_ID,
            )
        )
        conv = result.scalar_one_or_none()

        if not conv:
            print("  ⚠️  Demo conversation not found, skipping ticket creation.")
            return "skipped"

        # 查询是否已存在演示工单
        result = await session.execute(
            select(Ticket).where(
                Ticket.id == DEMO_TICKET_ID,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("  ⏭  Demo ticket already exists, skipped.")
            return "skipped"

        ticket = Ticket(
            id=DEMO_TICKET_ID,
            tenant_id=DEFAULT_TENANT_ID,
            conversation_id=DEMO_CONVERSATION_ID,
            subject="Demo: How to reset password?",
            status="open",
            priority="medium",
            assignee_id=DEFAULT_ADMIN_ID,
        )
        session.add(ticket)
        await session.commit()
        print("  ✅ Demo ticket created.")
        return "created"


async def init_demo_data() -> None:
    """
    初始化演示数据

    执行顺序（外键依赖链）：
    1. 创建知识库（文档依赖知识库）
    2. 创建文档记录
    3. 创建对话（工单依赖对话）
    4. 创建工单
    """
    print("🔧 Initializing demo data...")
    await create_demo_knowledge_base()
    await create_demo_document()
    await create_demo_conversation()
    await create_demo_ticket()
    print("✅ Demo data initialization complete.")


async def main() -> None:
    """入口函数"""
    await init_demo_data()
    await engine.dispose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
