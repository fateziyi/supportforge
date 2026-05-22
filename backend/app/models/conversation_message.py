"""
对话消息明细表模型

对话消息（ConversationMessage）保存每一条消息的
详细内容：用户消息、客服消息、AI 回复消息、系统消息。
后续做上下文拼接、消息回放、审计排查都依赖这个表。

字段说明：
- id: 消息唯一标识
- tenant_id: 所属租户（多租户隔离的基础字段）
- conversation_id: 所属对话
- sender_type: 发送者类型，可选值：
  - user: 来自终端用户
  - agent: 来自 AI 智能体
  - human_agent: 来自人工客服
  - system: 系统自动消息
- sender_id: 发送者 ID，系统消息可为空
- content: 消息正文（用 Text 类型，不截断长消息）
- message_type: 消息类型，可选值：
  - text: 普通文本消息
  - event: 事件类消息（如转人工、关闭对话）
  - tool_result: Agent 工具调用结果

继承 TimestampMixin 的理由：
  与 CLAUDE.md §9 一致，所有表必须包含
  created_at 和 updated_at 时间字段。
  消息表业务上 updated_at ≈ created_at，
  但统一继承可减少代码风格分裂。
"""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin


class ConversationMessage(Base, TimestampMixin):
    """对话消息明细表 — 每一条对话消息"""

    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # ── 多租户字段 ──
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    # ── 所属对话 ──
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=False,
        index=True,
    )

    # ── 发送者信息 ──
    # 可选值：user / agent / human_agent / system
    sender_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    # 系统消息可为空
    sender_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )

    # ── 消息内容 ──
    # 用 Text 类型，不截断长消息
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ── 消息类型 ──
    # 可选值：text / event / tool_result
    message_type: Mapped[str] = mapped_column(
        String(20),
        default="text",
        nullable=False,
    )

    # ── 关系定义 ──
    tenant = relationship("Tenant")
    conversation = relationship(
        "Conversation",
        back_populates="messages",
    )
