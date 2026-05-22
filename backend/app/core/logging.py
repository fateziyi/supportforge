"""
日志初始化与请求日志中间件

这个文件负责两件事：
1. setup_logging() — 初始化项目日志系统，统一日志格式
2. RequestLogMiddleware — 请求日志中间件，自动记录每个请求的关键信息

日志格式设计：
    [时间] 级别 request_id=xxx method=GET path=/api/v1/health status=200 duration_ms=3

为什么需要请求日志中间件？
- 每个请求进入时自动生成 request_id，方便把同一请求的所有日志串联
- 请求结束时自动记录耗时、状态码，便于性能监控和问题排查
- request_id 会写入 ContextVar，后续所有日志和审计都可以读取

面试考点：
- "你怎么做请求链路追踪？" → request_id + ContextVar + 日志中间件
- "怎么监控接口性能？" → duration_ms 记录在日志中，可后续接入 Prometheus
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .context import clear_context, set_request_id

# ── 日志初始化 ──

def setup_logging(log_level: str = "INFO") -> None:
    """
    初始化项目日志系统

    配置日志格式和级别，所有模块使用同一个 logger 实例。

    Args:
        log_level: 日志级别，可选 DEBUG / INFO / WARNING / ERROR / CRITICAL
                   默认 INFO，生产环境建议 WARNING
    """
    # 获取项目的 logger 实例
    # "app" 是 logger 的名称，所有模块通过 logging.getLogger("app.xxx") 获取子 logger
    logger = logging.getLogger("app")

    # 设置日志级别
    # DEBUG: 所有日志都输出
    # INFO: 只输出 INFO 及以上级别的日志
    # WARNING: 只输出 WARNING 及以上级别的日志
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 避免重复添加 handler
    # 如果已经有 handler（比如被其他模块初始化过），不再重复添加
    if logger.handlers:
        return

    # 创建控制台日志 handler
    # StreamHandler 把日志输出到终端（stdout）
    handler = logging.StreamHandler()

    # 设置日志格式
    # 格式说明：
    #   [%(asctime)s] — 时间戳，如 [2026-05-20 14:30:00]
    #   %(levelname)s — 日志级别，如 INFO / ERROR
    #   %(message)s   — 日志内容
    formatter = logging.Formatter(
        fmt="[\u001b[32m%(asctime)s\u001b[0m] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)


# ── 请求日志中间件 ──

class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件

    每个请求进入时：
    1. 生成一个唯一的 request_id
    2. 写入 ContextVar，后续所有模块可以读取
    3. 记录请求开始时间

    每个请求结束时：
    1. 计算请求耗时（duration_ms）
    2. 记录请求方法、路径、状态码、耗时
    3. 清理 ContextVar，防止数据串到下一个请求

    中间件执行流程：
    RequestLogMiddleware.dispatch()
      1. set_request_id() → 生成 request_id
      2. 记录开始时间
      3. call_next(request) → 调用下游处理（路由、业务逻辑等）
      4. 计算耗时
      5. 打印日志
      6. clear_context() → 清理上下文（在 finally 中，确保一定执行）
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        中间件的核心处理逻辑

        每个 HTTP 请求都会经过这个方法。

        Args:
            request: 当前 HTTP 请求对象，包含 method、url 等信息
            call_next: 下一个处理器的调用函数
                       调用 call_next(request) 会继续执行后续中间件和路由处理
                       返回值是下游处理器的 Response 对象

        Returns:
            Response: 下游处理器返回的响应对象
        """
        # 获取日志实例
        logger = logging.getLogger("app")

        # 1. 生成 request_id 并写入上下文
        rid = set_request_id()

        # 2. 记录请求开始时间
        # time.time() 返回当前时间的浮点数（秒级精度）
        start_time = time.time()

        # 3. 调用下游处理器，获取响应
        # call_next 是 Starlette/FastAPI 提供的函数，
        # 它会把请求传递给下一个中间件和最终的路由处理器
        # 如果下游抛出异常，call_next 会返回一个 500 响应
        try:
            response = await call_next(request)
        except Exception:
            # 下游处理器抛出了异常
            # 这种情况下 response 无法正常获取，构造一个 500 状态码
            logger.error(
                f"request_id={rid} "
                f"method={request.method} "
                f"path={request.url.path} "
                f"status=500 "
                f"error=unhandled_exception"
            )
            # 仍然返回一个默认的 500 响应
            from starlette.responses import JSONResponse
            response = JSONResponse(
                status_code=500,
                content={
                    "code": 50000,
                    "message": "Internal Server Error",
                    "data": None,
                },
            )

        # 4. 计算请求耗时
        # duration_ms 单位是毫秒，乘以 1000 将秒转为毫秒
        # round(xxx, 2) 保留两位小数，避免精度过长
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # 5. 打印请求日志
        # 日志中包含：request_id、请求方法、路径、状态码、耗时
        # 这些信息足够用于问题排查和性能监控
        logger.info(
            f"request_id={rid} "
            f"method={request.method} "
            f"path={request.url.path} "
            f"status={response.status_code} "
            f"duration_ms={duration_ms}"
        )

        # 6. 清理上下文变量（放在 finally 中确保一定执行）
        # 如果不清理，下一个请求可能读到当前请求的 request_id
        # 这在日志排查时会造成混乱
        clear_context()

        return response
