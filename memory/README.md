# Memory System

A comprehensive, modular memory management system for AI agents that provides both basic storage/retrieval capabilities and advanced learning-oriented memory types.

## Overview

The memory system is designed with a layered architecture that supports:

- **Core Memory Management**: Basic storage, retrieval, and context management
- **Specialized Memory Types**: Domain-specific memory managers for different aspects of learning and interaction
- **Pluggable Backends**: Support for different storage backends (in-memory, Redis, Memgraph)
- **Learning Integration**: Advanced memory types that support educational applications

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   LearningMemorySystem                     │
│  (Comprehensive system combining all memory types)         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│              Specialized Memory Managers                   │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│ Episodic    │ Semantic    │ User Profile│ Interaction      │
│ Memory      │ Memory      │ Memory      │ Memory           │
├─────────────┴─────────────┴─────────────┴──────────────────┤
│              Learning Graph Memory                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                 CoreMemoryManager                          │
│            (Base memory operations)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│               Storage & Retrieval Layer                    │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│ Memory      │ Context     │ Retrieval   │ Backend          │
│ Store       │ Manager     │ Strategy    │ Switcher         │
└─────────────┴─────────────┴─────────────┴──────────────────┘
```

## Core Components

### 1. CoreMemoryManager

The foundation of the memory system, providing:

- **Memory Storage**: Store and retrieve memory entries with metadata
- **Context Management**: Manage conversation contexts and sessions
- **Search Capabilities**: Find relevant memories using text search
- **Backend Support**: Switch between different storage backends
- **Auto-save**: Automatic persistence of active contexts

#### Basic Usage

```python
from memory import CoreMemoryManager, InMemoryStore

# Initialize memory manager
manager = CoreMemoryManager(memory_store=InMemoryStore())
await manager.start()

# Store memory
await manager.store_memory(
    content="Python is a programming language",
    importance=0.8,
    session_id="session123"
)

# Search memories
results = await manager.search_memory("python", limit=5)

# Manage conversation context
await manager.add_conversation_turn(
    session_id="session123",
    user_input="What is Python?",
    agent_response="Python is a programming language..."
)

await manager.stop()
```

### 2. Specialized Memory Managers

#### EpisodicMemoryManager

Manages learning experiences and specific events:

```python
from memory import EpisodicMemoryManager

manager = EpisodicMemoryManager()
await manager.start()

# Store learning event
await manager.store_learning_event(
    event_type="concept_learned",
    content="User learned about Python variables",
    user_id="user123",
    session_id="session456",
    context={"concept": "variables", "difficulty": "beginner"},
    importance=0.9
)

# Store problem-solving attempt
await manager.store_problem_attempt(
    problem_id="python_vars_01",
    user_id="user123",
    session_id="session456",
    attempt_content="x = 5",
    was_successful=True,
    solution_steps=["declare variable", "assign value"],
    time_spent=30.0
)

await manager.stop()
```

#### SemanticMemoryManager

Manages structured knowledge and facts:

```python
from memory import SemanticMemoryManager

manager = SemanticMemoryManager()
await manager.start()

# Store semantic fact
fact_id = await manager.store_fact(
    fact_content="Variables in Python can hold different data types",
    domain="programming",
    related_concepts=["variables", "data_types", "python"],
    user_id="user123",
    confidence=0.9
)

# Search facts
facts = await manager.search_facts(
    query="python variables",
    domain="programming",
    user_id="user123"
)

await manager.stop()
```

#### InteractionMemoryManager

Manages conversation history and interaction patterns:

```python
from memory import InteractionMemoryManager, InteractionType

manager = InteractionMemoryManager()
await manager.start()

# Store interaction turn
await manager.store_interaction_turn(
    user_id="user123",
    session_id="session456",
    turn_number=1,
    user_input="What are Python variables?",
    agent_response="Python variables are containers...",
    interaction_type=InteractionType.QUESTION,
    context={"topic": "python_basics"}
)

# Get session history
history = await manager.get_session_history("session456")

await manager.stop()
```

#### LearningGraphMemory

Manages learning prerequisites and concept relationships:

```python
from memory import LearningGraphMemory

manager = LearningGraphMemory()
await manager.start()

# Mark concept as learned
await manager.mark_concept_learned(
    user_id="user123",
    concept_id="python_variables",
    mastery_level=0.8,
    evidence="Correctly answered 8/10 questions"
)

# Check learning readiness
readiness = await manager.can_learn_concept(
    user_id="user123",
    concept_id="python_functions",
    domain="python"
)

# Get next concepts to learn
next_concepts = await manager.get_next_concepts(
    user_id="user123",
    domain="python",
    limit=5
)

await manager.stop()
```

### 3. LearningMemorySystem

Comprehensive system that combines all memory types:

```python
from memory import LearningMemorySystem, InteractionType

# Initialize comprehensive learning system
system = LearningMemorySystem()
await system.start()

# Process learning interaction (uses all memory types)
response = await system.process_learning_interaction(
    user_id="user123",
    user_input="Can you explain Python variables?",
    session_id="session456",
    interaction_type=InteractionType.QUESTION,
    domain="python"
)

# Complete learning session (consolidates across all memory types)
consolidation = await system.complete_learning_session(
    user_id="user123",
    session_id="session456",
    session_summary="User learned about Python variables",
    concepts_learned=["python", "variables"],
    overall_success=0.8
)

# Get comprehensive insights
insights = await system.get_comprehensive_learning_insights(
    user_id="user123",
    domain="python",
    days_back=7
)

await system.stop()
```

## Memory Store Implementations

### InMemoryStore

Simple in-memory storage for development and testing:

```python
from memory import InMemoryStore

