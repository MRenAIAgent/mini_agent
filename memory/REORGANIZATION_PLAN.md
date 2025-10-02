# Memory System Reorganization Plan

## Current Status

**Completed:**
- ✅ Created new directory structure
- ✅ Extracted `MemoryCoordinator` to `coordinators/legacy_coordinator.py`
- ✅ Extracted `LearningAnalytics` to `coordinators/learning_analytics.py`
- ✅ Copied files to new directories (core, types, managers, coordinators, system)
- ✅ Created __init__.py files for all new packages

**Pending:**
- ⏳ Update import statements in all files
- ⏳ Remove old files after verification
- ⏳ Update test imports
- ⏳ Test the reorganized structure

## New Directory Structure

```
memory/
├── core/                      # Core abstractions
│   ├── __init__.py           ✅ Created
│   ├── memory_store.py       ✅ Copied
│   ├── memory_context.py     ✅ Copied
│   └── retrieval_strategy.py ✅ Copied
│
├── types/                     # Memory type implementations
│   ├── __init__.py           ✅ Created
│   ├── episodic_memory.py    ✅ Copied
│   ├── semantic_memory.py    ✅ Copied
│   ├── user_profile_memory.py ✅ Copied
│   ├── interaction_memory.py ✅ Copied
│   └── learning_graph_memory.py ✅ Copied
│
├── managers/                  # Management layer
│   ├── __init__.py           ✅ Created
│   ├── memory_manager.py     ✅ Copied
│   └── context_manager.py    ✅ Copied
│
├── coordinators/              # Coordination layer
│   ├── __init__.py           ✅ Updated
│   ├── enhanced_coordinator.py ✅ Moved
│   ├── parallel_retrieval.py ✅ Moved
│   ├── relevance_scorer.py   ✅ Moved
│   ├── adaptive_weights.py   ✅ Moved
│   ├── legacy_coordinator.py ✅ Created (extracted)
│   └── learning_analytics.py ✅ Created (extracted)
│
├── backends/                  # Storage backends
│   ├── __init__.py           ✅ Exists
│   ├── memgraph_backend.py   ✅ Exists
│   └── redis_backend.py      ✅ Exists
│
├── system/                    # Top-level system
│   ├── __init__.py           ⏳ Need to create
│   └── learning_memory_system.py ✅ Copied (needs cleanup)
│
├── docs/                      # Documentation
│   └── MEMORY_SYSTEM_DESIGN.md ✅ Exists
│
└── __init__.py                ⏳ Need to update

OLD FILES (to be removed after testing):
├── episodic_memory.py
├── semantic_memory.py
├── user_profile_memory.py
├── interaction_memory.py
├── learning_graph_memory.py
├── learning_memory_system.py
├── memory_manager.py
├── memory_store.py
├── memory_context.py
├── context_manager.py
└── retrieval_strategy.py
```

## Import Changes Required

### 1. Core Package Imports

**Old:**
```python
from .memory_store import MemoryStore, MemoryEntry, InMemoryStore
from .memory_context import MemoryContext, ConversationTurn
from .retrieval_strategy import RetrievalStrategy, SimilarityRetrieval
```

**New:**
```python
from .core import MemoryStore, MemoryEntry, InMemoryStore
from .core import MemoryContext, ConversationTurn
from .core import RetrievalStrategy, SimilarityRetrieval
```

### 2. Types Package Imports

**Old:**
```python
from .episodic_memory import EpisodicMemoryManager
from .semantic_memory import SemanticMemoryManager
from .user_profile_memory import UserProfileMemoryManager
from .interaction_memory import InteractionMemoryManager, InteractionType
from .learning_graph_memory import LearningGraphMemory, ConceptStatus
```

**New:**
```python
from .types import (
    EpisodicMemoryManager,
    SemanticMemoryManager,
    UserProfileMemoryManager,
    InteractionMemoryManager,
    InteractionType,
    LearningGraphMemory,
    ConceptStatus
)
```

### 3. Managers Package Imports

**Old:**
```python
from .memory_manager import CoreMemoryManager
from .context_manager import ContextManager
```

**New:**
```python
from .managers import CoreMemoryManager, ContextManager
```

### 4. Coordinators Package Imports

**Old:**
```python
from .coordinator import EnhancedMemoryCoordinator
```

**New:**
```python
from .coordinators import (
    EnhancedMemoryCoordinator,
    MemoryCoordinator,
    LearningAnalytics
)
```

### 5. System Package Imports

**Old:**
```python
from .learning_memory_system import LearningMemorySystem
```

**New:**
```python
from .system import LearningMemorySystem
```

## Files Requiring Import Updates

### In `memory/types/` directory:
- `episodic_memory.py`: Update `from .memory_manager import` → `from ..managers import`
- `semantic_memory.py`: Update `from .memory_manager import` → `from ..managers import`
- `user_profile_memory.py`: Update `from .memory_manager import` → `from ..managers import`
- `interaction_memory.py`: Update `from .memory_manager import` → `from ..managers import`
- `learning_graph_memory.py`: Update `from .memory_manager import` → `from ..managers import`

### In `memory/managers/` directory:
- `memory_manager.py`: Update imports from `from .memory_store import` → `from ..core import`
- `context_manager.py`: Update imports from `from .memory_store import` → `from ..core import`

### In `memory/coordinators/` directory:
- `enhanced_coordinator.py`: Update imports to use `..types`, `..managers`, etc.
- `parallel_retrieval.py`: Update imports
- `relevance_scorer.py`: Update imports
- `legacy_coordinator.py`: Already has TYPE_CHECKING imports
- `learning_analytics.py`: Already has TYPE_CHECKING imports

