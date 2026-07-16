# 认证接口 Auth

> 基础路径：`/api/v1/auth`

---

## 1. 登录

```
POST /api/v1/auth/login
```

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 登录邮箱 |
| password | string | 是 | 登录密码 |
| tenant_slug | string | 否 | 租户登录路由标识；同邮箱跨租户时必须提供 |

### 请求示例

```json
{
  "email": "admin@example.com",
  "password": "123456"
}
```

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| access_token | string | 访问令牌 |
| refresh_token | string | 刷新令牌 |
| token_type | string | 固定为 `bearer` |
| expires_in | number | Access Token 有效秒数 |
| user | object | 当前用户信息 |

### `user` 结构

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 用户 ID |
| tenant_id | string | 租户 ID |
| username | string | 用户名 |
| email | string | 邮箱 |
| role | string | 角色 |

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "xxx",
    "refresh_token": "yyy",
    "token_type": "bearer",
    "user": {
      "id": "u1",
      "tenant_id": "t1",
      "username": "admin",
      "email": "admin@example.com",
      "role": "tenant_admin"
    }
  }
}
```

---

## 2. 刷新 Token

```
POST /api/v1/auth/refresh
```

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | 刷新令牌 |

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| access_token | string | 新访问令牌 |
| refresh_token | string | 新刷新令牌 |
| token_type | string | `bearer` |

Refresh Token 每次使用都会轮换。旧 token、已登出 token、过期 token 或误传 Access Token 均返回 HTTP 401、业务码 `40100`。

---

## 3. 获取当前用户信息

```
GET /api/v1/auth/me
```

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 用户 ID |
| tenant_id | string | 租户 ID |
| username | string | 用户名 |
| email | string | 邮箱 |
| role | string | 角色 |
| status | string | 状态 |

请求必须携带 `Authorization: Bearer <access_token>`。服务端会同时校验 JWT、数据库用户状态和租户状态。

---

## 4. 退出登录

```
POST /api/v1/auth/logout
```

不需要额外请求字段，但必须携带 `Authorization: Bearer <access_token>`。服务端撤销该用户在当前租户的全部 Refresh Token 会话。

> 当前 Access Token 为短期无状态 JWT，logout 后已签发的 Access Token 最多仍可使用到自身过期时间；Refresh Token 会立即失效。
