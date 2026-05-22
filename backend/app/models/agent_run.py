"""
Agent 执行记录表模型

Agent 执行记录（AgentRun）保存每次 LangGraph / Agent
工作流运行的关键信息，用于后续问题排查、链路追踪、
性能分析、AI 成本分析。

字段说明：
- id: Agent 运行唯一标识
- tenant_id: 所属租户（多租户隔离的基础字段）
- conversation_id: 来源对话（可为空，如独立 Agent 任务）
- trigger_message_id: 触发本次 Agent 的消息（可为空）
- status: 执行状态，可选值：
  - running: 正在执行中
  - success: 执行成功
  - failed: 执行失败
- input_payload: 输入参数（JSON 类型）
- output_payload: 输出结果（JSON 类型，可为空）
- error_message: 失败时的错误信息（可为空）
- started_at: Agent 真正开始执行的时间
- finished_at: Agent 执行结束时间（可为空，表示仍在执行）

started_at 与 created_at 的区别：
  - created_at: 记录在数据库中被创建的时间
  - started_at: Agent 真正开始执行的时间
  两者都可能不同（如 Agent 进入队列等待执行）
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin


class AgentRun(Base, TimestampMixin):
    """Agent 执行记录表 — 每次 Agent 工作流运行"""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # ── 多租户字段 ──
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    # ── 来源对话 ──
    # 可为空（如独立 Agent 任务，不绑定对话）
    conversation_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=True,
        index=True,
    )

    # ── 触发消息 ──
    # 可为空，但有索引便于反查（"这条消息触发了哪个 AgentRun？"）
    trigger_message_id: Mapped[str | None] = mapped_column(
        ForeignKey("conversation_messages.id"),
        nullable=True,
        index=True,
    )

    # ── 执行状态 ──
    # 可选值：running / success / failed
    status: Mapped[str] = mapped_column(
        String(20),
        default="running",
        nullable=False,
        index=True,
    )

    # ── 输入参数 ──
    input_payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ── 输出结果 ──
    # 执行成功后才填充
    output_payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ── 错误信息 ──
    # 执行失败时填充
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ── 执行时间 ──
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # 可为空，表示仍在执行中
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── 关系定义 ──
    tenant = relationship("Tenant")
    conversation = relationship(
        "Conversation",
        back_populates="agent_runs",
    )
    # 触发消息（可为空）
    trigger_message = relationship("ConversationMessage")
