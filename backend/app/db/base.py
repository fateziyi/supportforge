"""
ORM 基类与公共 Mixin 模块

这个文件定义了项目所有 ORM 模型共享的基础设施：
1. Base — 所有模型的声明基类，Alembic 通过 Base.metadata 发现所有表
2. TimestampMixin — 公共时间戳字段（created_at / updated_at），减少模型重复代码

为什么需要统一基类？
- Alembic 迁移依赖 Base.metadata 来自动发现所有模型定义的表结构
- 如果没有统一基类，每个模型要自己定义时间戳字段，大量重复代码
- 统一基类还能确保所有表的主键命名、字段类型风格一致

使用方式（Day 4/Day 5 的模型会这样继承）：
    from app.db.base import Base, TimestampMixin

    class Tenant(Base, TimestampMixin):
        __tablename__ = "tenants"
        id: Mapped[str] = mapped_column(String(36), primary_key=True)
        name: Mapped[str] = mapped_column(String(100))

面试考点：
- "你的 ORM 基类是怎么设计的？" → Base + TimestampMixin，Alembic 通过 metadata 自动发现
- "时间戳字段为什么用 server_default=func.now()？" → 数据库侧生成，避免应用时钟不准
- "updated_at 的 onupdate 是什么？" → SQLAlchemy 自动在 UPDATE 时刷新该字段
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    所有 ORM 模型的声明基类

    使用 SQLAlchemy 2.0 的 DeclarativeBase 风格。
    所有模型都继承这个类，Alembic 通过 Base.metadata 自动发现所有表定义。

    设计意图：
    - 不在这个基类上定义任何字段（比如 id），因为不同表可能有不同主键策略
    - 有些表用 UUID 主键，有些用自增 ID，统一在基类上定义会限制灵活性
    - 主键策略留给每个模型自己决定，基类只提供"识别为 ORM 模型"的能力
    """
    pass


class TimestampMixin:
    """
    公共时间戳字段 Mixin

    提供两个所有业务表都需要的时间字段：
    - created_at: 记录创建时间，数据库侧默认值 func.now()
    - updated_at: 记录最后修改时间，数据库侧默认值 func.now()，SQLAlchemy 在 UPDATE 时自动刷新

    为什么用 Mixin 而不是直接放在 Base 上？
    - 有些表可能不需要时间戳（比如纯关联表、配置表）
    - Mixin 可以灵活选择继承或不继承，不会强制所有表都有这两个字段

    为什么用 server_default=func.now()？
    - func.now() 让数据库在 INSERT 时自动填入当前时间
    - 不依赖应用服务器时钟，避免不同服务器时区不一致的问题
    - 数据库是时间的唯一权威来源

    为什么用 onupdate=func.now()？
    - SQLAlchemy 在执行 UPDATE 操作时，自动刷新 updated_at 的值
    - 不需要在业务代码里手动设置 updated_at
    - 注意：onupdate 是 SQLAlchemy 层面的功能，不是数据库触发器

    使用方式：
        class Tenant(Base, TimestampMixin):
            __tablename__ = "tenants"
            ...

    字段类型说明：
    - DateTime(timezone=True) → 使用带时区的时间类型（timestamptz in PostgreSQL）
    - 这样可以避免时区混乱问题，所有时间都以 UTC 存储，前端按用户时区展示
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )