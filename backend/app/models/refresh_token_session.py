"""Refresh Token 可撤销会话模型，仅保存 jti，不保存原始 JWT。"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class RefreshTokenSession(Base, TimestampMixin):
    """租户隔离的 Refresh Token 会话，用于轮换、登出和重放拦截。"""

    __tablename__ = "refresh_token_sessions"
    __table_args__ = (
        UniqueConstraint("id", "tenant_id", name="uq_refresh_sessions_id_tenant"),
        UniqueConstraint("jti", name="uq_refresh_sessions_jti"),
        ForeignKeyConstraint(
            ["user_id", "tenant_id"],
            ["users.id", "users.tenant_id"],
            name="fk_refresh_sessions_user_tenant",
        ),
        Index(
            "ix_refresh_sessions_tenant_user_revoked",
            "tenant_id",
            "user_id",
            "revoked_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    jti: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    revoked_reason: Mapped[str | None] = mapped_column(String(30), nullable=True)
    replaced_by_jti: Mapped[str | None] = mapped_column(String(36), nullable=True)
