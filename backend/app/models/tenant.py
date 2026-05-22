"""
租户表 ORM 模型

这个文件定义了多租户 SaaS 平台的顶层实体——租户（Tenant）。

租户是这个系统里最核心的概念：
- 所有业务数据（用户、知识库、文档、对话、工单）都归属于某个租户
- 不同租户之间的数据完全隔离，一个租户看不到另一个租户的数据
- Week 2 的认证和 RBAC 都依赖于"当前请求属于哪个租户"的判断

字段设计说明：
- id: 使用 String(36) 存储 UUID，而不是自增整数
  - UUID 适合分布式场景，避免主键冲突
  - 36 位长度刚好是标准 UUID 的字符串表示（含 4 个连字符）
  - 不用 PostgreSQL 的 UUID 类型，保持与其他数据库的兼容性
- name: 租户名称，全局唯一
  - 一个平台不能有两个同名租户
  - 例如"Acme Corp"和"Globex Inc"不能都叫"Acme Corp"
- status: 租户状态，用字符串而非 Enum
  - Day 4 先用字符串，减少复杂度
  - 可选值：active（正常）、disabled（停用）
  - 后续如果需要更多状态或 Enum 校验，可以在 Week 2 补充

面试考点：
- "你的多租户是怎么做的？" → 所有业务表都有 tenant_id，查询时自动过滤
- "为什么租户 ID 用 UUID 而不是自增？" → 分布式友好、避免主键碰撞
- "租户之间数据怎么隔离？" → 查询层 WHERE tenant_id = xxx，不是物理隔离
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """
    租户表模型

    作为多租户 SaaS 的顶层实体，所有业务数据都归属于某个 Tenant。
    继承 TimestampMixin 获得 created_at 和 updated_at 字段。

    表名：tenants
    主键：id（UUID 字符串）
    """

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )
