"""认证安全工具：负责密码哈希与 Access JWT 的签发、校验。"""

from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from pydantic import BaseModel, ValidationError

from .config import settings
from .exceptions import UnauthorizedException

_password_hasher = PasswordHasher()


class AccessTokenPayload(BaseModel):
    """Access Token 的最小可信载荷，供后续认证依赖统一消费。"""

    sub: str
    tenant_id: str
    role: str
    token_type: str
    iat: datetime
    exp: datetime


def hash_password(password: str) -> str:
    """将明文密码转换为不可逆的 Argon2id 哈希。"""
    return _password_hasher.hash(password)


def is_argon2_hash(password_hash: str) -> bool:
    """判断已有密码哈希是否已迁移到 Argon2，供初始化脚本兼容旧数据。"""
    return password_hash.startswith("$argon2")


def verify_password(password: str, password_hash: str) -> bool:
    """安全校验明文密码和 Argon2 哈希；格式错误统一按校验失败处理。"""
    try:
        return _password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError):
        return False


def create_access_token(
    *,
    user_id: str,
    tenant_id: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """签发仅用于访问 API 的 JWT，并固定写入租户与角色上下文。"""
    now = datetime.now(timezone.utc)
    expires_at = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "token_type": "access",
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> AccessTokenPayload:
    """验证 JWT 签名、过期时间和业务载荷，失败时不泄露具体原因。"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        token_payload = AccessTokenPayload.model_validate(payload)
        if token_payload.token_type != "access":
            raise ValueError("unexpected token type")
        return token_payload
    except (jwt.PyJWTError, ValidationError, ValueError) as exc:
        raise UnauthorizedException() from exc
