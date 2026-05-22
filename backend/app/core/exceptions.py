"""
统一异常处理模块

这个文件定义了项目所有自定义异常类型，并提供全局异常处理器，
把各种错误统一转成标准 JSON 结构返回给前端。

为什么需要统一异常处理？
- 如果不做统一处理，FastAPI 默认返回的 422/500 错误格式各不相同
- 前端很难统一解析错误信息，排错也不方便
- 统一后，所有错误都遵循 {"code": xxx, "message": "xxx", "data": null} 格式

异常层级：
  AppException (基类)
    ├── BusinessException (通用业务异常, HTTP 400)
    ├── UnauthorizedException (未登录/Token无效, HTTP 401)
    ├── ForbiddenException (无权限, HTTP 403)
    └── NotFoundException (资源不存在, HTTP 404)

全局异常处理器注册顺序：
  1. AppException handler → 处理所有自定义业务异常
  2. HTTPException handler → 处理 FastAPI 内置的 HTTP 异常
  3. Exception handler → 处理所有未知异常（兜底，防止堆栈泄露）

面试考点：
- "你的错误是怎么统一处理的？" → 自定义异常 + 全局处理器
- "怎么防止堆栈信息泄露？" → 未知异常只返回 500 + "Internal Server Error"
- "多租户场景下权限怎么校验？" → ForbiddenException + RBAC
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# ── 自定义异常基类 ──

class AppException(Exception):
    """
    项目自定义异常基类

    所有业务异常都继承这个类，包含三个核心字段：
    - code: 业务错误码（不是 HTTP 状态码），用于前端区分错误类型
    - message: 人类可读的错误描述
    - status_code: HTTP 状态码，决定响应的 HTTP 状态码

    设计意图：
    - code 和 status_code 分开，因为同一个 HTTP 400 可能对应多种业务错误
    - 比如：code=40001 表示"参数缺失"，code=40002 表示"格式错误"
    """

    # 默认值：400（通用业务异常）
    code: int = 40000
    message: str = "业务异常"
    status_code: int = 400

    def __init__(self, message: str = "", code: int = 0, status_code: int = 0):
        """
        初始化异常

        Args:
            message: 错误描述，如果不传则使用类默认值
            code: 业务错误码，如果不传则使用类默认值
            status_code: HTTP 状态码，如果不传则使用类默认值
        """
        # 只在传入了自定义值时覆盖默认值
        if message:
            self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)


class BusinessException(AppException):
    """
    通用业务异常

    用于处理业务逻辑中的错误，比如：
    - 参数校验失败
    - 业务规则违反
    - 数据状态不允许的操作

    HTTP 状态码：400
    """
    code: int = 40000
    message: str = "业务异常"
    status_code: int = 400


class UnauthorizedException(AppException):
    """
    未认证异常（未登录 / Token 无效 / Token 过期）

    用于处理需要登录但未提供有效凭证的情况。

    HTTP 状态码：401
    """
    code: int = 40100
    message: str = "未登录或凭证无效"
    status_code: int = 401


class ForbiddenException(AppException):
    """
    无权限异常（已登录但权限不足）

    用于处理用户已登录但没有权限执行该操作的情况。
    比如：普通客服试图访问平台管理员的功能。

    HTTP 状态码：403
    """
    code: int = 40300
    message: str = "权限不足"
    status_code: int = 403


class NotFoundException(AppException):
    """
    资源不存在异常

    用于处理查询的资源不存在的情况。
    比如：查询一个不存在的租户、用户、工单。

    HTTP 状态码：404
    """
    code: int = 40400
    message: str = "资源不存在"
    status_code: int = 404


# ── 统一错误响应格式 ──
# 所有错误返回都遵循这个结构，和 API 通用约定的成功返回结构对齐
# 成功：{"code": 0, "message": "success", "data": {...}}
# 失败：{"code": 40001, "message": "资源不存在", "data": null}

def _error_response(
    code: int,
    message: str,
    data: object = None,
    status_code: int = 0,
) -> JSONResponse:
    """
    生成统一错误响应

    Args:
        code: 业务错误码
        message: 错误描述
        data: 附加数据，通常为 None
        status_code: HTTP 状态码，如果不传则从 code 推算（code // 100）

    Returns:
        JSONResponse: 统一格式的错误响应
    """
    # 如果没有显式指定 HTTP status_code，从业务码推算
    # 比如 code=40400 → status_code=404，code=40000 → status_code=400
    http_status = status_code if status_code else max(400, min(599, code // 100))
    return JSONResponse(
        status_code=http_status,
        content={
            "code": code,
            "message": message,
            "data": data,
        },
    )


# ── 全局异常处理器 ──

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    处理所有自定义业务异常

    当代码中抛出 AppException（及其子类）时，FastAPI 自动调用这个处理器。
    它把异常信息转成统一 JSON 格式返回给前端。

    Args:
        request: 当前请求对象（可用于记录审计日志）
        exc: 抛出的异常对象，包含 code、message、status_code

    Returns:
        JSONResponse: 统一格式的错误响应
    """
    return _error_response(
        code=exc.code,
        message=exc.message,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    处理 Starlette/FastAPI 内置的 HTTPException

    包括两类场景：
    1. FastAPI 路由匹配失败（404 Not Found）— Starlette 内部抛出
    2. 代码中手动抛出 HTTPException — FastAPI 的 HTTPException

    这个处理器把它们都统一转成我们的标准格式。

    ⚠️ 重要：必须注册 Starlette 的 HTTPException，否则路由不存在时的 404
    会返回 {"detail":"Not Found"} 而不是我们的统一格式。

    Args:
        request: 当前请求对象
        exc: HTTP 异常对象

    Returns:
        JSONResponse: 统一格式的错误响应
    """
    return _error_response(
        code=exc.status_code * 100,  # 把 HTTP 状态码转成业务码：404 → 40400
        message=str(exc.detail),     # exc.detail 是错误描述
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理所有未知异常（兜底处理器）

    当代码抛出未被上面两个处理器捕获的异常时（比如数据库连接失败、空指针等），
    这个处理器负责兜底。

    关键安全约束：
    - 不把异常堆栈信息返回给前端（防止泄露服务器内部信息）
    - 对前端统一返回 "Internal Server Error"
    - 在开发阶段可以在日志中打印完整堆栈，方便开发者排查

    Args:
        request: 当前请求对象
        exc: 未知异常对象

    Returns:
        JSONResponse: 只返回 500 + "Internal Server Error"
    """
    # 开发阶段：打印完整堆栈到终端日志，方便排查
    # production 环境应该只记录到日志文件，不打印到终端
    import traceback
    traceback.print_exc()

    return _error_response(
        code=50000,
        message="Internal Server Error",
    )


# ── 注册函数 ──
# 在 main.py 中调用 register_exception_handlers(app) 即可生效

def register_exception_handlers(app: FastAPI) -> None:
    """
    将所有异常处理器注册到 FastAPI 应用实例上

    注册顺序决定了异常处理的优先级：
    1. AppException handler — 优先处理自定义异常
    2. HTTPException handler — 处理 FastAPI 内置异常（包括 Starlette 内部产生的 404 等）

    Args:
        app: FastAPI 应用实例
    """
    # 注册 Starlette 的 HTTPException（覆盖路由 404 等场景）
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(FastAPIHTTPException, http_exception_handler)    # type: ignore[arg-type]
    app.add_exception_handler(AppException, app_exception_handler)             # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)            # type: ignore[arg-type]


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    处理 FastAPI 的参数校验异常（422）

    当请求参数不符合 Pydantic Schema 定义时，
    FastAPI 会自动抛出 RequestValidationError。
    这个处理器把它也转成统一格式返回。

    Args:
        request: 当前请求对象
        exc: 参数校验异常对象，包含详细的字段错误信息

    Returns:
        JSONResponse: 统一格式的错误响应
    """
    # exc.errors() 返回详细的字段校验错误列表
    # 比如 [{"loc": ["body", "email"], "msg": "field required", "type": "value_error"}]
    # 我们把第一个错误的信息作为 message 返回，前端可以据此提示用户
    error_details = exc.errors()
    first_error = error_details[0] if error_details else {}
    # 构造简短的错误描述：字段名 + 错误信息
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    msg = first_error.get("msg", "参数校验失败")
    message = f"{field}: {msg}" if field else msg

    return _error_response(
        code=42200,
        message=message,
        data=error_details,  # 把完整的校验错误列表放在 data 里，前端可以据此渲染
    )
