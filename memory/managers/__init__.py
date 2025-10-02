"""Memory management layer.

This package provides management abstractions for memory operations:

- CoreMemoryManager: Base orchestrator for memory operations
- ContextManager: Session context lifecycle management
"""

from .memory_manager import CoreMemoryManager
from .context_manager import ContextManager

__all__ = [
    'CoreMemoryManager',
    'ContextManager',
]
