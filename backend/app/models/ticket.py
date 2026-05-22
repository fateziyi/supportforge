"""
工单表模型

工单（Ticket）用于承接 AI 无法闭环解决的问题。
工单是客服系统与智能体之间的桥梁：
简单问题 AI 回答，复杂问题升级工单。

字段说明：
- id: 工单唯一标识
- tenant_id: 所属租户（多租户隔离的基础字段）
- conversation_id: 来源对话
- subject: 工单标题
- status: 工单状态，可选值：
  - open: 新建工单，待处理
  - assigned: 已指派给客服
  - resolved: 已解决
  - closed: 已关闭
- priority: 优先级，可选值：
  - low: 低优先级
  - medium: 中优先级
  - high: 高优先级
  - urgent: 紧急
- assignee_id: 指派给哪个客服（可为空，表示未指派）

设计决策：
  工单创建者不单独设 created_by_user_id 字段，
  默认从 conversation.user_id 推导。
  如后续需要独立字段可在 Week 2 补充。
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin


class Ticket(Base, TimestampMixin):
    """工单表 — 承接 AI 无法闭环解决的问题"""

    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # ── 多租户字段 ──
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    # ── 来源对话 ──
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=False,
        index=True,
    )

    # ── 工单标题 ──
    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # ── 工单状态 ──
    # 可选值：open / assigned / resolved / closed
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        nullable=False,
    )

    # ── 优先级 ──
    # 可选值：low / medium / high / urgent
    priority: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        nullable=False,
    )

    # ── 指派客服 ──
    # 可为空，表示还未指派
    assignee_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # ── 关系定义 ──
    tenant = relationship("Tenant")
    conversation = relationship(
        "Conversation",
        back_populates="tickets",
    )
    # 指派的客服（可为空）
    assignee = relationship("User")
