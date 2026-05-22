"""
知识库表 ORM 模型

这个文件定义了知识库（KnowledgeBase）表，是 RAG 检索的逻辑容器。

知识库与租户的关系：
- 每个知识库归属于一个租户（多对一）
- 一个租户可以有多个知识库
- 例如 Acme Corp 可以有"产品手册知识库"、"常见问题知识库"两个

知识库与文档的关系：
- 一个知识库下有多个文档（一对多）
- 文档是知识库的成员，上传文档时必须指定归属哪个知识库
- RAG 检索时，可以指定在某个知识库范围内检索，也可以跨知识库检索

字段设计说明：
- id: UUID 字符串主键
- tenant_id: 外键指向 tenants.id，必须有索引
  - 索引原因：查询某个租户的所有知识库是最常见的操作
- name: 知识库名称，租户内唯一
  - (tenant_id, name) 联合唯一约束
  - 同一租户不能有两个叫"产品手册"的知识库
  - 但不同租户可以各自有一个"产品手册"
- description: 知识库描述，允许为空
  - 用 String(500) 而不是 Text，因为描述不需要太长
  - 如果后续需要更长的描述，可以改为 Text 类型
- status: 知识库状态
  - active: 正常使用
  - archived: 已归档，不再使用但数据保留

面试考点：
- "知识库和租户是什么关系？" → 多对一，每个知识库属于一个租户
- "知识库名唯一怎么做的？" → (tenant_id, name) 联合唯一
- "为什么 description 用 String 而不是 Text？" → 描述不需要超长文本
"""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin


class KnowledgeBase(Base, TimestampMixin):
    """
    知识库表模型

    作为 RAG 检索的逻辑容器，每个知识库归属于一个租户。
    继承 TimestampMixin 获得 created_at 和 updated_at 字段。

    表名：knowledge_bases
    主键：id（UUID 字符串）
    外键：tenant_id → tenants.id
    联合唯一：(tenant_id, name)
    """

    __tablename__ = "knowledge_bases"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_kb_tenant_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )

    # ── 关系定义 ──
    tenant = relationship("Tenant")
    documents = relationship("Document", back_populates="knowledge_base")