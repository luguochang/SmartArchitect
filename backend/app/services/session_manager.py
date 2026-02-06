"""
画布会话管理器 (Canvas Session Manager)

提供内存存储 + 可选文件持久化的会话管理功能，用于增量生成流程图时保存画布状态。
"""

import json
import os
import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from app.models.schemas import Node, Edge

logger = logging.getLogger(__name__)


class CanvasSessionManager:
    """画布会话管理器（内存存储 + 文件持久化）"""

    def __init__(
        self,
        ttl_minutes: int = 60,
        persist_path: str = "data/canvas_sessions",
        enable_persistence: bool = True
    ):
        """
        初始化会话管理器

        Args:
            ttl_minutes: 会话过期时间（分钟），默认 60 分钟
            persist_path: 持久化文件存储路径，默认 "data/canvas_sessions"
            enable_persistence: 是否启用文件持久化，默认 True
        """
        self._sessions: Dict[str, dict] = {}  # {session_id: {nodes, edges, timestamp, ...}}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._persist_path = persist_path
        self._enable_persistence = enable_persistence

        logger.info(
            f"CanvasSessionManager initialized: ttl={ttl_minutes}min, "
            f"persistence={enable_persistence}, path={persist_path}"
        )

    def create_or_update_session(
        self,
        session_id: Optional[str],
        nodes: List[Node],
        edges: List[Edge]
    ) -> str:
        """
        创建或更新会话

        Args:
            session_id: 会话 ID，如果为 None 则创建新会话
            nodes: 节点列表
            edges: 边列表

        Returns:
            会话 ID（新创建或更新的）
        """
        # 生成新会话 ID
        if not session_id:
            session_id = self._generate_session_id()
            logger.info(f"Creating new session: {session_id}")
        else:
            logger.info(f"Updating existing session: {session_id}")

        # 构建会话数据
        session_data = {
            "nodes": [n.model_dump() for n in nodes],
            "edges": [e.model_dump() for e in edges],
            "timestamp": datetime.now(),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "created_at": self._sessions.get(session_id, {}).get("created_at", datetime.now())
        }

        # 检查会话大小（防止超大画布）
        session_size = len(json.dumps(session_data, default=str))
        max_size = 5 * 1024 * 1024  # 5MB

        if session_size > max_size:
            logger.error(
                f"Session too large: {session_size / 1024 / 1024:.1f}MB > 5MB "
                f"(nodes={len(nodes)}, edges={len(edges)})"
            )
            raise ValueError(
                f"Session too large ({session_size / 1024 / 1024:.1f}MB > 5MB). "
                "Please clear canvas or reduce node count."
            )

        # 存储到内存
        self._sessions[session_id] = session_data

        # 持久化到文件（可选）
        if self._enable_persistence:
            try:
                self._persist_session(session_id)
            except Exception as e:
                logger.warning(f"Failed to persist session {session_id}: {e}")

        logger.info(
            f"Session saved: {session_id} ({len(nodes)} nodes, {len(edges)} edges, "
            f"size={session_size / 1024:.1f}KB)"
        )

        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        获取会话数据

        Args:
            session_id: 会话 ID

        Returns:
            会话数据字典，如果会话不存在或已过期则返回 None
        """
        # 先从内存查找
        if session_id not in self._sessions:
            # 尝试从文件恢复
            if self._enable_persistence:
                try:
                    self._load_session(session_id)
                except Exception as e:
                    logger.warning(f"Failed to load session {session_id} from file: {e}")

        session = self._sessions.get(session_id)

        # 会话不存在
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return None

        # 检查是否过期
        age = datetime.now() - session["timestamp"]
        if age > self._ttl:
            logger.warning(
                f"Session expired: {session_id} (age={age.total_seconds() / 60:.1f}min > {self._ttl.total_seconds() / 60}min)"
            )
            self.delete_session(session_id)
            return None

        # 更新访问时间
        session["timestamp"] = datetime.now()

        logger.info(
            f"Session retrieved: {session_id} ({session['node_count']} nodes, "
            f"{session['edge_count']} edges, age={age.total_seconds() / 60:.1f}min)"
        )

        return session

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            是否成功删除
        """
        # 从内存删除
        existed = session_id in self._sessions
        self._sessions.pop(session_id, None)

        # 删除持久化文件
        if self._enable_persistence:
            try:
                self._delete_persisted_session(session_id)
            except Exception as e:
                logger.warning(f"Failed to delete persisted session {session_id}: {e}")

        if existed:
            logger.info(f"Session deleted: {session_id}")
        else:
            logger.warning(f"Session not found for deletion: {session_id}")

        return existed

    def cleanup_expired(self) -> int:
        """
        清理所有过期会话（定期任务）

        Returns:
            清理的会话数量
        """
        now = datetime.now()
        expired_ids = [
            sid for sid, sess in self._sessions.items()
            if now - sess["timestamp"] > self._ttl
        ]

        for sid in expired_ids:
            self.delete_session(sid)

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions: {expired_ids}")

        return len(expired_ids)

    def get_session_count(self) -> int:
        """获取当前会话总数"""
        return len(self._sessions)

    def get_session_stats(self) -> dict:
        """获取会话统计信息"""
        now = datetime.now()
        total = len(self._sessions)
        total_nodes = sum(s["node_count"] for s in self._sessions.values())
        total_edges = sum(s["edge_count"] for s in self._sessions.values())
        avg_age_minutes = sum((now - s["timestamp"]).total_seconds() / 60 for s in self._sessions.values()) / max(total, 1)

        return {
            "total_sessions": total,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "avg_age_minutes": avg_age_minutes,
            "ttl_minutes": self._ttl.total_seconds() / 60,
            "persistence_enabled": self._enable_persistence
        }

    # ==================== 私有方法 ====================

    def _generate_session_id(self) -> str:
        """生成唯一的会话 ID"""
        return f"canvas-{uuid.uuid4().hex[:16]}"

    def _persist_session(self, session_id: str):
        """持久化会话到文件"""
        if not self._enable_persistence:
            return

        # 确保目录存在
        Path(self._persist_path).mkdir(parents=True, exist_ok=True)

        session_file = os.path.join(self._persist_path, f"{session_id}.json")
        session_data = self._sessions[session_id].copy()

        # 将 datetime 转换为字符串
        session_data["timestamp"] = session_data["timestamp"].isoformat()
        session_data["created_at"] = session_data["created_at"].isoformat()

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        logger.debug(f"Session persisted to file: {session_file}")

    def _load_session(self, session_id: str):
        """从文件加载会话"""
        if not self._enable_persistence:
            return

        session_file = os.path.join(self._persist_path, f"{session_id}.json")

        if not os.path.exists(session_file):
            return

        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        # 将字符串转换回 datetime
        session_data["timestamp"] = datetime.fromisoformat(session_data["timestamp"])
        session_data["created_at"] = datetime.fromisoformat(session_data["created_at"])

        self._sessions[session_id] = session_data

        logger.debug(f"Session loaded from file: {session_file}")

    def _delete_persisted_session(self, session_id: str):
        """删除持久化文件"""
        if not self._enable_persistence:
            return

        session_file = os.path.join(self._persist_path, f"{session_id}.json")

        if os.path.exists(session_file):
            os.remove(session_file)
            logger.debug(f"Persisted session file deleted: {session_file}")


# ==================== 全局实例 ====================

_session_manager: Optional[CanvasSessionManager] = None


def get_session_manager() -> CanvasSessionManager:
    """
    获取全局会话管理器实例（单例模式）

    Returns:
        CanvasSessionManager 实例
    """
    global _session_manager

    if _session_manager is None:
        _session_manager = CanvasSessionManager(
            ttl_minutes=60,  # 1 小时过期
            persist_path="data/canvas_sessions",
            enable_persistence=True  # 启用文件持久化
        )

    return _session_manager


def reset_session_manager():
    """重置全局会话管理器（主要用于测试）"""
    global _session_manager
    _session_manager = None
