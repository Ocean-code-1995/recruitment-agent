"""
Context Engineering Module.

Handles context window optimization and memory management for Long-Running Agents.
Implements "Compactive Summarization" to prevent token overflow while preserving
critical conversation history.
"""

from .token_counter import count_tokens_for_messages
from .history_manager import HistoryManager
from .compacting_supervisor import CompactingSupervisor, compacting_supervisor, history_manager

__all__ = [
    # Utilities
    "count_tokens_for_messages",
    # Classes
    "HistoryManager",
    "CompactingSupervisor",
    # Singletons
    "compacting_supervisor",
    "history_manager",
]

