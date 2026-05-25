"""
认证相关 Pydantic Schema

这个文件定义了认证模块的请求和响应数据结构（DTO），
是 API 接口与外部世界的"数据契约"。

为什么用 Pydantic 而不是直接用 ORM 模型？
- ORM 模型是数据库层的内部结构，包含 password_hash 等敏感字段
- Schema 是 API 层的外部契约，只暴露前端/联调方需要看到的字段
- 分离 ORM 和 Schema 的好处：
  1. 安全：不会意外把密码哈希暴露到 API 响应
  2. 灵活：同一个 ORM 模型可以有多个 Schema（创建、更新、列表等）
  3. 清晰：接口文档只显示与业务相关的内容，不显示内部实现细节

Day 6 的 Schema 只覆盖认证最小闭环：
- LoginRequest：登录请求体（email + password）
- CurrentUserResponse：当前登录用户信息
- TokenResponse：登录成功后的完整响应

Week 2 会补充：
- TokenRefreshRequest
- PasswordChangeRequest
- UserCreateRequest / UserUpdateRequest 等更多业务 Schema

面试考点：
- "Pydantic Schema 和 ORM 模型怎么配合？" → Schema 负责 API 边界，ORM 负责数据库映射
- "为什么 LoginRequest 不包含 tenant_id？" → tenant_id 从 JWT token 推导，不需要前端传入
"""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """
    登录请求体

    前端调用 POST /api/v1/auth/login 时传入的数据结构。

    字段说明：
    - email: 登录邮箱，使用 Pydantic 的 EmailStr 类型自动校验格式
      - EmailStr 要求必须是合法邮箱格式（如 admin@acme.com）
      - 如果传入 "not-an-email" 这样的非法格式，Pydantic 会自动返回 422 校验错误
    - password: 登录密码，Day 6 暂不做复杂校验
      - Week 2 会增加最小长度、复杂度等校验规则
    """

    email: EmailStr
    password: str


class CurrentUserResponse(BaseModel):
    """
    当前登录用户信息

    这个结构会出现在两个地方：
    1. TokenResponse 的 user 字段（登录成功时一起返回）
    2. GET /api/v1/auth/me 的响应（Week 2 实现）

    字段说明：
    - id: 用户唯一标识
    - tenant_id: 所属租户标识，后续所有业务请求都依赖这个字段做数据隔离
    - email: 用户邮箱，也是登录标识
    - role: 用户角色，与 CLAUDE.md §7 一致
      - platform_admin / tenant_admin / support_agent / auditor
    """

    id: str
    tenant_id: str
    email: str
    role: str


class TokenResponse(BaseModel):
    """
    登录成功后的完整响应

    前端拿到这个响应后：
    1. 把 access_token 存到本地（localStorage 或 cookie）
    2. 后续请求带上 Authorization: Bearer <access_token>
    3. user 信息可以直接用来渲染界面（如显示用户名、角色）

    字段说明：
    - access_token: 访问令牌，Day 6 返回 mock 值，Week 2 替换为真实 JWT
    - refresh_token: 刷新令牌，access_token 过期后用它换取新 token
    - token_type: 固定为 "bearer"，符合 OAuth2 规范
    - expires_in: access_token 的过期秒数（Day 6 固定 3600，Week 2 从 JWT 配置读取）
    - user: 当前登录用户信息，避免前端再发一次 GET /me

    为什么把 user 嵌套在 TokenResponse 里？
    - 减少前端请求次数：登录成功后直接拿到用户信息，不需要再调 GET /me
    - 前端初始化更方便：拿到 token 和 user 后一次性完成所有初始化
    - 这是很多 SaaS 平台的标准做法（如 Auth0、Firebase Auth）
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: CurrentUserResponse
