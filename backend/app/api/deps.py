"""
FastAPI 依赖注入骨架

这个文件定义所有路由共享的依赖注入函数（Dependency）。

什么是依赖注入？
- 在 FastAPI 中，Depends() 是一种"自动提供参数"的机制
- 路由函数声明依赖后，FastAPI 会自动调用依赖函数，把结果传给路由
- 例如：路由需要数据库会话 → 声明 Depends(get_db) → FastAPI 自动创建会话并传入

当前状态：
- Day 1 只创建骨架，不实现具体逻辑
- get_db() → Day 3 实现数据库连接后填充
- get_current_user() → Week 2 实现 JWT 认证后填充

为什么先只写骨架？
- Day 1 的目标是让后端能启动，不是把所有功能一次性写完
- 骨架文件存在后，后续开发可以直接填充，不需要新建文件
- raise NotImplementedError 而不是 pass，确保如果有人误调用会立刻报错而不是静默失败

面试考点：
- "你的多租户是怎么实现的？" → get_current_user 从 JWT 解析 tenant_id
- "tenant_id 从哪来？" → 只从 JWT 解析，不信任前端传参（CLAUDE.md 第 6 条规则）
"""


async def get_db():
    """
    获取数据库会话的依赖注入函数

    每次请求都会创建一个新的数据库会话（AsyncSession），
    请求结束后自动关闭，确保不会泄漏数据库连接。

    使用方式（Day 3 完善后）：
        @router.get("/users")
        async def list_users(db: AsyncSession = Depends(get_db)):
            ...

    Returns:
        AsyncSession: 数据库会话对象（Day 3 实现）

    Raises:
        NotImplementedError: 当前是骨架，Day 3 实现后移除
    """
    raise NotImplementedError("Day 3 实现数据库依赖 get_db")


async def get_current_user():
    """
    获取当前登录用户的依赖注入函数

    从请求的 JWT token 中解析出用户信息和租户 ID，
    确保所有业务操作都在正确的租户范围内进行。

    使用方式（Week 2 完善后）：
        @router.get("/me")
        async def get_me(user: CurrentUser = Depends(get_current_user)):
            ...

    Returns:
        CurrentUser: 包含 user_id 和 tenant_id 的用户上下文对象（Week 2 实现）

    Raises:
        NotImplementedError: 当前是骨架，Week 2 实现后移除

    重要设计约束（来自 CLAUDE.md）：
        tenant_id 只从 JWT 解析，绝不信任前端传参
        这防止了前端伪造 tenant_id 导致跨租户数据泄露的安全问题
    """
    raise NotImplementedError("Week 2 实现认证依赖 get_current_user")