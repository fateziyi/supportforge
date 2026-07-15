"""
文档表 ORM 模型

这个文件定义了文档（Document）表，是知识库文档上传、解析、向量入库的持久化基础。

文档与租户的关系：
- 每个文档归属于一个租户（多对一）
- 一个租户可以有多个文档
- 租户是文档的所有者，也是数据隔离的边界

文档与知识库的关系：
- 每个文档归属于一个知识库（多对一）
- 一个知识库可以有多个文档
- 文档上传时必须指定所属知识库
- RAG 检索时可以按知识库范围过滤

字段设计说明：
- id: UUID 字符串主键
- tenant_id: 外键指向 tenants.id，必须有索引
  - 与其他租户级别数据一致，所有查询都需要按租户过滤
- knowledge_base_id: 外键指向 knowledge_bases.id，必须有索引
  - 查询某个知识库下的所有文档是最常见的操作
- filename: 原始文件名，如 "产品手册.pdf"
  - 用户上传时看到的文件名
  - 不做唯一约束，因为不同知识库可以有同名文件
- file_path: 文件在存储系统中的路径
  - 例如 "/uploads/acme/kb1/产品手册.pdf"
  - Week 3 会用本地文件系统或对象存储来管理实际文件
- mime_type: 文件的 MIME 类型
  - 例如 "application/pdf"、"text/plain"、
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  - Day 4 必加这个字段，Week 3 文档解析需根据文件类型决定解析策略
  - PDF、Word、Excel、TXT 等不同类型需要不同的解析器
- status: 文档处理状态
  - uploaded: 刚上传，还没开始解析
  - parsing: 正在解析（Celery 异步任务处理中）
  - ready: 解析完成，可以检索
  - failed: 解析失败，需要人工处理

面试考点：
- "文档状态是怎么管理的？" → uploaded → parsing → ready / failed，Celery 异步处理
- "为什么文档有两个外键？" → 租户（数据隔离）+ 知识库（业务归属）
- "mime_type 有什么用？" → Week 3 解析时根据类型选择解析器
"""

from sqlalchemy import ForeignKey, ForeignKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    """
    文档表模型

    每个文档归属于一个租户和一个知识库，是 RAG 文档处理的持久化基础。
    继承 TimestampMixin 获得 created_at 和 updated_at 字段。

    表名：documents
    主键：id（UUID 字符串）
    外键：tenant_id → tenants.id、knowledge_base_id → knowledge_bases.id
    """

    __tablename__ = "documents"
    __table_args__ = (
        ForeignKeyConstraint(
            ["knowledge_base_id", "tenant_id"],
            ["knowledge_bases.id", "knowledge_bases.tenant_id"],
            name="fk_documents_kb_tenant",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    knowledge_base_id: Mapped[str] = mapped_column(
        ForeignKey("knowledge_bases.id"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="uploaded",
        nullable=False,
    )

    # ── 关系定义 ──
    tenant = relationship("Tenant")
    knowledge_base = relationship(
        "KnowledgeBase",
        back_populates="documents",
        foreign_keys=[knowledge_base_id],
    )
