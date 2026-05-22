"""
ORM 模型包 — 全部模型的导入入口

这个文件的核心职责是：把所有 ORM 模型类导入到这里，
让 Alembic 的 env.py 通过 `import app.models` 时，
能把全部模型加载到 Base.metadata 中，从而自动发现所有表定义。

为什么需要在这里集中导入？
- Alembic 的 autogenerate 功能依赖 Base.metadata 来发现新表
- 只有被导入的模型才会注册到 Base.metadata
- 如果某个模型没在这里导入，Alembic 就不会生成对应的建表迁移

导入顺序说明：
- 按依赖关系从底层到上层排列
- Tenant 是最顶层的实体，不依赖其他业务表
- User 依赖 Tenant（外键 tenant_id）
- KnowledgeBase 依赖 Tenant（外键 tenant_id）
- Document 依赖 Tenant 和 KnowledgeBase（两个外键）
- Conversation 依赖 Tenant 和 User
- ConversationMessage 依赖 Tenant 和 Conversation
- Ticket 依赖 Tenant、Conversation 和 User
- AuditLog 依赖 Tenant 和 User
- AgentRun 依赖 Tenant、Conversation 和 ConversationMessage

⚠️ 注意：
- 每次新增模型文件后，必须在这里补上导入
- 否则 Alembic autogenerate 不会发现新表，迁移脚本会遗漏建表操作
"""

from .agent_run import AgentRun as AgentRun
from .audit_log import AuditLog as AuditLog
from .conversation import Conversation as Conversation
from .conversation_message import ConversationMessage as ConversationMessage
from .document import Document as Document
from .knowledge_base import KnowledgeBase as KnowledgeBase
from .tenant import Tenant as Tenant
from .ticket import Ticket as Ticket
from .user import User as User
