"""
Checkpoint manager — wraps LangGraph's MemorySaver checkpointer for examination state persistence.

Each examination uses its langgraph_thread_id as the LangGraph thread_id, enabling per-session
state persistence across multiple HTTP requests.
"""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manages LangGraph thread checkpoints using an in-memory MemorySaver.

    In a production deployment this can be swapped for a PostgreSQL-backed
    SqliteSaver or a custom checkpointer without changing any callers.
    """

    _checkpointer = None

    @classmethod
    def get_checkpointer(cls):
        """Lazy-initialise and return a MemorySaver checkpointer instance."""
        if cls._checkpointer is None:
            try:
                from langgraph.checkpoint.memory import MemorySaver  # type: ignore
                cls._checkpointer = MemorySaver()
                logger.info("LangGraph MemorySaver checkpointer initialised.")
            except Exception as exc:  # noqa: BLE001
                logger.warning("LangGraph checkpointer init failed: %s", exc)
                cls._checkpointer = None
        return cls._checkpointer

    @classmethod
    def get_thread_config(cls, thread_id: str) -> dict:
        """Return a LangGraph config dict for the given thread."""
        return {"configurable": {"thread_id": thread_id}}

    @classmethod
    def get_thread_state(cls, thread_id: str) -> Optional[dict]:
        """Retrieve the latest persisted state for a given thread ID."""
        checkpointer = cls.get_checkpointer()
        if checkpointer is None:
            return None
        try:
            config = cls.get_thread_config(thread_id)
            snapshot = checkpointer.get(config)
            return snapshot.values if snapshot else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to retrieve thread state for %s: %s", thread_id, exc)
            return None

    @classmethod
    def clear_thread(cls, thread_id: str) -> None:
        """Remove all checkpoints for a thread (called on exam completion)."""
        checkpointer = cls.get_checkpointer()
        if checkpointer is None:
            return
        try:
            # MemorySaver stores by thread_id key — just remove the entry
            if hasattr(checkpointer, "storage"):
                keys_to_remove = [k for k in checkpointer.storage if thread_id in str(k)]
                for k in keys_to_remove:
                    del checkpointer.storage[k]
        except Exception as exc:  # noqa: BLE001
            logger.debug("Could not clear thread %s: %s", thread_id, exc)
