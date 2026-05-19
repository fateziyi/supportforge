# 用户接口 Users

> 基础路径：`/api/v1/users`

---

## 1. 创建用户

```
POST /api/v1/users
```

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| email | string | 是 | 邮箱 |
| password | string | 是 | 密码 |
| role | string | 是 | 角色 |
| tenant_id | string | 否 | 一般由后端自动注入 |

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

## 2. 用户列表

```
GET /api/v1/users
```

### 查询参数

| 字段 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量 |
| role | string | 角色筛选 |
| keyword | string | 关键词 |

---

## 3. 用户详情

```
GET /api/v1/users/{user_id}
```

---

## 4. 更新用户

```
PUT /api/v1/users/{user_id}
```

### 请求字段

| 字段 | 类型 | 说明 |
|------|------|------|
| username | string | 用户名 |
| email | string | 邮箱 |
| role | string | 角色 |
| status | string | 状态 |

---

## 5. 删除用户

```
DELETE /api/v1/users/{user_id}
```

---

## 6. 修改角色

```
PATCH /api/v1/users/{user_id}/role
```

### 请求字段

| 字段 | 类型 | 说明 |
|------|------|------|
| role | string | 新角色 |