store = InMemoryStore()
# Stores data in RAM, lost when process ends
```

### FileStore

File-based persistence:

```python
from memory.memory_store import FileStore

store = FileStore("memories.json")
# Persists data to JSON file
```

### Backend Support

The system supports pluggable backends for production use:

```python
from memory import CoreMemoryManager

# Configure Redis backend
redis_config = {
    "backend_type": "redis",
    "host": "localhost",
    "port": 6379,
    "db": 0
}

manager = CoreMemoryManager(backend_config=redis_config)

# Configure Memgraph backend
memgraph_config = {
    "backend_type": "memgraph",
    "host": "localhost",
    "port": 7687,
    "auth": ("", "")
}

manager = CoreMemoryManager(backend_config=memgraph_config)
```

## Memory Entry Structure

All memories are stored as `MemoryEntry` objects:

```python
@dataclass
class MemoryEntry:
    id: str                          # Unique identifier
    content: str                     # Main content
    metadata: Dict[str, Any]         # Flexible metadata
    timestamp: datetime              # Creation time
    embedding: Optional[List[float]] # Vector embedding (if available)
    importance: float                # Importance score (0.0-1.0)
    access_count: int               # Access frequency
    last_accessed: datetime         # Last access time
```

## Configuration

### LearningSystemConfig

Configure the comprehensive learning system:

```python
from memory import LearningSystemConfig, LearningMemorySystem, InMemoryStore

config = LearningSystemConfig(
    episodic_config={"memory_store": InMemoryStore()},
    semantic_config={"memory_store": InMemoryStore()},
    profile_config={"memory_store": InMemoryStore()},
    interaction_config={"memory_store": InMemoryStore()},
    graph_config={"memory_store": InMemoryStore()}
)

system = LearningMemorySystem(config)
```

## Search and Retrieval

The memory system provides powerful search capabilities:

### Basic Text Search

```python
# Simple text search
results = await manager.search_memory("python programming", limit=10)

# Search with filters
results = await manager.search_memory(
    query="variables",
    limit=5,
    filters={"domain": "programming", "user_id": "user123"}
)
```

### Context-Aware Retrieval

```python
# Get relevant context for a query
context = await manager.get_relevant_context(
    session_id="session123",
    query="python variables",
    include_conversation=True,
    include_memories=True,
    memory_limit=5
)
```

## Testing

The memory system includes comprehensive tests:

```bash
# Run all memory system tests
python -m pytest tests/unit/test_comprehensive_memory_system.py -v

# Run specific component tests
python -m pytest tests/unit/test_comprehensive_memory_system.py::TestCoreMemoryManager -v
python -m pytest tests/unit/test_comprehensive_memory_system.py::TestLearningMemorySystem -v
```

## Performance Considerations

- **Memory Store Choice**: Use `InMemoryStore` for development, backend stores for production
- **Search Scope**: Limit search results with the `limit` parameter
- **Auto-save Interval**: Configure auto-save frequency based on your needs
- **Context Cleanup**: The system automatically cleans up old contexts

## Error Handling

The memory system gracefully handles errors:

- Failed storage operations return `False`
- Search errors return empty lists
- Context operations have fallback behaviors
- Backend connection failures fall back to in-memory storage

## Examples

### Educational Chatbot

```python
from memory import LearningMemorySystem, InteractionType

async def educational_chatbot():
    system = LearningMemorySystem()
    await system.start()

    try:
        # Student asks about Python
        response = await system.process_learning_interaction(
            user_id="student_456",
            user_input="I'm confused about Python lists",
            session_id="lesson_python_basics",
            interaction_type=InteractionType.QUESTION,
            domain="python"
        )

        print(f"Bot response: {response.response_text}")
        print(f"Personalization applied: {response.personalization_applied}")
        print(f"Next recommendations: {response.next_recommendations}")

        # End the session
        consolidation = await system.complete_learning_session(
            user_id="student_456",
            session_id="lesson_python_basics",
            session_summary="Student learned about Python lists",
            concepts_learned=["python", "lists", "data_structures"],
            overall_success=0.85
        )

        print(f"Learning consolidated: {consolidation.consolidation_success}")

    finally:
        await system.stop()
```

### Knowledge Base Agent

```python
from memory import SemanticMemoryManager

async def knowledge_agent():
    manager = SemanticMemoryManager()
    await manager.start()

    try:
        # Store domain knowledge
        await manager.store_fact(
            fact_content="React is a JavaScript library for building user interfaces",
            domain="web_development",
            related_concepts=["react", "javascript", "ui", "frontend"],
            confidence=0.95
        )

        # Query knowledge
        facts = await manager.search_facts(
            query="javascript ui library",
            domain="web_development"
        )

        for fact in facts:
            print(f"Knowledge: {fact.content}")

    finally:
        await manager.stop()
```

## Contributing

When extending the memory system:

1. **Follow the inheritance pattern**: Extend `CoreMemoryManager` for new memory types
2. **Add comprehensive tests**: Include both unit and integration tests
3. **Document new features**: Update this README with examples
4. **Consider backwards compatibility**: Maintain existing APIs when possible

## API Reference

For detailed API documentation, see the individual module docstrings:

- `memory.memory_manager`: Core memory management
- `memory.episodic_memory`: Learning events and experiences
- `memory.semantic_memory`: Structured knowledge and facts
- `memory.interaction_memory`: Conversation and dialogue management
- `memory.learning_graph_memory`: Learning prerequisites and paths
- `memory.learning_memory_system`: Comprehensive learning system

## License

This memory system is part of the mini_agent project and follows the same licensing terms.