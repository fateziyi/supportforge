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

---

## 4. 退出登录

```
POST /api/v1/auth/logout
```

不需要额外请求字段，服务端使 token 失效即可。