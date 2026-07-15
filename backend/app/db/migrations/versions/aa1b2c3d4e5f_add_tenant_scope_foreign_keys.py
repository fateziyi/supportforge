"""在数据库层禁止关联资源跨租户引用。"""

from typing import Sequence, Union

from alembic import op

revision: str = "aa1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "f84d9c005858"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """为引用目标创建组合候选键，并用 tenant_id 参与外键校验。"""
    for table in ["users", "knowledge_bases", "conversations", "conversation_messages"]:
        op.create_unique_constraint(f"uq_{table}_id_tenant", table, ["id", "tenant_id"])

    constraints = [
        ("fk_documents_kb_tenant", "documents", ["knowledge_base_id", "tenant_id"], "knowledge_bases"),
        ("fk_conversations_user_tenant", "conversations", ["user_id", "tenant_id"], "users"),
        ("fk_messages_conversation_tenant", "conversation_messages", ["conversation_id", "tenant_id"], "conversations"),
        ("fk_tickets_conversation_tenant", "tickets", ["conversation_id", "tenant_id"], "conversations"),
        ("fk_tickets_assignee_tenant", "tickets", ["assignee_id", "tenant_id"], "users"),
        ("fk_audit_logs_user_tenant", "audit_logs", ["user_id", "tenant_id"], "users"),
        ("fk_agent_runs_conversation_tenant", "agent_runs", ["conversation_id", "tenant_id"], "conversations"),
        ("fk_agent_runs_message_tenant", "agent_runs", ["trigger_message_id", "tenant_id"], "conversation_messages"),
    ]
    for name, source, columns, target in constraints:
        op.create_foreign_key(name, source, target, columns, ["id", "tenant_id"])


def downgrade() -> None:
    """按依赖反序撤销组合外键和候选键。"""
    for name, source in reversed([
        ("fk_documents_kb_tenant", "documents"),
        ("fk_conversations_user_tenant", "conversations"),
        ("fk_messages_conversation_tenant", "conversation_messages"),
        ("fk_tickets_conversation_tenant", "tickets"),
        ("fk_tickets_assignee_tenant", "tickets"),
        ("fk_audit_logs_user_tenant", "audit_logs"),
        ("fk_agent_runs_conversation_tenant", "agent_runs"),
        ("fk_agent_runs_message_tenant", "agent_runs"),
    ]):
        op.drop_constraint(name, source, type_="foreignkey")
    for table in ["conversation_messages", "conversations", "knowledge_bases", "users"]:
        op.drop_constraint(f"uq_{table}_id_tenant", table, type_="unique")
