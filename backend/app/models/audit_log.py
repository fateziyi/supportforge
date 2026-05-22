"""
审计日志表模型

审计日志（AuditLog）用于记录关键业务操作和 AI 行为，
后续所有需要追踪的操作都可以统一写入这里，例如：
- 用户登录
- 文档上传
- 工单创建 / 指派 / 关闭
- Agent 调用模型 / 检索知识库 / 升级工单

字段说明：
- id: 审计日志唯一标识
- tenant_id: 所属租户（多租户隔离的基础字段）
- user_id: 操作用户（可为空，如系统自动操作）
- action: 动作名，如 ticket_created / document_uploaded
- resource_type: 资源类型，如 ticket / document / conversation
- resource_id: 资源 ID（可为空）
- payload: 附加详情，优先用 JSON 类型便于结构化查询

继承 TimestampMixin 的理由：
  与 CLAUDE.md §9 一致，所有表必须包含
  created_at 和 updated_at 时间字段。
  审计日志业务上 updated_at ≈ created_at，
  但统一继承可保持代码风格一致，减少决策维度。
"""

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    """审计日志表 — 记录关键业务操作和 AI 行为"""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # ── 多租户字段 ──
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    # ── 操作用户 ──
    # 可为空（如系统自动操作、Agent 自动决策）
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # ── 动作名 ──
    # 如：ticket_created / document_uploaded / agent_model_call
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # ── 资源信息 ──
    # 资源类型，如：ticket / document / conversation
    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    # 资源 ID（可为空）
    resource_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )

    # ── 附加详情 ──
    # 优先用 JSON，便于后续做结构化审计查询
    payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ── 关系定义 ──
    tenant = relationship("Tenant")
    # 操作用户（可为空）
    user = relationship("User")
