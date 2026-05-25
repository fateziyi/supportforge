"""
用户表 ORM 模型

这个文件定义了用户（User）表，是认证和 RBAC 的数据基础。

用户与租户的关系：
- 每个用户归属于一个租户（多对一）
- 一个租户可以有多个用户
- 用户登录时，JWT token 里会同时包含 user_id 和 tenant_id
- 后续所有业务操作都基于 tenant_id 进行数据隔离

字段设计说明：
- id: UUID 字符串主键，与 Tenant 一致
- tenant_id: 外键指向 tenants.id，必须建索引
  - 索引原因：几乎所有查询都需要按租户过滤用户
  - 例如"获取当前租户的所有用户"、"获取当前租户的某个用户"
- username: 用户名，租户内唯一
  - 同一个租户不能有两个叫"admin"的用户
  - 但不同租户可以各自有一个"admin"
- email: 登录邮箱，租户内唯一
  - 同一个租户不能有重复邮箱
  - 但不同租户可以有相同邮箱（比如不同公司都有 hr@company.com）
- password_hash: 存储加密后的密码
  - 绝对不能叫 password，那会误导成存储明文密码
  - Week 2 会用 argon2 进行哈希（比 bcrypt 更抗 GPU/ASIC 攻击）
- role: 用户角色，字符串类型
  - 可选值必须与 CLAUDE.md §7 一致：
    - platform_admin: 平台超级管理员
    - tenant_admin: 租户管理员
    - support_agent: 客服坐席
    - auditor: 审计人员
  - Day 4 先用字符串，不做 Enum 校验
- status: 用户状态，active / disabled

联合唯一约束说明：
- (tenant_id, email): 同一租户内邮箱唯一
  - 用户登录用邮箱，如果租户内有重复邮箱就无法识别是哪个用户
- (tenant_id, username): 同一租户内用户名唯一
  - 显示名/标识名需要在租户内唯一，避免混淆

面试考点：
- "邮箱唯一约束怎么做？" → (tenant_id, email) 联合唯一，而非全局唯一
- "为什么不用全局唯一邮箱？" → 不同公司可能用相同邮箱格式，多租户要允许跨租户重复
- "角色是怎么定义的？" → 4 级 RBAC，与 CLAUDE.md §7 对齐
"""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    用户表模型

    每个用户归属于一个租户，登录时通过 email + password 认证。
    继承 TimestampMixin 获得 created_at 和 updated_at 字段。

    表名：users
    主键：id（UUID 字符串）
    外键：tenant_id → tenants.id
    联合唯一：(tenant_id, email)、(tenant_id, username)
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        UniqueConstraint("tenant_id", "username", name="uq_user_tenant_username"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # role 与 CLAUDE.md §7 一致：
    # platform_admin / tenant_admin / support_agent / auditor
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )

    # ── 关系定义 ──
    # relationship 用字符串类名，避免循环导入
    tenant = relationship("Tenant")