### In `memory/system/` directory:
- `learning_memory_system.py`:
  - Update all imports to use relative imports from parent packages
  - Remove embedded `MemoryCoordinator` and `LearningAnalytics` classes (now in coordinators/)
  - Update instantiation to import from coordinators

## Next Steps

### Step 1: Create system/__init__.py
```python
"""Top-level learning memory system."""

from .learning_memory_system import (
    LearningMemorySystem,
    LearningSystemConfig,
    ComprehensiveLearningResponse,
    SessionConsolidationResult,
    ComprehensiveLearningInsights
)

__all__ = [
    'LearningMemorySystem',
    'LearningSystemConfig',
    'ComprehensiveLearningResponse',
    'SessionConsolidationResult',
    'ComprehensiveLearningInsights',
]
```

### Step 2: Update memory/__init__.py

Make it export from all subpackages for backward compatibility:

```python
"""Memory system for AI agents with multiple memory types.

This package provides a comprehensive memory system with:
- Episodic memory (learning experiences)
- Semantic memory (knowledge and concepts)
- User profile memory (preferences and characteristics)
- Interaction memory (conversation history)
- Learning graph memory (learning paths)
"""

# Core abstractions
from .core import (
    MemoryStore,
    MemoryEntry,
    InMemoryStore,
    MemoryContext,
    ConversationTurn,
    RetrievalStrategy,
    SimilarityRetrieval
)

# Memory types
from .types import (
    EpisodicMemoryManager,
    SemanticMemoryManager,
    UserProfileMemoryManager,
    InteractionMemoryManager,
    InteractionType,
    LearningGraphMemory,
    ConceptStatus
)

# Managers
from .managers import (
    CoreMemoryManager,
    ContextManager
)

# Coordinators
from .coordinators import (
    EnhancedMemoryCoordinator,
    IntegratedMemoryContext,
    MemoryCoordinator,
    LearningAnalytics
)

# Top-level system
from .system import (
    LearningMemorySystem,
    LearningSystemConfig,
    ComprehensiveLearningResponse,
    SessionConsolidationResult,
    ComprehensiveLearningInsights
)

__all__ = [
    # Core
    'MemoryStore',
    'MemoryEntry',
    'InMemoryStore',
    'MemoryContext',
    'ConversationTurn',
    'RetrievalStrategy',
    'SimilarityRetrieval',

    # Types
    'EpisodicMemoryManager',
    'SemanticMemoryManager',
    'UserProfileMemoryManager',
    'InteractionMemoryManager',
    'InteractionType',
    'LearningGraphMemory',
    'ConceptStatus',

    # Managers
    'CoreMemoryManager',
    'ContextManager',

    # Coordinators
    'EnhancedMemoryCoordinator',
    'IntegratedMemoryContext',
    'MemoryCoordinator',
    'LearningAnalytics',

    # System
    'LearningMemorySystem',
    'LearningSystemConfig',
    'ComprehensiveLearningResponse',
    'SessionConsolidationResult',
    'ComprehensiveLearningInsights',
]
```

### Step 3: Migration Script

Create `scripts/migrate_imports.py`:
```python
#!/usr/bin/env python3
"""Script to update imports in all files after reorganization."""

import re
from pathlib import Path

# Define import mappings
IMPORT_MAPPINGS = {
    r'from \.memory_manager import': 'from ..managers import',
    r'from \.memory_store import': 'from ..core import',
    r'from \.memory_context import': 'from ..core import',
    r'from \.retrieval_strategy import': 'from ..core import',
    r'from \.context_manager import': 'from ..managers import',
    r'from \.episodic_memory import': 'from ..types import',
    r'from \.semantic_memory import': 'from ..types import',
    r'from \.user_profile_memory import': 'from ..types import',
    r'from \.interaction_memory import': 'from ..types import',
    r'from \.learning_graph_memory import': 'from ..types import',
    r'from \.coordinator import': 'from ..coordinators import',
}

def update_file_imports(file_path):
    """Update imports in a single file."""
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    for old_pattern, new_import in IMPORT_MAPPINGS.items():
        content = re.sub(old_pattern, new_import, content)

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Updated: {file_path}")
    else:
        print(f"No changes: {file_path}")

def main():
    memory_dir = Path('memory')

    # Update all Python files in subdirectories
    for subdir in ['types', 'managers', 'coordinators', 'system']:
        subdir_path = memory_dir / subdir
        if subdir_path.exists():
            for py_file in subdir_path.glob('*.py'):
                if py_file.name != '__init__.py':
                    update_file_imports(py_file)

if __name__ == '__main__':
    main()
```

### Step 4: Testing Checklist

After reorganization, test:

- [ ] Import `LearningMemorySystem` from top-level package
- [ ] Create system instance
- [ ] Store memories in each type
- [ ] Retrieve with enhanced coordinator
- [ ] Run existing unit tests
- [ ] Run integration tests
- [ ] Verify backward compatibility

## Benefits of New Structure

1. **Clear Separation of Concerns**: Each directory has a single responsibility
2. **Easier Navigation**: Developers can quickly find relevant code
3. **Better Modularity**: Can import only needed components
4. **Improved Testability**: Can test each layer independently
5. **Scalability**: Easy to add new memory types or coordinators
6. **Documentation**: Structure self-documents the architecture

## Rollback Plan

If issues arise:
1. All original files still exist in root `memory/` directory
2. Can revert by removing new directories
3. Update `__init__.py` to use original imports
4. No data loss (only code reorganization)
