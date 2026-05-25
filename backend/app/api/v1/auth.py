"""
认证接口路由

这个文件定义了认证相关的 API 路由骨架。
Day 6 先提供最小登录入口，返回 mock token。

设计说明：
- 路由层只做"参数接收 + 响应返回"，不做真正的认证逻辑
- Day 6 的 login 接口默认只支持初始化脚本创建出的管理员账号
  （如 admin@acme.com）
- mock token 结构尽量接近未来真实 JWT 结构，方便 Week 2 替换

为什么 Day 6 只做 mock 而不直接实现 JWT？
- JWT 签发需要：密钥管理、过期策略、刷新机制、黑名单等
- 如果 Day 6 就开始做这些，会把"API 骨架搭出来"的目标膨胀成"半个 Week 2"
- 先把接口路径和响应结构定下来，Week 2 只需要替换内部逻辑

Week 2 替换指南：
- 保持 POST /api/v1/auth/login 的路径不变
- 保持 LoginRequest / TokenResponse 的结构不变
- 只需要把 mock 返回值替换为真实 JWT 签发逻辑
- 可能需要增加 password 校验、用户锁定、token 过期等安全措施

面试考点：
- "Day 6 的认证是怎么做的？" → mock token，Week 2 换 JWT
- "为什么不在 Day 6 就做 JWT？" → 避免任务膨胀，先搭骨架再填逻辑
"""

from fastapi import APIRouter, HTTPException

from ...schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# ── Day 6 mock 登录的默认值 ──
# 这些值与 init_db.py 创建的默认管理员账号对齐
# Week 2 实现真实 JWT 后，应从数据库查询用户信息
DEFAULT_ADMIN_EMAIL = "admin@acme.com"
DEFAULT_TENANT_ID = "default-tenant-id"
DEFAULT_ADMIN_ID = "default-admin-id"


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    """
    登录接口骨架（Day 6 mock 版本）

    Day 6 行为：
    - 默认只支持初始化脚本创建出的管理员账号
    - 不做真实密码校验，只要邮箱匹配就返回 mock token
    - 如果邮箱不匹配默认管理员，返回 401

    Week 2 替换时：
    - 增加真实密码校验（argon2-cffi）
    - 增加用户状态检查（是否 disabled）
    - 增加真实 JWT 签发（PyJWT + 密钥管理）
    - 增加登录日志记录（写入 audit_logs）

    Args:
        payload: LoginRequest，包含 email 和 password

    Returns:
        TokenResponse，包含 access_token、refresh_token、user 信息

    Raises:
        HTTPException(401): 邮箱不匹配默认管理员账号
    """
    # Day 6 mock 逻辑：只支持默认管理员账号
    # Week 2 替换为：从数据库查询用户 + 校验密码哈希
    if payload.email != DEFAULT_ADMIN_EMAIL:
        raise HTTPException(
            status_code=401,
            detail="Day 6 mock login only supports the default "
            "admin account (admin@acme.com). "
            "Week 2 will implement full authentication.",
        )

    # 返回 mock token + 用户信息
    # Week 2 替换为：真实 JWT 签发（access_token 和 refresh_token）
    return TokenResponse(
        access_token="mock-access-token",
        refresh_token="mock-refresh-token",
        token_type="bearer",
        expires_in=3600,
        user=CurrentUserResponse(
            id=DEFAULT_ADMIN_ID,
            tenant_id=DEFAULT_TENANT_ID,
            email=DEFAULT_ADMIN_EMAIL,
            role="tenant_admin",
        ),
    )
