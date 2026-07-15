"""
对话主表模型

对话（Conversation）是一轮客户咨询会话的容器。
后续消息都归属于某个 conversation，Agent 回答、
转工单、人工接管都挂在 conversation 上下文里。

字段说明：
- id: 对话唯一标识
- tenant_id: 所属租户（多租户隔离的基础字段）
- user_id: 发起对话的用户
- status: 对话状态，可选值：
  - open: 对话进行中
  - closed: 对话已关闭
  - handoff: 已转人工客服
- last_message_at: 最后一条消息时间（刚创建时可为空）

关系说明：
- tenant: 对话归属一个租户
- user: 对话由一个用户发起
- messages: 一个对话有多条消息
- tickets: 一个对话可能升级出多个工单
- agent_runs: 一个对话可能触发多次 Agent 运行
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    """对话主表 — 一轮客户咨询会话的容器"""

    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_conversations_id_tenant"),
        ForeignKeyConstraint(
            ["user_id", "tenant_id"],
            ["users.id", "users.tenant_id"],
            name="fk_conversations_user_tenant",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # ── 多租户字段 ──
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    # ── 发起者 ──
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # ── 对话状态 ──
    # 可选值：open / closed / handoff
    # 先用字符串，后续再考虑 Enum 或状态机
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        nullable=False,
    )

    # ── 最后消息时间 ──
    # 刚创建但还没发消息的对话，此字段为空
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── 关系定义 ──
    # relationship 用字符串类名，避免循环导入
    tenant = relationship("Tenant")
    user = relationship("User", foreign_keys=[user_id])
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        foreign_keys="ConversationMessage.conversation_id",
    )
    tickets = relationship(
        "Ticket", back_populates="conversation", foreign_keys="Ticket.conversation_id"
    )
    agent_runs = relationship(
        "AgentRun",
        back_populates="conversation",
        foreign_keys="AgentRun.conversation_id",
    )
