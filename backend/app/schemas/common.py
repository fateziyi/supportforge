"""所有 API 成功响应共用的数据契约。"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一包装成功响应，避免每个接口自行约定顶层字段。"""

    code: int = 0
    message: str = "success"
    data: T
