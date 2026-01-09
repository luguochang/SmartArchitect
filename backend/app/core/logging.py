"""
集中式日志配置模块
为 SmartArchitect AI 后端提供统一的日志管理
"""

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


def setup_logging():
    """
    配置应用程序的日志系统

    功能:
    - 控制台输出（开发模式）
    - 文件输出（app.log）每日轮转
    - 错误文件输出（error.log）仅记录 ERROR 及以上级别
    - 日志保留 30 天
    """
    # 获取日志目录路径（相对于当前文件）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(current_dir, "..", "..", "logs")
    log_dir = os.path.abspath(log_dir)

    # 创建日志目录（如果不存在）
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception as e:
        print(f"Warning: Failed to create log directory: {e}", file=sys.stderr)
        print("Falling back to console-only logging", file=sys.stderr)
        _setup_console_only()
        return

    # 配置根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清除现有的 handlers（避免重复）
    root_logger.handlers.clear()

    # ===== 1. 控制台处理器（开发模式） =====
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ===== 2. 应用日志文件处理器（每日轮转） =====
    try:
        app_log_path = os.path.join(log_dir, "app.log")
        file_handler = TimedRotatingFileHandler(
            filename=app_log_path,
            when="midnight",        # 每天午夜轮转
            interval=1,              # 每 1 天
            backupCount=30,          # 保留 30 天的日志
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Failed to create app.log handler: {e}", file=sys.stderr)

    # ===== 3. 错误日志文件处理器（仅 ERROR 级别） =====
    try:
        error_log_path = os.path.join(log_dir, "error.log")
        error_handler = TimedRotatingFileHandler(
            filename=error_log_path,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)
    except Exception as e:
        print(f"Warning: Failed to create error.log handler: {e}", file=sys.stderr)

    # 记录日志系统启动
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info(f"SmartArchitect AI Backend - Logging initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log directory: {log_dir}")
    logger.info(f"Log level: INFO")
    logger.info(f"Log retention: 30 days")
    logger.info("=" * 80)


def _setup_console_only():
    """
    备用方案：仅配置控制台日志（当文件日志失败时）
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger(__name__)
    logger.warning("Logging configured for console output only (file logging disabled)")
