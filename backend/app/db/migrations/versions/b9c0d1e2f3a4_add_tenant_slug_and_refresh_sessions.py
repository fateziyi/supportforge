"""增加登录租户 slug 与可撤销 Refresh Token 会话。"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b9c0d1e2f3a4"
down_revision: Union[str, Sequence[str], None] = "aa1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """安全回填既有租户 slug，并创建带租户组合外键的会话表。"""
    op.add_column("tenants", sa.Column("slug", sa.String(length=80), nullable=True))
    op.execute(
        "UPDATE tenants SET slug = CASE "
        "WHEN id = 'default-tenant-id' THEN 'acme-demo' "
        "ELSE 'tenant-' || replace(id, '-', '') END"
    )
    op.alter_column("tenants", "slug", nullable=False)
    op.create_unique_constraint("uq_tenants_slug", "tenants", ["slug"])
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    op.create_table(
        "refresh_token_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("jti", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=30), nullable=True),
        sa.Column("replaced_by_jti", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id", "tenant_id"], ["users.id", "users.tenant_id"], name="fk_refresh_sessions_user_tenant"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "tenant_id", name="uq_refresh_sessions_id_tenant"),
        sa.UniqueConstraint("jti", name="uq_refresh_sessions_jti"),
    )
    op.create_index("ix_refresh_sessions_tenant_id", "refresh_token_sessions", ["tenant_id"])
    op.create_index("ix_refresh_sessions_user_id", "refresh_token_sessions", ["user_id"])
    op.create_index("ix_refresh_sessions_jti", "refresh_token_sessions", ["jti"])
    op.create_index("ix_refresh_sessions_expires_at", "refresh_token_sessions", ["expires_at"])
    op.create_index("ix_refresh_sessions_revoked_at", "refresh_token_sessions", ["revoked_at"])
    op.create_index("ix_refresh_sessions_tenant_user_revoked", "refresh_token_sessions", ["tenant_id", "user_id", "revoked_at"])


def downgrade() -> None:
    """撤销 Day 9 新增表与租户 slug。"""
    op.drop_table("refresh_token_sessions")
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_constraint("uq_tenants_slug", "tenants", type_="unique")
    op.drop_column("tenants", "slug")
