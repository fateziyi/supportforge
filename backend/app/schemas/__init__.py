"""
Schema（数据传输对象）包 — 全部 Schema 的导入入口

这个文件的核心职责是：把所有 Pydantic Schema 类导入到这里，
方便其他模块通过 `from app.schemas import ...` 统一引用。

与 models/__init__.py 的区别：
- models/__init__.py 是为了让 Alembic 发现所有 ORM 模型
- schemas/__init__.py 是为了方便 API 层引用所有 Schema

Day 6 已定义的 Schema：
- LoginRequest：登录请求体
- CurrentUserResponse：当前用户信息
- TokenResponse：登录成功后的响应

Week 2 会补充：
- TenantCreateRequest / TenantUpdateRequest
- UserCreateRequest / UserUpdateRequest
- KnowledgeBaseCreateRequest / KnowledgeBaseUpdateRequest
- 等更多业务 Schema
"""

from .auth import (
    CurrentUserResponse as CurrentUserResponse,
)
from .auth import (
    LoginRequest as LoginRequest,
)
from .auth import (
    TokenResponse as TokenResponse,
)
