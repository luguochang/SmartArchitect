"""
请求日志中间件
拦截所有 HTTP 请求并记录详细信息
"""

import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggerMiddleware(BaseHTTPMiddleware):
    """
    日志中间件 - 记录所有 API 请求和响应

    功能:
    - 记录请求方法、路径、查询参数
    - 记录响应状态码、执行时间
    - 捕获异常并记录完整堆栈
    """

    async def dispatch(self, request: Request, call_next):
        """
        处理每个 HTTP 请求

        Args:
            request: FastAPI Request 对象
            call_next: 下一个中间件或路由处理器

        Returns:
            Response: HTTP 响应对象
        """
        # 记录开始时间
        start_time = time.time()

        # 提取请求信息
        method = request.method
        url_path = request.url.path
        query_params = dict(request.query_params) if request.query_params else {}
        client_ip = request.client.host if request.client else "unknown"

        # 记录请求（INFO 级别）
        if query_params:
            logger.info(f"[REQUEST] {method} {url_path} | Client: {client_ip} | Params: {query_params}")
        else:
            logger.info(f"[REQUEST] {method} {url_path} | Client: {client_ip}")

        try:
            # 调用下一个处理器
            response: Response = await call_next(request)

            # 计算执行时间
            duration_ms = (time.time() - start_time) * 1000

            # 记录响应（INFO 级别）
            logger.info(
                f"[RESPONSE] {method} {url_path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration_ms:.2f}ms"
            )

            return response

        except Exception as e:
            # 计算执行时间
            duration_ms = (time.time() - start_time) * 1000

            # 记录异常（ERROR 级别，包含堆栈）
            logger.error(
                f"[ERROR] {method} {url_path} | "
                f"Duration: {duration_ms:.2f}ms | "
                f"Error: {str(e)}",
                exc_info=True  # 包含完整堆栈信息
            )

            # 重新抛出异常，让 FastAPI 处理
            raise


class __init__:
    """
    中间件包初始化文件
    """
    pass
